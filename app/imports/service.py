"""
CSV upload and staging.

UPLOAD -> PARSE -> VALIDATE -> STAGE. Nothing here writes to the ledger;
rows stay in staged_transactions until approved (see review.py).
"""

import hashlib
import os
from collections import Counter

from flask import current_app
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.constants import (
    APPROVAL_APPROVED, APPROVAL_PENDING, APPROVAL_REJECTED, IMPORT_FAILED,
    IMPORT_STAGED, PARSER_VERSION, VALIDATION_INVALID, VALIDATION_VALID,
)
from app.errors import InvalidRequest, NotFound
from app.extensions import db
from app.households.accounts import get_account
from app.households.service import require_member
from app.imports.csv_parser import ImportFileError, normalize_description, parse_csv
from app.imports.expiry import discard_review, extend_review, new_deadline
from app.imports.excel import read_sheet
from app.integrations.categories import suggest_categories
from app.models import Import, StagedTransaction, Transaction


def clean_filename(name):
    name = os.path.basename((name or "").replace("\\", "/")).strip()
    return name[:255] or "upload.csv"


def check_upload(filename, data):
    limit = current_app.config["MAX_UPLOAD_BYTES"]
    if not filename.lower().endswith((".csv", ".xlsx")):
        raise InvalidRequest("Choose a .csv or .xlsx file")
    if not data:
        raise InvalidRequest("The file is empty")
    if len(data) > limit:
        raise InvalidRequest("File is larger than the %d KB limit" % (limit // 1024))


def find_duplicate_candidates(account_id, rows, import_id):
    """
    Flag rows that look like transactions already recorded for this account
    (approved ledger rows, or pending rows of other imports).
    Matching is a multiset: the 2nd identical coffee in a file is only flagged
    if there are already 2 matching records. Repeats inside one file are
    never flagged against each other.
    Returns {row_number: [candidate dicts]}.
    """
    dates = {r["transaction_date"] for r in rows if r["transaction_date"] and not r["errors"]}
    if not dates:
        return {}
    known = {}
    # Rows already approved from this same file are its own repeats, not duplicates.
    ledger = Transaction.query.filter(Transaction.account_id == account_id,
                                      or_(Transaction.import_id.is_(None), Transaction.import_id != import_id),
                                      Transaction.transaction_date.in_(dates)).all()
    for t in ledger:
        key = (t.transaction_date, t.amount_minor, t.direction, normalize_description(t.original_description))
        known.setdefault(key, []).append({"kind": "transaction", "id": t.id})
    others = StagedTransaction.query.filter(
        StagedTransaction.account_id == account_id,
        StagedTransaction.import_id != import_id,
        StagedTransaction.approval_status == APPROVAL_PENDING,
        StagedTransaction.validation_status == VALIDATION_VALID,
        StagedTransaction.transaction_date.in_(dates)).all()
    for s in others:
        key = (s.transaction_date, s.amount_minor, s.direction, normalize_description(s.original_description))
        known.setdefault(key, []).append({"kind": "staged", "id": s.id})

    seen = Counter()
    flagged = {}
    for r in rows:
        if r["errors"]:
            continue
        key = (r["transaction_date"], r["amount_minor"], r["direction"], normalize_description(r["original_description"]))
        seen[key] += 1
        if len(known.get(key, [])) >= seen[key]:
            flagged[r["source_row_number"]] = known[key][:5]
    return flagged


def duplicate_candidates_for_edit(account_id, staged):
    """Re-check one edited row with the same rules as upload, over its import's pending rows."""
    if staged.transaction_date is None or staged.amount_minor is None or staged.direction is None:
        return []
    pending = StagedTransaction.query.filter(
        StagedTransaction.import_id == staged.import_id,
        StagedTransaction.approval_status == APPROVAL_PENDING,
        (StagedTransaction.validation_status == VALIDATION_VALID) | (StagedTransaction.id == staged.id),
    ).order_by(StagedTransaction.source_row_number).all()
    rows = [{"transaction_date": s.transaction_date, "amount_minor": s.amount_minor, "direction": s.direction,
             "original_description": s.original_description, "source_row_number": s.source_row_number,
             "errors": []} for s in pending]
    return find_duplicate_candidates(account_id, rows, staged.import_id).get(staged.source_row_number, [])


def create_import(actor_id, account_id, filename, data, preset="signed_amount", overrides=None, *, sheet=None):
    """
    Returns (import, already_imported). Exact re-upload of the same file to the
    same account returns the existing import and creates nothing.
    """
    account = get_account(actor_id, account_id, write=True)
    if account.account_status != "active":
        raise InvalidRequest("This account is closed")
    filename = clean_filename(filename)
    check_upload(filename, data)
    file_hash = hashlib.sha256(data).hexdigest()
    version = PARSER_VERSION
    if filename.lower().endswith(".xlsx"):
        version = "xlsx-v1"
        try:
            name, rows = read_sheet(data, sheet, preset, overrides, current_app.config["MAX_IMPORT_ROWS"])
        except ImportFileError as exc:
            raise InvalidRequest(str(exc)) from exc
        file_hash = hashlib.sha256(f"xlsx:{file_hash}:{name}".encode()).hexdigest()

    existing = Import.query.filter(Import.account_id == account.id, Import.file_hash == file_hash,
                                   Import.import_status != IMPORT_FAILED).first()
    if existing:
        return existing, True

    if version == PARSER_VERSION:
        try:
            rows = parse_csv(data, preset, overrides, current_app.config["MAX_IMPORT_ROWS"])["rows"]
        except ImportFileError as exc:
            failed = Import(household_id=account.household_id, account_id=account.id, uploaded_by=actor_id,
                            file_hash=file_hash, filename=filename, parser_version=version,
                            import_status=IMPORT_FAILED, error_message=str(exc))
            db.session.add(failed)
            db.session.commit()
            raise InvalidRequest(str(exc))
    suggest_categories(rows)
    imp = Import(household_id=account.household_id, account_id=account.id, uploaded_by=actor_id,
                 file_hash=file_hash, filename=filename, parser_version=version,
                 import_status=IMPORT_STAGED, total_rows=len(rows), review_expires_at=new_deadline(),
                 valid_rows=sum(1 for r in rows if not r["errors"]),
                 invalid_rows=sum(1 for r in rows if r["errors"]))
    db.session.add(imp)
    try:
        db.session.flush()  # Claim the account/file key before staging any rows.
    except IntegrityError:
        db.session.rollback()
        existing = Import.query.filter(Import.account_id == account.id, Import.file_hash == file_hash,
                                       Import.import_status != IMPORT_FAILED).first()
        if existing:
            return existing, True
        raise
    flagged = find_duplicate_candidates(account.id, rows, imp.id)
    for r in rows:
        db.session.add(StagedTransaction(
            import_id=imp.id, household_id=account.household_id, account_id=account.id,
            source_row_number=r["source_row_number"], raw_row={},
            original_description=r["original_description"], description=r["description"] or r["original_description"],
            transaction_date=r["transaction_date"], amount_minor=r["amount_minor"],
            currency=r["currency"], direction=r["direction"], transaction_type=r["transaction_type"],
            category=r["category"], suggested_category=r.get("suggested_category"),
            validation_status=VALIDATION_INVALID if r["errors"] else VALIDATION_VALID,
            validation_errors=r["errors"],
            potential_duplicate=r["source_row_number"] in flagged,
            duplicate_candidates=flagged.get(r["source_row_number"], []),
            edit_history=[]))
    db.session.commit()
    return imp, False


def display_status(staged):
    if staged.approval_status == APPROVAL_APPROVED:
        return "approved"
    if staged.approval_status == APPROVAL_REJECTED:
        return "rejected"
    if staged.validation_status == VALIDATION_INVALID:
        return "invalid"
    return "pending"


def get_import(actor_id, import_id):
    imp = db.session.get(Import, import_id) if import_id else None
    if imp is None:
        raise NotFound("Import not found")
    try:
        require_member(actor_id, imp.household_id)
    except NotFound:
        raise NotFound("Import not found")
    return imp


def list_imports(actor_id, household_id):
    require_member(actor_id, household_id)
    return Import.query.filter_by(household_id=household_id).order_by(Import.uploaded_at.desc()).all()


def cancel_review(actor_id, import_id):
    imp = get_import(actor_id, import_id)
    require_member(actor_id, imp.household_id, write=True)
    household_id = imp.household_id
    discard_review(import_id)
    db.session.commit()
    return household_id


def review_activity(actor_id, import_id):
    imp = get_import(actor_id, import_id)
    require_member(actor_id, imp.household_id, write=True)
    extend_review(import_id)
    db.session.commit()
    return imp.review_expires_at


def import_stats(imp):
    counts = Counter(display_status(s) for s in StagedTransaction.query.filter_by(import_id=imp.id).all())
    duplicates = StagedTransaction.query.filter_by(import_id=imp.id, potential_duplicate=True,
                                                   approval_status=APPROVAL_PENDING).count()
    return {"total": imp.total_rows, "pending": counts["pending"], "invalid": counts["invalid"],
            "approved": counts["approved"], "rejected": counts["rejected"],
            "potential_duplicates_pending": duplicates}


def list_staged(actor_id, import_id, status=None):
    imp = get_import(actor_id, import_id)
    rows = StagedTransaction.query.filter_by(import_id=imp.id).order_by(StagedTransaction.source_row_number).all()
    if status:
        rows = [r for r in rows if display_status(r) == status]
    return rows
