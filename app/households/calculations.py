"""Deterministic, educational household-planning calculations.

All currency inputs and outputs are integer paise. RD results are estimates,
not bank quotations: monthly instalments are modelled with an equivalent
monthly rate derived from the selected nominal compounding convention.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


PAISE = Decimal("100")
ONE_PAISE = Decimal("1")


def rupees_to_paise(value):
    """Parse a non-negative rupee amount and return integer paise."""
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        raise ValueError("Enter a valid rupee amount.") from None
    if (not amount.is_finite() or amount < 0 or amount > Decimal("9999999999.99")
            or amount.as_tuple().exponent < -2):
        raise ValueError("Amounts must be nonnegative, within the supported limit, and have at most two decimal places.")
    return int((amount * PAISE).quantize(ONE_PAISE, rounding=ROUND_HALF_UP))


def emergency_reserve(essential_monthly_paise, target_months, current_reserve_paise,
                      monthly_contribution_paise):
    """Calculate a user-selected reserve target and contribution runway."""
    values = (essential_monthly_paise, current_reserve_paise, monthly_contribution_paise)
    if any(not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("Reserve amounts must be nonnegative whole-paise values.")
    if essential_monthly_paise <= 0:
        raise ValueError("Enter essential monthly expenses greater than zero.")
    if not isinstance(target_months, int) or not 1 <= target_months <= 120:
        raise ValueError("Choose a target between 1 and 120 months.")

    target = essential_monthly_paise * target_months
    shortfall = max(0, target - current_reserve_paise)
    progress = min(Decimal(current_reserve_paise) * 100 / Decimal(target), Decimal("100"))
    months_to_target = (0 if shortfall == 0 else
                        (shortfall + monthly_contribution_paise - 1) // monthly_contribution_paise
                        if monthly_contribution_paise else None)
    return {
        "target_paise": target,
        "shortfall_paise": shortfall,
        "progress_percent": progress.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
        "months_to_target": months_to_target,
    }


def recurring_deposit(monthly_deposit_paise, duration_months, annual_rate_percent,
                      compounding="quarterly", deposit_timing="end"):
    """Estimate RD maturity using a monthly-equivalent periodic rate.

    ``quarterly`` uses a nominal annual rate divided by four, converted to an
    equivalent monthly rate. ``monthly`` uses the nominal annual rate divided
    by twelve. Beginning-of-month deposits earn one extra monthly period.
    """
    if not isinstance(monthly_deposit_paise, int) or monthly_deposit_paise <= 0:
        raise ValueError("Monthly deposit must be greater than zero.")
    if not isinstance(duration_months, int) or not 1 <= duration_months <= 120:
        raise ValueError("Choose a duration between 1 and 120 months.")
    try:
        annual_rate = Decimal(str(annual_rate_percent).strip())
    except (InvalidOperation, ValueError, AttributeError):
        raise ValueError("Enter a valid annual interest rate.") from None
    if (not annual_rate.is_finite() or not Decimal("0") <= annual_rate <= Decimal("100")
            or annual_rate.as_tuple().exponent < -2):
        raise ValueError("Annual interest rate must be between 0% and 100%, with up to two decimal places.")
    if compounding not in ("monthly", "quarterly"):
        raise ValueError("Choose monthly or quarterly compounding.")
    if deposit_timing not in ("beginning", "end"):
        raise ValueError("Choose beginning- or end-of-month deposits.")

    total_deposits = monthly_deposit_paise * duration_months
    with localcontext() as context:
        context.prec = 32
        periods_per_year = Decimal(12 if compounding == "monthly" else 4)
        periodic_rate = annual_rate / Decimal("100") / periods_per_year
        if periodic_rate == 0:
            monthly_rate = Decimal("0")
            maturity = Decimal(total_deposits)
        else:
            months_per_period = Decimal(12) / periods_per_year
            monthly_rate = (Decimal(1) + periodic_rate) ** (Decimal(1) / months_per_period) - Decimal(1)
            growth = (Decimal(1) + monthly_rate) ** duration_months
            maturity = Decimal(monthly_deposit_paise) * (growth - Decimal(1)) / monthly_rate
            if deposit_timing == "beginning":
                maturity *= Decimal(1) + monthly_rate
        maturity_paise = int(maturity.quantize(ONE_PAISE, rounding=ROUND_HALF_UP))

    return {
        "total_deposits_paise": total_deposits,
        "interest_paise": maturity_paise - total_deposits,
        "maturity_paise": maturity_paise,
    }


def savings_goal(goal_amount_paise, current_saved_paise, monthly_contribution_paise):
    """Estimate the time to reach a savings goal without assuming investment returns."""
    values = (goal_amount_paise, current_saved_paise, monthly_contribution_paise)
    if any(not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("Savings goal amounts must be nonnegative whole-paise values.")
    if goal_amount_paise <= 0:
        raise ValueError("Enter a savings goal greater than zero.")
    shortfall = max(0, goal_amount_paise - current_saved_paise)
    months = (0 if shortfall == 0 else
              (shortfall + monthly_contribution_paise - 1) // monthly_contribution_paise
              if monthly_contribution_paise else None)
    progress = min(Decimal(current_saved_paise) * 100 / Decimal(goal_amount_paise), Decimal("100"))
    return {
        "goal_paise": goal_amount_paise,
        "shortfall_paise": shortfall,
        "progress_percent": progress.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
        "months_to_goal": months,
    }
