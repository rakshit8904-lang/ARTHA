from bs4 import BeautifulSoup

from app.extensions import db
from app.models import MonthlyPlan, SavedGoal
from tests.conftest import Api
from tests.test_authorization import add_member
from tests.test_goals import fields
from app.households.goal_routes import india_today


def household_with(app, alice, bob, carol=None):
    hid = alice.household()
    add_member(app, hid, bob.user["id"], "viewer")
    if carol:
        add_member(app, hid, carol.user["id"], "viewer")
    return hid


def save(api, hid, goal_id=None, **changes):
    path = f"/households/{hid}/goals" + (f"/{goal_id}" if goal_id else "")
    return api.client.post(path, data=fields(**changes))


def test_private_goal_visible_to_creator_and_owners_only(app, alice, bob):
    carol = Api(app, "carol@example.com", "Carol")
    hid = household_with(app, alice, bob, carol)
    res = save(bob, hid, name="Bob's course", visibility="private")
    assert res.status_code == 302
    detail = res.headers["Location"]
    assert bob.client.get(detail).status_code == 200
    assert alice.client.get(detail).status_code == 200
    assert carol.client.get(detail).status_code == 404
    assert "Bob's course" not in carol.client.get(f"/households/{hid}/goals").get_data(as_text=True)
    assert "Private" in BeautifulSoup(alice.client.get(f"/households/{hid}/goals").data, "html.parser").select_one(".goal-card").get_text()
    with app.app_context():
        goal = SavedGoal.query.one()
        assert goal.created_by == bob.user["id"] and goal.visibility == "private"


def test_viewer_cannot_create_or_switch_to_household_goal(app, alice, bob):
    hid = household_with(app, alice, bob)
    assert save(bob, hid, visibility="household").status_code == 403
    detail = save(bob, hid, visibility="private").headers["Location"]
    goal_id = detail.rsplit("/", 1)[1]
    assert save(bob, hid, goal_id, revision="1", name="Renamed", visibility="private").status_code == 302
    assert save(bob, hid, goal_id, revision="2", visibility="household").status_code == 403
    assert save(bob, hid, visibility="").status_code == 400


def test_owner_can_edit_but_not_expose_someone_elses_private_goal(app, alice, bob):
    hid = household_with(app, alice, bob)
    goal_id = save(bob, hid, visibility="private").headers["Location"].rsplit("/", 1)[1]
    assert save(alice, hid, goal_id, revision="1", assigned_minor="9000", visibility="private").status_code == 302
    assert save(alice, hid, goal_id, revision="2", visibility="household").status_code == 403
    page = BeautifulSoup(alice.client.get(f"/households/{hid}/goals/{goal_id}").data, "html.parser")
    assert not page.select("#goal-visibility input[type=radio]")
    with app.app_context():
        goal = db.session.get(SavedGoal, goal_id)
        assert goal.visibility == "private" and goal.inputs["assigned_minor"] == 900000


def test_viewer_cannot_edit_shared_goal_and_sees_no_save_button(app, alice, bob):
    hid = household_with(app, alice, bob)
    detail = save(alice, hid).headers["Location"]
    assert bob.client.post(detail, data=fields(revision="1")).status_code == 403
    assert bob.client.post(detail, data=fields(revision="1", visibility="private")).status_code == 403
    page = BeautifulSoup(bob.client.get(detail).data, "html.parser")
    assert not page.find("button", string="Save goal")


def test_private_goals_excluded_from_household_total(app, alice, bob):
    hid = household_with(app, alice, bob)
    save(alice, hid, assigned_minor="10000")
    save(alice, hid, name="Mine", assigned_minor="3000", visibility="private")
    save(bob, hid, name="Bob's", assigned_minor="2000", visibility="private")
    with app.app_context():
        db.session.add(MonthlyPlan(household_id=hid, month=india_today().strftime("%Y-%m"), plan_type="family",
                                   city="Pune", income=5000000, other_income=0, limits={}, revision=1,
                                   allocation={"savings_goals": 1000000}))
        db.session.commit()
    owner = BeautifulSoup(alice.client.get(f"/households/{hid}/goals").data, "html.parser")
    assert "₹10,000.00 a month" in owner.select_one("#goal-totals").get_text()
    assert "covers this" in owner.select_one("#goal-totals").get_text()
    assert "2, assigned ₹5,000.00" in owner.select_one("#goal-private-total").get_text()
    viewer = BeautifulSoup(bob.client.get(f"/households/{hid}/goals").data, "html.parser")
    assert "1, assigned ₹2,000.00" in viewer.select_one("#goal-private-total").get_text()


def test_goals_saved_before_privacy_stay_household_goals(app, alice):
    hid = alice.household()
    with app.app_context():
        db.session.add(SavedGoal(household_id=hid, name="Old", inputs={"target_minor": 1}))
        db.session.commit()
        assert SavedGoal.query.one().visibility == "household" and SavedGoal.query.one().created_by is None
