from bs4 import BeautifulSoup

from app.extensions import db
from app.households.profile import monthly_equivalent
from app.models import MonthlyPlan, ProfileItem, Transaction
from tests.conftest import Api
from tests.test_authorization import add_member
from tests.test_planning_tools import _plan


def row(n, **values):
    return {f"{n}-{k.replace('x_', 'x-')}": v for k, v in values.items()}


def post(api, hid, section, *rows, **extra):
    data = {}
    for r in rows:
        data.update(r)
    return api.client.post(f"/households/{hid}/profile/{section}", data=data | extra)


def items(app, **filters):
    with app.app_context():
        return ProfileItem.query.filter_by(**filters).order_by(ProfileItem.kind).all()


SALARY = dict(kind="salary", label="Job", state="amount", amount="50000", frequency="monthly",
              x_stability="steady", visibility="household")


def test_monthly_equivalent_spreads_periodic_amounts():
    assert monthly_equivalent(12000000, "yearly") == 1000000
    assert monthly_equivalent(100000, "quarterly") == 33333
    assert monthly_equivalent(100000, "one_time") is None and monthly_equivalent(None, "monthly") is None


def test_income_saved_with_unknown_kept_separate_from_zero(app, alice):
    hid = alice.household()
    res = post(alice, hid, "income", row(0, **SALARY),
               row(1, kind="family", state="unknown", visibility="household"),
               row(2, kind="rental", state="zero", visibility="household"), row(3, kind="", state=""))
    assert res.status_code == 302
    saved = {i.kind: i for i in items(app, household_id=hid)}
    assert saved["salary"].amount_minor == 5000000 and saved["salary"].details == {"stability": "steady"}
    assert saved["family"].state == "unknown" and saved["family"].amount_minor is None
    assert saved["rental"].state == "zero" and saved["rental"].amount_minor is None
    overview = BeautifulSoup(alice.client.get(f"/households/{hid}/profile").data, "html.parser")
    card = overview.select_one("#profile-income").get_text()
    assert "3 entries" in card and "1 amount not known yet" in card and "₹50,000.00 (partial)" in card
    assert "Not started" in overview.select_one("#profile-assets").get_text()


def test_bills_use_real_frequency_and_next_due(app, alice):
    hid = alice.household()
    post(alice, hid, "bills", row(0, kind="school_fees", label="Riya", state="amount", amount="60000", frequency="yearly",
                                  date="2027-04-01", visibility="household"),
         row(1, kind="medical_insurance", state="amount", amount="1500", frequency="quarterly", visibility="household"))
    page = BeautifulSoup(alice.client.get(f"/households/{hid}/profile/bills").data, "html.parser")
    summary = page.select_one("#profile-summary").get_text()
    assert "₹5,500.00" in summary and "2027-04-01" in summary
    assert items(app, kind="school_fees")[0].frequency == "yearly"


def test_assets_liabilities_and_savings_details(app, alice):
    hid = alice.household()
    assert post(alice, hid, "assets", row(0, kind="bank", state="amount", amount="80000", date="2026-11-01",
                                          x_accessible="yes", visibility="household"),
                row(1, kind="gold", state="unknown", x_accessible="no", visibility="household")).status_code == 302
    assert post(alice, hid, "liabilities", row(0, kind="education_loan", state="amount", amount="300000",
                                               x_monthly_payment="6500", x_rate="9.5", visibility="household")).status_code == 302
    assert post(alice, hid, "savings", row(0, kind="recurring_deposit", state="amount", amount="12000",
                                           x_monthly_deposit="2000", x_term_months="24", x_rate="7", visibility="household"),
                row(1, kind="reserve", state="amount", amount="30000", visibility="household")).status_code == 302
    loan = items(app, kind="education_loan")[0]
    assert loan.details == {"monthly_payment": 650000, "rate": "9.5"}
    page = BeautifulSoup(alice.client.get(f"/households/{hid}/profile").data, "html.parser")
    assert "₹6,500.00" in page.select_one("#profile-liabilities").get_text()
    assert "₹30,000.00" in page.select_one("#profile-savings").get_text()
    assets = BeautifulSoup(alice.client.get(f"/households/{hid}/profile/assets").data, "html.parser")
    assert "within about a week: ₹80,000.00" in assets.select_one("#profile-summary").get_text()


def test_invalid_rows_save_nothing(app, alice):
    hid = alice.household()
    bad = [dict(state="amount", amount=""), dict(state="unknown", amount="100"), dict(frequency=""),
           dict(kind="car"), dict(state="maybe"), dict(amount="-1"), dict(amount="1.001"), dict(visibility=""),
           dict(x_stability="great")]
    for change in bad:
        res = post(alice, hid, "income", row(0, **SALARY), row(1, **(SALARY | dict(kind="other") | change)))
        assert res.status_code == 400, change
        assert "Entry 2" in res.get_data(as_text=True)
    assert post(alice, hid, "liabilities", row(0, kind="other", state="zero", x_rate="51", visibility="household")).status_code == 400
    assert post(alice, hid, "savings", row(0, kind="other", state="zero", x_term_months="0", visibility="household")).status_code == 400
    assert items(app, household_id=hid) == []
    assert alice.client.get(f"/households/{hid}/profile/pets").status_code == 404


def test_edit_remove_and_stale_revision(app, alice):
    hid = alice.household()
    post(alice, hid, "income", row(0, **SALARY))
    item = items(app, kind="salary")[0]
    edit = row(0, **(SALARY | dict(amount="55000")), id=item.id, revision="1")
    assert post(alice, hid, "income", edit).status_code == 302
    assert items(app, kind="salary")[0].amount_minor == 5500000
    assert post(alice, hid, "income", edit).status_code == 409
    assert items(app, kind="salary")[0].revision == 2
    assert post(alice, hid, "income", row(0, **SALARY, id=item.id, revision="2", remove="1")).status_code == 302
    assert items(app, household_id=hid) == []


def test_none_of_these(app, alice):
    hid = alice.household()
    assert post(alice, hid, "liabilities", none="1").status_code == 302
    assert "You said none" in alice.client.get(f"/households/{hid}/profile").get_data(as_text=True)
    assert post(alice, hid, "liabilities", row(0, kind="credit_card", state="zero", visibility="household"), none="1").status_code == 400
    assert post(alice, hid, "liabilities", row(0, kind="credit_card", state="zero", visibility="household")).status_code == 302
    assert [i.kind for i in items(app, section="liabilities")] == ["credit_card"]


def test_private_items_follow_goal_privacy_rules(app, alice, bob):
    carol = Api(app, "carol@example.com", "Carol")
    hid = alice.household()
    add_member(app, hid, bob.user["id"], "viewer")
    add_member(app, hid, carol.user["id"], "viewer")
    assert post(bob, hid, "assets", row(0, kind="cash", label="Bob cash", state="amount", amount="5000", visibility="household")).status_code == 403
    assert post(bob, hid, "assets", row(0, kind="cash", label="Bob cash", state="amount", amount="5000", visibility="private")).status_code == 302
    assert post(alice, hid, "assets", row(0, kind="bank", label="Joint", state="amount", amount="90000", visibility="household")).status_code == 302
    assert "Bob cash" in alice.client.get(f"/households/{hid}/profile/assets").get_data(as_text=True)
    carol_page = carol.client.get(f"/households/{hid}/profile/assets").get_data(as_text=True)
    assert "Bob cash" not in carol_page and "Joint" in carol_page
    assert "₹95,000.00" in alice.client.get(f"/households/{hid}/profile").get_data(as_text=True)
    assert "₹90,000.00" in carol.client.get(f"/households/{hid}/profile").get_data(as_text=True)
    private, joint = items(app, kind="cash")[0], items(app, kind="bank")[0]
    assert post(alice, hid, "assets", row(0, kind="cash", label="Bob cash", state="amount", amount="6000",
                                          visibility="household", id=private.id, revision="1")).status_code == 403
    assert post(alice, hid, "assets", row(0, kind="cash", label="Bob cash", state="amount", amount="6000",
                                          visibility="private", id=private.id, revision="1")).status_code == 302
    assert post(bob, hid, "assets", row(0, kind="bank", state="zero", visibility="household",
                                        id=joint.id, revision="1")).status_code == 403
    assert post(carol, hid, "assets", row(0, kind="cash", state="zero", visibility="private",
                                          id=private.id, revision="2")).status_code == 404
    assert post(bob, hid, "assets", none="1").status_code == 403
    assert post(alice, hid, "liabilities", none="1").status_code == 302
    assert post(bob, hid, "liabilities", row(0, kind="family_loan", state="unknown", visibility="private")).status_code == 302
    assert items(app, kind="_none") and items(app, kind="family_loan")


def test_profile_isolation_csrf_and_no_side_effects(app, alice, bob):
    hid = alice.household()
    _plan(alice, hid)
    with app.app_context():
        plan = db.session.get(MonthlyPlan, (hid, "2026-11"))
        before = (plan.revision, dict(plan.limits), Transaction.query.count())
    post(alice, hid, "income", row(0, **SALARY))
    with app.app_context():
        plan = db.session.get(MonthlyPlan, (hid, "2026-11"))
        assert (plan.revision, dict(plan.limits), Transaction.query.count()) == before
    assert bob.client.get(f"/households/{hid}/profile").status_code == 404
    assert post(bob, hid, "income", row(0, **SALARY)).status_code == 404
    app.config["CSRF_ENABLED"] = True
    assert post(alice, hid, "income", row(0, **SALARY)).status_code == 400
    assert len(items(app, household_id=hid)) == 1
