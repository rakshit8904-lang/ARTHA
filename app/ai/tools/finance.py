"""Deterministic read-only calculations over the authorised monthly summary."""
from decimal import Decimal, ROUND_HALF_UP


def paise_to_rupees(value):
    if value is None:
        return None
    return str((Decimal(int(value)) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_financial_insights(summary):
    """Return a small, minimised set of derived figures; never infer missing values as zero."""
    if not isinstance(summary, dict):
        return None
    income = summary.get("income_minor")
    spending = summary.get("confirmed_spending_minor")
    if not isinstance(income, int) or not isinstance(spending, int):
        return {"availability": "partial", "reason": "Income or spending is not fully available."}
    result = {
        "income_inr": paise_to_rupees(income),
        "confirmed_spending_inr": paise_to_rupees(spending),
        "net_after_confirmed_spending_inr": paise_to_rupees(income - spending),
        "coverage_status": summary.get("coverage_status", "unknown"),
    }
    result["confirmed_spending_to_income_ratio"] = (
        round(spending / income, 4) if income > 0 else None
    )
    result["interpretation_limit"] = (
        "This is a comparison of approved income and confirmed spending, not a bank balance "
        "or complete disposable-income calculation."
    )
    return result
