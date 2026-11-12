from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from app.errors import Conflict, InvalidRequest, NotFound
from app.extensions import db
from app.households.service import require_member
from app.imports.review import now_iso
from app.models import Account, Household, Transaction, TransferDecision


def lock_classifications(household_id):
    # An actual UPDATE serializes ledger edits on both SQLite and PostgreSQL.
    Household.query.filter_by(id=household_id).update(
        {Household.updated_at: Household.updated_at}, synchronize_session=False)


def confirmed_leg(txn):
    pair = TransferDecision
    return db.session.query(pair.debit_id).filter(
        pair.decision == "confirmed", or_(pair.debit_id == txn.id, pair.credit_id == txn.id)).correlate(txn).exists()


def pairs(household_id):
    debit, credit = Transaction, aliased(Transaction)
    source, destination = Account, aliased(Account)
    decision = TransferDecision
    query = (db.session.query(debit, credit, source.account_name.label("source"),
                              destination.account_name.label("destination"), decision.decision)
             .select_from(debit).join(credit, and_(credit.household_id == debit.household_id,
                   credit.transaction_date == debit.transaction_date, credit.amount_minor == debit.amount_minor,
                   credit.currency == debit.currency, credit.account_id != debit.account_id))
             .join(source, source.id == debit.account_id).join(destination, destination.id == credit.account_id)
             .outerjoin(decision, and_(decision.debit_id == debit.id, decision.credit_id == credit.id))
             .filter(debit.household_id == household_id, debit.direction == "debit", credit.direction == "credit"))
    return query, debit, credit


def transfer_page(actor_id, household_id, page):
    require_member(actor_id, household_id)
    query, debit, credit = pairs(household_id)
    order = (debit.transaction_date.desc(), debit.id, credit.id)
    confirmed = query.filter(TransferDecision.decision == "confirmed").order_by(*order).all()
    pending = (query.filter(~confirmed_leg(debit), ~confirmed_leg(credit),
                            or_(TransferDecision.decision.is_(None), TransferDecision.decision == "unsure"))
               .order_by(*order).limit(11).offset((page - 1) * 10).all())
    return confirmed, pending[:10], len(pending) > 10


def decide_transfer(actor_id, household_id, debit_id, credit_id, choice):
    require_member(actor_id, household_id, write=True)
    if choice not in ("confirmed", "dismissed", "unsure"):
        raise InvalidRequest("Choose a transfer decision")
    lock_classifications(household_id)
    query, debit, credit = pairs(household_id)
    match = query.filter(debit.id == debit_id, credit.id == credit_id).first()
    if not match:
        raise NotFound("Matching ledger entries not found")
    pair = db.session.get(TransferDecision, (debit_id, credit_id))
    if pair and pair.decision == choice:
        return
    if query.filter(debit.id == debit_id, credit.id == credit_id,
                    or_(confirmed_leg(debit), confirmed_leg(credit))).first():
        raise Conflict("One of these entries already has a confirmed transfer")
    if not pair:
        pair = TransferDecision(debit_id=debit_id, credit_id=credit_id)
        db.session.add(pair)
    pair.decision = choice
    if choice == "confirmed":
        for txn in match[:2]:
            history = list(txn.correction_metadata or [])
            for field, value in (("transaction_type", "internal_transfer"), ("category", None), ("matched_transaction_id", None)):
                old = getattr(txn, field)
                if old != value:
                    history.append(dict(at=now_iso(), by=actor_id, stage="transfer", field=field, old=old, new=value))
                    setattr(txn, field, value)
            txn.correction_metadata = history
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise Conflict("The transfer review changed. Reload Money flow.") from exc
