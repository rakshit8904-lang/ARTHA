"""Read-only monthly finance service backed by the approved household ledger."""
from sqlalchemy import func
from app.extensions import db
from app.households.service import require_member
from app.ledger.service import month_bounds, spending_aggregation
from app.models import Transaction


def monthly_summary(auth_context, household_id, month):
    require_member(auth_context.user_id, household_id)
    start, end = month_bounds(month)
    rows = (db.session.query(Transaction.transaction_type, Transaction.direction,
                            func.sum(Transaction.amount_minor))
            .filter(Transaction.household_id == household_id,
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date < end)
            .group_by(Transaction.transaction_type, Transaction.direction).all())
    totals = {(kind, direction): int(amount or 0) for kind, direction, amount in rows}
    income = totals.get(("income", "credit"), 0)
    spend = spending_aggregation(auth_context.user_id, household_id, month)
    unresolved_debits = totals.get((None, "debit"), 0)
    unresolved_credits = totals.get((None, "credit"), 0)
    excluded = {
        "unmatched_refunds_minor": spend["unmatched_refunds"],
        "internal_transfers_minor": sum(v for (k, _), v in totals.items() if k == "internal_transfer"),
        "card_settlements_minor": sum(v for (k, _), v in totals.items() if k == "card_settlement"),
        "cash_withdrawals_minor": sum(v for (k, _), v in totals.items() if k == "cash_withdrawal"),
        "investment_contributions_minor": sum(v for (k, _), v in totals.items() if k == "investment"),
        "loan_payments_minor": sum(v for (k, _), v in totals.items() if k == "loan_payment"),
    }
    count = Transaction.query.filter(Transaction.household_id == household_id,
                                    Transaction.transaction_date >= start,
                                    Transaction.transaction_date < end).count()
    notes = ["Only approved ledger entries are included; account coverage has not been confirmed.",
             "Matched refunds reduce spending in the month received; unmatched refunds are excluded.",
             "Unclassified movements are excluded from income and spending.",
             "Excluded movements are gross ledger-leg amounts: both legs of a transfer may appear.",
             "Investment movements include credits and debits, not only contributions.",
             "Debt payments and other excluded movements are not deducted from this surplus.",
             "This is not a bank balance, disposable income or complete net-worth statement."]
    if not count:
        notes.insert(0, "No approved records for this month; totals are unknown.")
    net = income - spend["confirmed"] if count else None
    status = "partial" if count else "unknown"
    return {
        "household_id": household_id, "transaction_count": count,
        "expense_minor": spend["confirmed"] if count else None,
        "cash_surplus_minor": net, "coverage_status": status,
        "calculation_version": "ledger-v1", "warnings": notes,
        "month": month, "currency": "INR", "source": "approved_household_ledger",
        "income_minor": income if count else None,
        "confirmed_spending_minor": spend["confirmed"] if count else None,
        "net_after_confirmed_spending_minor": net,
        "unresolved_debits_minor": unresolved_debits,
        "unresolved_credits_minor": unresolved_credits,
        "coverage": {"status": status,
                     "unresolved_debits_minor": unresolved_debits,
                     "unresolved_credits_minor": unresolved_credits},
        "spending_by_category_minor": spend["by_category"],
        "excluded_movements": excluded,
        "notes": notes,
    }
