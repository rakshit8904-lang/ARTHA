"""Deterministic relocation scenario calculations. All money inputs are INR paise."""


def calculate_relocation(*, monthly_income_minor, rent_minor, utilities_minor=0,
                          food_minor=0, transport_minor=0, other_minor=0,
                          deposit_months=0, moving_cost_minor=0, setup_cost_minor=0):
    values = [monthly_income_minor, rent_minor, utilities_minor, food_minor,
              transport_minor, other_minor, moving_cost_minor, setup_cost_minor]
    if any(type(v) is not int or not 0 <= v <= 999999999999 for v in values):
        raise ValueError("All monetary inputs must be non-negative integer paise values.")
    if type(deposit_months) is not int or not 0 <= deposit_months <= 24:
        raise ValueError("Deposit months must be between 0 and 24.")
    monthly_cost = rent_minor + utilities_minor + food_minor + transport_minor + other_minor
    surplus = monthly_income_minor - monthly_cost
    upfront = rent_minor * deposit_months + moving_cost_minor + setup_cost_minor
    rent_burden = (rent_minor / monthly_income_minor) if monthly_income_minor else None
    return {
        "monthly_income_minor": monthly_income_minor,
        "monthly_cost_minor": monthly_cost,
        "monthly_surplus_minor": surplus,
        "rent_burden_ratio": rent_burden,
        "upfront_cost_minor": upfront,
        "months_of_income_for_upfront_cost": (upfront / monthly_income_minor) if monthly_income_minor else None,
        "status": "surplus" if surplus > 0 else "break_even" if surplus == 0 else "deficit",
        "assumptions": ["User-entered estimates; not verified market quotes.",
                        "Security deposit is modelled as monthly rent multiplied by deposit months.",
                        "One-time moving and setup costs are excluded from monthly costs."],
    }
