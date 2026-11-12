from bs4 import BeautifulSoup

from app.extensions import db
from app.models import MonthlyPlan
from tests.test_authorization import add_member
from tests.test_planning_tools import _plan


def form(alice, hid, month):
    return BeautifulSoup(alice.client.get(f"/households/{hid}/plan?month={month}").data, "html.parser")


def test_new_month_starts_from_latest_earlier_plan_without_saving(app, alice):
    hid = alice.household()
    assert _plan(alice, hid).status_code == 302  # 2026-11
    page = form(alice, hid, "2026-12")
    assert "Started from your 2026-11 plan" in page.select_one("#plan-prefill").get_text()
    assert page.select_one("input[name=city]")["value"] == "Pune"
    assert page.select_one("input[name='Monthly EMI']")["value"] == "2000.00"
    assert page.select_one("input[name=revision]")["value"] == "0"
    with app.app_context():
        assert db.session.get(MonthlyPlan, (hid, "2026-12")) is None


def test_saved_month_and_earlier_months_are_not_prefilled(alice):
    hid = alice.household()
    _plan(alice, hid)
    assert form(alice, hid, "2026-10").select_one("input[name=city]")["value"] == ""
    assert not form(alice, hid, "2026-10").select_one("#plan-prefill")
    saved = BeautifulSoup(alice.client.get(f"/households/{hid}/plan?month=2026-11&edit=1").data, "html.parser")
    assert not saved.select_one("#plan-prefill") and saved.select_one("input[name=city]")["value"] == "Pune"


def test_prefill_stays_within_household(app, alice, bob):
    _plan(alice, alice.household())
    other = bob.household()
    assert bob.client.get(f"/households/{other}/plan?month=2026-12").data.count(b"Pune") == 0


def test_household_page_groups_every_tool(app, alice):
    hid = alice.household()
    page = BeautifulSoup(alice.client.get(f"/households/{hid}").data, "html.parser")
    sections = {s.h2.get_text(): len(s.select("a")) for s in page.select(".household-sections section")}
    assert sections == {"Understand your spending": 6, "Plan your month": 4, "Decide and track": 5, "Learn": 1}
