"""Deterministic saved-goal calculations. Money is INR paise; no investment return is assumed."""
from decimal import Decimal, ROUND_CEILING, localcontext

PURPOSES = {"purchase": "A purchase", "education": "Education", "family": "A family commitment",
            "move": "Moving city", "reserve": "A reserve or safety fund", "travel": "Travel", "other": "Something else"}
ONGOING_LINES = 3
MAX_MINOR = 999999999999


def month_index(month):
    year, mon = (int(part) for part in month.split("-"))
    return year * 12 + mon - 1


def saving_schedule(remaining, months):
    """One contribution per month; amount rounded up to whole rupees, the last one absorbs rounding."""
    if remaining == 0:
        return {"monthly_needed_minor": 0, "payments": 0, "final_payment_minor": 0}
    per = -(-remaining // months)
    per = -(-per // 100) * 100
    payments = -(-remaining // per)
    return {"monthly_needed_minor": per, "payments": payments,
            "final_payment_minor": remaining - per * (payments - 1)}


def loan_emi(principal, annual_rate, term_months):
    """Reducing-balance EMI, rounded up to the paise. annual_rate is a Decimal percentage."""
    if annual_rate == 0:
        return -(-principal // term_months)
    with localcontext() as ctx:
        ctx.prec = 40
        r = annual_rate / Decimal(1200)
        growth = (1 + r) ** term_months
        emi = Decimal(principal) * r * growth / (growth - 1)
        return int(emi.to_integral_value(rounding=ROUND_CEILING))


def calculate_goal(*, target_minor, saved_minor, assigned_minor, target_month, current_month,
                   ongoing=None, loan=None):
    for value in (target_minor, saved_minor, assigned_minor):
        if type(value) is not int or not 0 <= value <= MAX_MINOR:
            raise ValueError("Amounts must be non-negative whole-paise values.")
    if target_minor <= 0:
        raise ValueError("Enter a target amount greater than zero.")
    months = month_index(target_month) - month_index(current_month)
    if months < 1:
        raise ValueError("Choose a target month after the current month.")
    remaining = max(target_minor - saved_minor, 0)
    plan = saving_schedule(remaining, months)
    result = {"months": months, "remaining_minor": remaining, **plan,
              "assigned_minor": assigned_minor, "gap_minor": plan["monthly_needed_minor"] - assigned_minor,
              "months_at_assigned": (-(-remaining // assigned_minor) if assigned_minor else None) if remaining else 0,
              "assumptions": ["No investment return is assumed (0%).",
                              "One contribution per month, starting this month; the last one is in the month before the target month.",
                              "All amounts are your own estimates, not quotes."]}

    ongoing = ongoing or []
    entered = [line["amount_minor"] for line in ongoing if line["amount_minor"] is not None]
    result["ongoing_total_minor"] = sum(entered) if entered else None
    result["ongoing_missing"] = [line["label"] for line in ongoing if line["amount_minor"] is None]

    if loan:
        amount, rate, term, fees = loan["loan_minor"], Decimal(loan["rate"]), loan["term_months"], loan["fees_minor"]
        if amount <= 0 or amount > target_minor:
            raise ValueError("The loan amount must be more than zero and no more than the target amount.")
        emi = loan_emi(amount, rate, term)
        down = target_minor - amount + fees
        down_remaining = max(down - saved_minor, 0)
        result["loan"] = {"emi_minor": emi, "total_repaid_minor": emi * term,
                          "total_interest_minor": emi * term - amount, "term_months": term,
                          "down_payment_minor": down, "down_remaining_minor": down_remaining,
                          **saving_schedule(down_remaining, months)}
        result["assumptions"].append("Loan figures use the standard reducing-balance EMI at the rate you entered; "
                                     "a lender's final EMI, charges and eligibility may differ.")
    return result
