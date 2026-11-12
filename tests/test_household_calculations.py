from decimal import Decimal

import pytest

from app.households.calculations import emergency_reserve, recurring_deposit, savings_goal, rupees_to_paise


def test_rupees_to_paise_uses_decimal_and_rejects_precision_loss():
    assert rupees_to_paise("123.45") == 12_345
    assert rupees_to_paise("0") == 0
    with pytest.raises(ValueError):
        rupees_to_paise("1.234")
    with pytest.raises(ValueError):
        rupees_to_paise("-1.00")


def test_emergency_reserve_uses_user_selected_months_and_contribution():
    result = emergency_reserve(50_000, 6, 100_000, 50_000)
    assert result == {
        "target_paise": 300_000,
        "shortfall_paise": 200_000,
        "progress_percent": Decimal("33.3"),
        "months_to_target": 4,
    }


def test_emergency_reserve_handles_funded_target_and_zero_contribution():
    funded = emergency_reserve(10_000, 3, 40_000, 0)
    assert funded["shortfall_paise"] == 0 and funded["months_to_target"] == 0
    unfunded = emergency_reserve(10_000, 3, 0, 0)
    assert unfunded["months_to_target"] is None


def test_rd_zero_rate_and_month_end_deposits():
    result = recurring_deposit(10_000, 12, "0", "quarterly", "end")
    assert result == {
        "total_deposits_paise": 120_000,
        "interest_paise": 0,
        "maturity_paise": 120_000,
    }


def test_rd_timing_and_compounding_affect_estimate():
    end_quarterly = recurring_deposit(10_000, 12, "6", "quarterly", "end")
    beginning_quarterly = recurring_deposit(10_000, 12, "6", "quarterly", "beginning")
    end_monthly = recurring_deposit(10_000, 12, "6", "monthly", "end")
    assert beginning_quarterly["maturity_paise"] > end_quarterly["maturity_paise"]
    assert end_monthly["maturity_paise"] > end_quarterly["maturity_paise"]
    assert end_quarterly["total_deposits_paise"] == 120_000
    assert end_quarterly["interest_paise"] > 0


def test_calculator_pages_are_household_scoped_and_return_estimates(alice, bob):
    household_id = alice.household()
    page = alice.client.get(f"/households/{household_id}/calculators")
    assert page.status_code == 200
    assert b"Emergency reserve" in page.data and b"Recurring Deposit" in page.data
    assert bob.client.get(f"/households/{household_id}/calculators").status_code == 404

    reserve = alice.client.post(f"/households/{household_id}/calculators", data={
        "calculator": "reserve", "essential_monthly_expenses": "500",
        "target_months": "6", "current_reserve": "1000", "monthly_contribution": "500",
    })
    assert reserve.status_code == 200
    assert b"\xe2\x82\xb93,000.00" in reserve.data
    assert b"4 months" in reserve.data

    rd = alice.client.post(f"/households/{household_id}/calculators", data={
        "calculator": "rd", "monthly_deposit": "100", "duration_months": "12",
        "annual_rate": "6", "compounding": "quarterly", "deposit_timing": "end",
    })
    assert rd.status_code == 200
    assert b"\xe2\x82\xb91,233.39" in rd.data


def test_savings_goal_timeline_without_assumed_returns():
    result = savings_goal(100_000, 25_000, 15_000)
    assert result["shortfall_paise"] == 75_000
    assert result["months_to_goal"] == 5
    assert result["progress_percent"] == Decimal("25.0")


def test_savings_goal_funded_and_zero_contribution_cases():
    funded = savings_goal(100_000, 120_000, 0)
    assert funded["shortfall_paise"] == 0
    assert funded["months_to_goal"] == 0
    waiting = savings_goal(100_000, 0, 0)
    assert waiting["months_to_goal"] is None


def test_rental_search_is_household_scoped_and_builds_encoded_external_query(alice, bob):
    household_id = alice.household()
    assert alice.client.get(f"/households/{household_id}/rental-search").status_code == 200
    assert bob.client.get(f"/households/{household_id}/rental-search").status_code == 404
    result = alice.client.post(f"/households/{household_id}/rental-search", data={
        "city": "Pune & Baner", "max_rent": "18000", "bedrooms": "2",
        "property_type": "apartment",
    })
    assert result.status_code == 200
    assert b"https://www.google.com/search?" in result.data
    assert b"Magicbricks" in result.data and b"under+INR+18000" in result.data


def test_rental_search_rejects_invalid_budget(alice):
    household_id = alice.household()
    result = alice.client.post(f"/households/{household_id}/rental-search", data={
        "city": "Pune", "max_rent": "-10", "bedrooms": "any", "property_type": "any",
    })
    assert result.status_code == 200
    assert b"valid maximum monthly rent" in result.data
