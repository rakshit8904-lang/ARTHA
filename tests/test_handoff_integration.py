import pytest

from app import create_app
from app.integrations import finance
from app.integrations.ledger_finance import monthly_summary
from app.households.relocation import calculate_relocation
from tests.conftest import csv_text
from tests.test_authorization import add_member
from tests.test_planning_tools import _plan


def holding(**changes):
    return dict(asset_name="Fictional fund", asset_type="mutual_fund", quantity="12.50000000",
                invested_minor=100000, current_value_minor=110000, as_of_date="2026-11-09",
                notes="Manual example") | changes


def test_portfolio_lifecycle_and_permissions(app, alice, bob):
    hid = alice.household()
    path = f"/households/{hid}/portfolio"
    assert bob.get(path).status_code == 404
    assert bob.post(path, holding()).status_code == 404
    made = alice.post(path, holding())
    assert made.status_code == 201
    item = made.get_json()["id"]
    got = alice.get(path).get_json()
    assert got["totals"]["gain_loss_minor"] == 10000
    assert got["holdings"][0]["quantity"] == "12.50000000"
    assert bob.client.delete(f"/api/v1/portfolio/{item}").status_code == 404
    add_member(app, hid, bob.user["id"], "viewer")
    assert bob.get(path).status_code == 200
    assert bob.post(path, holding()).status_code == 403
    assert bob.client.delete(f"/api/v1/portfolio/{item}").status_code == 403
    assert alice.client.delete(f"/api/v1/portfolio/{item}").status_code == 200
    assert alice.get(path).get_json()["holdings"] == []


def test_portfolio_invalid_inputs_never_create_holdings(alice):
    path = f"/households/{alice.household()}/portfolio"
    invalid = [dict(asset_name=None), dict(asset_type=[]), dict(quantity="NaN"),
               dict(quantity="0.000000001"), dict(quantity="-1"), dict(as_of_date="bad"),
               dict(invested_minor=True), dict(current_value_minor=10**30),
               dict(notes=["invalid"]), dict(notes="x"*501)]
    for changes in invalid:
        assert alice.post(path, holding(**changes)).status_code == 400, changes
    assert alice.get(path).get_json()["holdings"] == []


def test_relocation_api_requires_explicit_inputs_and_rejects_bool(alice, bob):
    path = f"/households/{alice.household()}/relocation/estimate"
    good = dict(monthly_income_minor=3000000, rent_minor=1000000, deposit_months=2)
    assert bob.post(path, good).status_code == 404
    result = alice.post(path, good)
    assert result.status_code == 200
    assert result.get_json()["upfront_cost_minor"] == 2000000
    for data in ({}, good | {"deposit_months":True}, good | {"rent_minor":True},
                 good | {"monthly_income_minor":10**30}):
        assert alice.post(path, data).status_code == 400
    with pytest.raises(ValueError):
        calculate_relocation(monthly_income_minor=True, rent_minor=0)


def test_connected_summary_contract_and_empty_month(app, alice, bob):
    # Shared legacy fixture deliberately disconnects the gateway. Verify the real
    # factory registers the production implementation, then exercise it via HTTP.
    create_app(dict(TESTING=True, SQLALCHEMY_DATABASE_URI=app.config["SQLALCHEMY_DATABASE_URI"]))
    assert finance.is_connected()
    hid = alice.household()
    path = f"/households/{hid}/summary?month=2026-11"
    empty = alice.get(path).get_json()
    assert empty["income_minor"] is None and empty["expense_minor"] is None
    assert empty["coverage_status"] == "unknown" and empty["transaction_count"] == 0
    assert alice.client.get(path).status_code == 200
    account = alice.account(hid)
    imp = alice.upload(account, csv_text([
        "2026-11-01,Salary,1000,credit,income,",
        "2026-11-02,Food,100,debit,purchase,Groceries",
        "2026-11-03,Transfer debit,200,debit,internal_transfer,",
        "2026-11-03,Transfer credit,200,credit,internal_transfer,",
        "2026-11-04,Unmatched refund,20,credit,refund,",
    ])).get_json()["import"]["id"]
    assert alice.post("/staged/approve", {"ids":[r["id"] for r in alice.rows(imp)]}).status_code == 200
    result = alice.get(path).get_json()
    assert (result["income_minor"],result["expense_minor"],result["cash_surplus_minor"]) == (100000,10000,90000)
    assert result["transaction_count"] == 5 and result["coverage_status"] == "partial"
    assert result["excluded_movements"]["internal_transfers_minor"] == 40000
    assert any("gross ledger-leg" in x for x in result["notes"])
    page = alice.client.get(path)
    assert page.status_code == 200 and "₹900.00" in page.get_data(as_text=True)
    assert bob.get(path).status_code == 404
    assert alice.get(path.replace("2026-11","0000-01")).status_code == 400


def test_allocation_recalculates_after_budget_edit_and_rejects_stale_save(alice):
    hid = alice.household()
    assert _plan(alice,hid).status_code == 302
    path = f"/households/{hid}/allocation?month=2026-11"
    saved = dict(revision="1",emergency_reserve="5000",savings_goals="7000",discretionary="3000")
    assert alice.client.post(path,data=saved).status_code == 302
    assert alice.client.post(path,data=saved).status_code == 409
    assert _plan(alice,hid,income="10000",revision="2").status_code == 302
    page = alice.client.get(path).get_data(as_text=True)
    assert "Saved allocations exceed" in page and "-₹8,000.00" in page


def test_new_household_pages_render_and_are_isolated(alice,bob):
    hid = alice.household()
    assert _plan(alice,hid).status_code == 302
    for suffix in ("", "/learning", "/calculators", "/recurring", "/rental-search",
                   "/city-affordability", "/allocation?month=2026-11"):
        path=f"/households/{hid}"+suffix
        assert alice.client.get(path).status_code == 200, path
        assert bob.client.get(path).status_code == 404, path
