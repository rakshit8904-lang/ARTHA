import pytest
from bs4 import BeautifulSoup

from app.extensions import db
from app.households.goal_routes import india_today
from app.households.goals import calculate_goal, loan_emi, saving_schedule
from app.models import MonthlyPlan, SavedGoal, Transaction
from tests.test_authorization import add_member
from tests.test_planning_tools import _plan


def month_ahead(months):
    today = india_today()
    index = today.year * 12 + today.month - 1 + months
    return f"{index // 12}-{index % 12 + 1:02d}"


def fields(**changes):
    return dict(name="Course fees", purpose="education", visibility="household", revision="0", target_minor="900000", saved_minor="180000",
                saved_as_of=india_today().isoformat(), assigned_minor="12000",
                target_month=month_ahead(36), action="save") | changes


def calc(**kw):
    base = dict(target_minor=90000000, saved_minor=18000000, assigned_minor=1200000,
                target_month="2029-11", current_month="2026-11")
    return calculate_goal(**(base | kw))


def test_deadline_first_baseline_matches_plan_example():
    r = calc()
    assert (r["months"], r["remaining_minor"], r["monthly_needed_minor"], r["gap_minor"]) == (36, 72000000, 2000000, 800000)
    assert r["months_at_assigned"] == 60 and r["ongoing_total_minor"] is None


def test_rounding_and_final_payment():
    assert saving_schedule(1000001, 3) == {"monthly_needed_minor": 333400, "payments": 3, "final_payment_minor": 333201}
    assert saving_schedule(100, 3) == {"monthly_needed_minor": 100, "payments": 1, "final_payment_minor": 100}
    assert calc(saved_minor=95000000)["remaining_minor"] == 0
    assert calc(saved_minor=95000000)["monthly_needed_minor"] == 0


@pytest.mark.parametrize("month", ["2026-11", "2026-10"])
def test_target_month_must_be_after_current_month(month):
    with pytest.raises(ValueError, match="after the current month"):
        calc(target_month=month)


def test_loan_emi_and_comparison():
    assert loan_emi(1200000, 0, 12) == 100000
    assert loan_emi(70000000, __import__("decimal").Decimal("9"), 60) == 1453085
    r = calc(saved_minor=0, loan=dict(loan_minor=70000000, rate="9", term_months=60, fees_minor=500000))
    loan = r["loan"]
    assert loan["down_payment_minor"] == 20500000 and loan["total_interest_minor"] == 1453085 * 60 - 70000000
    assert loan["monthly_needed_minor"] < r["monthly_needed_minor"]
    with pytest.raises(ValueError, match="no more than the target"):
        calc(loan=dict(loan_minor=90000001, rate="9", term_months=60, fees_minor=0))


def test_ongoing_costs_keep_unknown_separate_from_zero():
    r = calc(ongoing=[{"label": "Hostel", "amount_minor": 150000}, {"label": "Books", "amount_minor": 0},
                      {"label": "Travel home", "amount_minor": None}])
    assert r["ongoing_total_minor"] == 150000 and r["ongoing_missing"] == ["Travel home"]
    assert r["remaining_minor"] == 72000000  # ongoing costs never change the savings target
    assert calc(ongoing=[{"label": "Upkeep", "amount_minor": None}])["ongoing_total_minor"] is None


def test_save_reopen_edit_and_stale_revision(app, alice):
    hid = alice.household()
    path = f"/households/{hid}/goals"
    created = alice.client.post(path, data=fields(ongoing_label_1="Hostel", ongoing_amount_1="1500",
                                                  ongoing_label_2="Travel home"))
    assert created.status_code == 302
    detail = created.headers["Location"]
    page = BeautifulSoup(alice.client.get(detail).data, "html.parser")
    text = page.get_text()
    assert "₹20,000.00" in text and "Short by ₹8,000.00" in text and "₹1,500.00 a month" in text
    assert page.select_one("#ongoing_amount_1")["value"] == "1500.00" and page.select_one("#ongoing_amount_2")["value"] == ""
    assert "not entered yet for: Travel home" in page.select_one("#goal-results").get_text()
    assert page.select_one("#purpose option[selected]")["value"] == "education"
    assert "Education" in page.select_one(".goal-card").get_text()
    assert alice.client.post(detail, data=fields(revision="1", ongoing_label_1="Hostel", ongoing_amount_1="1500", ongoing_label_2="Travel home", name="Car 2029")).status_code == 302
    assert alice.client.post(detail, data=fields(revision="1", name="Stale")).status_code == 409
    with app.app_context():
        row = SavedGoal.query.one()
        assert row.name == "Car 2029" and row.revision == 2 and row.inputs["target_minor"] == 90000000
        assert row.inputs["ongoing"][1] == {"label": "Travel home", "amount_minor": None} and row.inputs["loan"] is None


def test_loan_fields_saved_and_compared(alice):
    path = f"/households/{alice.household()}/goals"
    loan = dict(loan_minor="700000", rate="9", term_months="60", fees_minor="5000")
    detail = alice.client.post(path, data=fields(**loan)).headers["Location"]
    page = BeautifulSoup(alice.client.get(detail).data, "html.parser")
    assert "₹14,530.85" in page.select_one("#goal-loan-compare").get_text()
    assert page.select_one("#rate")["value"] == "9"


def test_total_assigned_compared_with_goal_allocation(app, alice):
    hid = alice.household()
    path = f"/households/{hid}/goals"
    alice.client.post(path, data=fields())
    alice.client.post(path, data=fields(name="Laptop", target_minor="60000", assigned_minor="5000"))
    assert "unknown" in BeautifulSoup(alice.client.get(path).data, "html.parser").select_one("#goal-totals").get_text()
    month = india_today().strftime("%Y-%m")
    with app.app_context():
        db.session.add(MonthlyPlan(household_id=hid, month=month, plan_type="individual", city="Pune", income=5000000,
                                   other_income=0, limits={}, revision=1, allocation={"savings_goals": 1500000}))
        db.session.commit()
    totals = BeautifulSoup(alice.client.get(path).data, "html.parser").select_one("#goal-totals").get_text()
    assert "₹17,000.00" in totals and "₹2,000.00 more" in totals


def test_saving_goal_never_changes_plan_or_ledger(app, alice):
    hid = alice.household()
    _plan(alice, hid)
    with app.app_context():
        plan = db.session.get(MonthlyPlan, (hid, "2026-11"))
        before = (plan.revision, dict(plan.limits), plan.allocation, Transaction.query.count())
    assert alice.client.post(f"/households/{hid}/goals", data=fields()).status_code == 302
    with app.app_context():
        plan = db.session.get(MonthlyPlan, (hid, "2026-11"))
        assert (plan.revision, dict(plan.limits), plan.allocation, Transaction.query.count()) == before


def test_goal_isolation_viewer_and_csrf(app, alice, bob):
    hid = alice.household()
    other = bob.household()
    path = f"/households/{hid}/goals"
    detail = alice.client.post(path, data=fields()).headers["Location"]
    assert bob.client.get(detail).status_code == 404
    assert bob.client.post(path, data=fields()).status_code == 404
    assert bob.client.get(detail.replace(hid, other)).status_code == 404
    add_member(app, hid, bob.user["id"], "viewer")
    assert bob.client.get(detail).status_code == 200
    assert bob.client.post(detail, data=fields(action="calculate")).status_code == 200
    assert bob.client.post(detail, data=fields(revision="1")).status_code == 403
    app.config["CSRF_ENABLED"] = True
    rejected = alice.client.post(detail, data=fields(revision="1"))
    assert rejected.status_code == 400 and b"CSRF" in rejected.data


def test_goal_rejects_invalid_inputs(app, alice):
    path = f"/households/{alice.household()}/goals"
    today = india_today()
    for changes in [dict(name=""), dict(target_minor="0"), dict(target_minor="-1"), dict(saved_minor="1.001"),
                    dict(assigned_minor=""), dict(target_month=today.strftime("%Y-%m")), dict(target_month="2026-13"),
                    dict(saved_as_of="2999-01-01"), dict(saved_as_of="soon"), dict(purpose=""), dict(purpose="car"),
                    dict(ongoing_amount_1="100"), dict(ongoing_label_1="Fees", ongoing_amount_1="-5"),
                    dict(loan_minor="1000"), dict(loan_minor="1000", rate="51", term_months="12", fees_minor="0"),
                    dict(loan_minor="1000", rate="9", term_months="0", fees_minor="0"),
                    dict(loan_minor="1000000", rate="9", term_months="12", fees_minor="0"),
                    dict(action="delete"), dict(target_minor="NaN")]:
        assert alice.client.post(path, data=fields(**changes)).status_code == 400, changes
    with app.app_context():
        assert SavedGoal.query.count() == 0
