"""
Ledger reads and post-approval corrections.

Includes the Spend screen's all-time totals for approved ledger records.
"""

import re
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.constants import CATEGORIES, TRANSACTION_TYPES
from app.errors import InvalidRequest, NotFound, text
from app.extensions import db
from app.households.service import require_member
from app.imports.csv_parser import type_direction_error
from app.imports.review import check_matched_id, now_iso
from app.ledger.transfers import lock_classifications
from app.models import Transaction, TransferDecision

MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def month_bounds(month):
    """Return (first day, first day of next month) for 'YYYY-MM'. Dates are Asia/Kolkata calendar dates."""
    match = MONTH_RE.fullmatch(month) if isinstance(month, str) else None
    if not match:
        raise InvalidRequest("Month must look like 2026-11")
    year, mon = int(match.group(1)), int(match.group(2))
    if not 2000 <= year <= 2100:
        raise InvalidRequest("Choose a month between 2000 and 2100")
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


def list_transactions(actor_id, household_id, month=None, account_id=None,
                      transaction_type=None, category=None, limit=200, offset=0, *, expense_activity=False):
    require_member(actor_id, household_id)
    query = Transaction.query.filter_by(household_id=household_id)
    if expense_activity:
        query = query.filter(Transaction.transaction_type.in_(("purchase", "fee", "refund")))
    if month:
        start, end = month_bounds(month)
        query = query.filter(Transaction.transaction_date >= start, Transaction.transaction_date < end)
    if account_id:
        query = query.filter_by(account_id=account_id)
    if transaction_type:
        query = query.filter_by(transaction_type=None if transaction_type == "unclassified" else transaction_type)
    if category:
        query = query.filter_by(category=category)
    total = query.count()
    rows = (query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc(), Transaction.id.desc())
            .limit(min(max(limit, 1), 500)).offset(max(offset, 0)).all())
    return rows, total


def spending_aggregation(actor_id, household_id, month=None):
    """Aggregate approved ledger spending once for Spend and monthly plans.

    Confirmed spending is purchases plus fees less matched purchase refunds.
    Unclassified movements remain separate debit/credit totals. Monthly category
    actuals attribute a matched refund to its original purchase category in the
    month the refund was received; unmatched refunds are excluded.
    """
    require_member(actor_id, household_id)
    kind, direction = Transaction.transaction_type, Transaction.direction
    purchase = aliased(Transaction)
    matched = purchase.id.isnot(None)
    query = (db.session.query(kind, direction, Transaction.category, purchase.category, matched,
                              func.sum(Transaction.amount_minor))
             .outerjoin(purchase, (purchase.id == Transaction.matched_transaction_id)
                        & (purchase.household_id == household_id)
                        & (purchase.transaction_type == "purchase"))
             .filter(Transaction.household_id == household_id))
    if month is not None:
        start, end = month_bounds(month)
        query = query.filter(Transaction.transaction_date >= start, Transaction.transaction_date < end)
    groups = query.group_by(kind, direction, Transaction.category, purchase.category, matched)

    totals = {"confirmed": 0, "debit": 0, "credit": 0, "unmatched_refunds": 0}
    by_category = {}
    for txn_type, txn_direction, category, original_category, has_match, value in groups:
        value = int(value)
        if txn_type is None:
            totals[txn_direction] += value
        elif txn_type in ("purchase", "fee"):
            totals["confirmed"] += value
            if month is not None:
                key = category or "Uncategorized"
                by_category[key] = by_category.get(key, 0) + value
        elif txn_type == "refund" and has_match:
            totals["confirmed"] -= value
            if month is not None:
                key = original_category or "Uncategorized"
                by_category[key] = by_category.get(key, 0) - value
        elif txn_type == "refund":
            totals["unmatched_refunds"] += value

    totals["by_category"] = by_category
    return totals


def spend_totals(actor_id, household_id):
    """Backward-compatible Spend screen totals from the shared aggregation."""
    totals = spending_aggregation(actor_id, household_id)
    return {key: totals[key] for key in ("confirmed", "debit", "credit")}


def get_transaction(actor_id, transaction_id):
    txn = db.session.get(Transaction, transaction_id) if transaction_id else None
    if txn is None:
        raise NotFound("Transaction not found")
    try:
        require_member(actor_id, txn.household_id)
    except NotFound:
        raise NotFound("Transaction not found")
    return txn


def correct_transaction(actor_id, transaction_id, changes):
    """
    Correct classification fields of an approved record and keep the history.
    Amount, date and direction are not editable here: re-import the statement.
    """
    txn = get_transaction(actor_id, transaction_id)
    require_member(actor_id, txn.household_id, write=True)
    lock_classifications(txn.household_id)
    db.session.refresh(txn)
    allowed = ("category", "transaction_type", "matched_transaction_id", "description")
    unknown = [k for k in changes if k not in allowed]
    if unknown:
        raise InvalidRequest("Cannot correct: " + ", ".join(unknown))

    new = {"category": txn.category, "transaction_type": txn.transaction_type,
           "matched_transaction_id": txn.matched_transaction_id, "description": txn.description}
    for key, value in changes.items():
        new[key] = text(value, key) or None
    if new["category"] is not None and new["category"] not in CATEGORIES:
        raise InvalidRequest("Unknown category")
    if new["transaction_type"] not in TRANSACTION_TYPES:
        raise InvalidRequest("Unknown transaction type")
    if not new["description"]:
        raise InvalidRequest("Description cannot be empty")
    message = type_direction_error(new["transaction_type"], txn.direction)
    if message:
        raise InvalidRequest(message)
    if new["matched_transaction_id"]:
        if new["matched_transaction_id"] == txn.id:
            raise InvalidRequest("A transaction cannot be matched to itself")
        message = check_matched_id(txn.household_id, new["matched_transaction_id"],
                                   new["transaction_type"], txn.amount_minor, exclude_id=txn.id)
        if message:
            raise InvalidRequest(message)

    history = list(txn.correction_metadata or [])
    if txn.transaction_type == "internal_transfer" and new["transaction_type"] != "internal_transfer":
        # A corrected leg invalidates the pair; retain the other entry as an unmatched transfer.
        TransferDecision.query.filter(TransferDecision.decision == "confirmed",
            (TransferDecision.debit_id == txn.id) | (TransferDecision.credit_id == txn.id)).update(
            {"decision": "dismissed"}, synchronize_session=False)
    for key in changes:
        old_value = getattr(txn, key)
        if old_value != new[key]:
            history.append({"at": now_iso(), "by": actor_id, "stage": "ledger",
                            "field": key, "old": old_value, "new": new[key]})
            setattr(txn, key, new[key])
    txn.correction_metadata = history
    db.session.commit()
    return txn


def approved_records_for_month(auth_context, household_id, month):
    """
    Read-only feed for the finance service: approved records of one month.
    Requires a trusted AuthContext and active membership. Rejected, pending
    and invalid rows are not in the ledger table, so they cannot appear here.
    """
    require_member(auth_context.user_id, household_id)
    start, end = month_bounds(month)
    rows = (Transaction.query.filter(Transaction.household_id == household_id,
                                     Transaction.transaction_date >= start,
                                     Transaction.transaction_date < end)
            .order_by(Transaction.transaction_date, Transaction.created_at).all())
    return [{"transaction_id": t.id, "date": t.transaction_date.isoformat(),
             "type": t.transaction_type, "category": t.category, "direction": t.direction,
             "amount_minor": t.amount_minor, "currency": t.currency,
             "matched_transaction_id": t.matched_transaction_id, "approved": True} for t in rows]
