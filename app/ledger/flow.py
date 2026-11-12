"""Directed account connections derived from the household's approved ledger."""
from sqlalchemy import case, func

from app.errors import InvalidRequest, NotFound
from app.extensions import db
from app.households.service import require_member
from app.models import Account, Transaction
from app.ledger.transfers import confirmed_leg


def money_flow(actor_id, household_id, selection, page):
    require_member(actor_id, household_id)
    t = Transaction
    endpoint = case(
        (t.transaction_type.is_(None), "Awaiting classification"),
        (t.transaction_type == "internal_transfer", case(
            (t.direction == "debit", "Internal transfer · destination unknown"),
            else_="Internal transfer · source unknown")),
        (t.transaction_type == "purchase", func.coalesce(t.category, "Uncategorized purchase")),
        (t.transaction_type == "fee", func.coalesce(t.category, "Bank fees")),
        else_=func.replace(t.transaction_type, "_", " "),
    ).label("endpoint")
    ledger = t.query.filter(t.household_id == household_id, ~confirmed_leg(t))
    edges = (ledger.join(Account, Account.id == t.account_id)
             .with_entities(t.account_id, Account.account_name, t.direction, endpoint,
                            func.sum(t.amount_minor).label("amount"), func.count().label("count"))
             .group_by(t.account_id, Account.account_name, t.direction, endpoint)
             .order_by(Account.account_name, t.direction, endpoint).all())
    selected = None
    rows = []
    if any(selection):
        selected = next((e for e in edges if (e.account_id, e.direction, e.endpoint) == selection), None)
        if selected is None:
            raise NotFound("Connection not found in this household")
        if page < 1 or (page - 1) * 25 >= selected.count:
            raise InvalidRequest("Invalid transaction page")
        rows = (ledger.filter(t.account_id == selected.account_id, t.direction == selected.direction,
                              endpoint == selected.endpoint)
                .order_by(t.transaction_date.desc(), t.id).limit(25).offset((page - 1) * 25).all())
    return edges, selected, rows
