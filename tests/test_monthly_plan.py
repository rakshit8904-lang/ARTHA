import pytest
from bs4 import BeautifulSoup
from tests.conftest import csv_text
from tests.test_authorization import add_member


@pytest.mark.parametrize("kind", ["family", "individual"])
def test_monthly_plan_roundtrip_and_isolation(app, alice, bob, kind):
    hid = alice.household()
    acct = alice.account(hid)
    path = f"/households/{hid}/plan?month=2026-11"
    imp = alice.upload(acct, csv_text(["2026-11-01,Milk,120,debit,purchase,Groceries",
                                      "2026-10-01,Other month,400,debit,purchase,Groceries",
                                      "2026-11-02,Pending,30,debit,purchase,Groceries"])).get_json()["import"]["id"]
    alice.post("/staged/approve", {"ids": [r["id"] for r in alice.rows(imp)[:2]]})
    data = dict(plan_type=kind, housing="owned", city="Pune", income="20000", other_income="500", revision="0",
                Milk="1000", Fruit="1000", Vegetables="1000", **{"Other groceries": "1000", "Monthly EMI": "1500"})
    assert alice.client.post(path, data=data).status_code == 302
    assert alice.client.post(path, data=data).status_code == 409
    alice.post("/auth/logout")
    alice.post("/auth/login", {"email":"alice@example.com","password":"correct-horse-1"})
    html = BeautifulSoup(alice.client.get(path).data, "html.parser")
    grocery = html.find("th", string="Groceries").parent
    assert [c.text for c in grocery.select("td")] == ["₹4,000.00", "₹120.00", "₹3,880.00"]
    assert "₹15,000.00" in html.get_text()
    assert bob.client.get(path).status_code == 404
    add_member(app, hid, bob.user["id"], "viewer")
    assert bob.client.get(path).status_code == 200
    assert bob.client.post(path, data=dict(data,revision="1")).status_code == 403
    assert alice.client.post(path, data=dict(data,revision="1", Milk="-5")).status_code == 400
    assert alice.client.post(path, data=dict(data,revision="1", Milk="1050.25")).status_code == 302
    assert "₹4,050.25" in alice.client.get(path).get_data(as_text=True)
    assert b'id="monthly-plan"' in alice.client.get(path.replace("2026-11","2026-12")).data


@pytest.mark.parametrize("housing,included,expected,support", [
    ("owned", "", "₹1,500.00", "₹5,000.00"), ("rented", "yes", "₹12,000.00", "₹5,000.00"),
    ("rented", "no", "₹13,500.00", "₹5,000.00"), ("family", "", "₹2,000.00", "₹3,000.00"),
])
def test_only_applicable_housing_costs_count(alice, housing, included, expected, support):
    path = f"/households/{alice.household()}/plan?month=2026-11"
    form = dict(plan_type="individual", city="Pune", income="30000", revision="0", housing=housing,
                maintenance_included=included, Rent="12000", **{"Society maintenance":"1500",
                "Pledged to parents":"5000", "Housing contribution":"2000", "Monthly EMI":"700"})
    assert alice.client.post(path, data=form).status_code == 302
    html = BeautifulSoup(alice.client.get(path).data, "html.parser")
    for group, value in [("Housing/Rent", expected), ("Family support", support), ("Loan commitments","₹700.00")]:
        assert html.find("th", string=group).parent.td.text == value
    edit = BeautifulSoup(alice.client.get(path + "&edit=1").data, "html.parser")
    assert edit.select_one('[name=housing] option[selected]')["value"] == housing
    assert edit.select_one('[name="Pledged to parents"]')["value"] == "5000.00"


def test_legacy_plan_waits_for_explicit_choice(app, alice):
    from app.extensions import db
    from app.models import MonthlyPlan
    hid = alice.household()
    path = f"/households/{hid}/plan?month=2026-11"
    with app.app_context():
        db.session.add(MonthlyPlan(household_id=hid, month="2026-11", plan_type="family", city="Pune",
                                  income=5000000, other_income=0, limits={"Rent":1000000,"Society maintenance":50000}, revision=1))
        db.session.commit()
    edit = BeautifulSoup(alice.client.get(path + "&edit=1").data, "html.parser")
    assert not edit.select('[name=housing] option[selected]')
    assert edit.select_one('[name=Rent]')["value"] == "10000.00"
    base = dict(plan_type="family", city="Pune", income="50000", revision="1")
    assert alice.client.post(path, data=base).status_code == 400
    assert alice.client.post(path, data=dict(base,housing="family", **{"Housing contribution":"2000","Pledged to parents":"1000"})).status_code == 400
    assert "₹10,500.00" in alice.client.get(path).get_data(as_text=True)
    assert alice.client.post(path, data=dict(base,housing="family", **{"Housing contribution":"0","Pledged to parents":"5000"})).status_code == 302
