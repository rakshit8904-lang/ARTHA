from app.households.relocation import calculate_relocation


def test_relocation_estimate_separates_monthly_and_upfront_costs():
    result = calculate_relocation(
        monthly_income_minor=3000000, rent_minor=1000000, utilities_minor=200000,
        food_minor=500000, transport_minor=100000, other_minor=200000,
        deposit_months=2, moving_cost_minor=150000, setup_cost_minor=50000)
    assert result["monthly_cost_minor"] == 2000000
    assert result["monthly_surplus_minor"] == 1000000
    assert result["upfront_cost_minor"] == 2200000
    assert result["status"] == "surplus"


def test_relocation_rejects_negative_or_invalid_inputs():
    try:
        calculate_relocation(monthly_income_minor=100, rent_minor=-1)
    except ValueError:
        pass
    else:
        assert False, "negative money must be rejected"


def test_relocation_zero_income_has_no_division_error():
    result = calculate_relocation(monthly_income_minor=0, rent_minor=100)
    assert result["rent_burden_ratio"] is None
    assert result["status"] == "deficit"
