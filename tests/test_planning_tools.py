from app.extensions import db
from app.models import RecurringExpense
from tests.conftest import csv_text


def _plan(alice, household_id, income="30000", revision="0"):
    path = f"/households/{household_id}/plan?month=2026-11"
    form = dict(plan_type="individual", housing="owned", city="Pune", income=income,
                other_income="0", revision=revision, **{"Society maintenance":"1000", "Monthly EMI":"2000"})
    return alice.client.post(path, data=form)


def test_monthly_allocation_persists_and_is_bounded(alice, bob, app):
    hid = alice.household()
    assert _plan(alice, hid).status_code == 302
    path = f"/households/{hid}/allocation?month=2026-11"
    page = alice.client.get(path)
    assert page.status_code == 200
    # Planned surplus: 30,000 - 3,000 = 27,000.
    assert alice.client.post(path, data={"revision":"1", "emergency_reserve":"5000",
        "savings_goals":"7000", "discretionary":"3000"}).status_code == 302
    assert "₹12,000.00" in alice.client.get(path).get_data(as_text=True)
    assert alice.client.post(path, data={"revision":"2", "emergency_reserve":"20000",
        "savings_goals":"7000", "discretionary":"1"}).status_code == 400
    assert bob.client.get(path).status_code == 404


def test_recurring_candidates_need_three_months_and_confirmation(alice, bob, app):
    hid = alice.household()
    account = alice.account(hid)
    rows = [
        "2026-08-05,StreamFlix monthly,499,debit,purchase,Entertainment & Subscriptions",
        "2026-09-05,StreamFlix monthly,499,debit,purchase,Entertainment & Subscriptions",
        "2026-10-05,StreamFlix monthly,499,debit,purchase,Entertainment & Subscriptions",
        "2026-10-11,One-off shoes,2500,debit,purchase,Shopping & Clothing",
    ]
    import_id = alice.upload(account, csv_text(rows)).get_json()["import"]["id"]
    staged = alice.rows(import_id)
    assert alice.post("/staged/approve", {"ids": [r["id"] for r in staged]}).status_code in (200, 302)
    path = f"/households/{hid}/recurring"
    response = alice.client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "StreamFlix monthly" in html
    assert "One-off shoes" not in html
    from app.households.recurring import recurring_candidates
    with app.app_context():
        candidates, _ = recurring_candidates(alice.user["id"], hid)
    assert len(candidates) == 1
    fingerprint = candidates[0]["fingerprint"]
    assert alice.client.post(f"{path}/{fingerprint}", data={"choice":"confirmed"}).status_code == 302
    assert "Confirmed recurring payments" in alice.client.get(path).get_data(as_text=True)
    with app.app_context():
        saved = db.session.get(RecurringExpense, (hid, fingerprint))
        assert saved.status == "confirmed"
    assert bob.client.get(path).status_code == 404


def test_recurring_confirmation_requires_owner(alice, bob, app):
    from tests.test_authorization import add_member
    hid = alice.household()
    add_member(app, hid, bob.user["id"], "viewer")
    assert bob.client.post(f"/households/{hid}/recurring/{'a'*64}", data={"choice":"confirmed"}).status_code == 403
