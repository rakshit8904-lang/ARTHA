from datetime import date

from app.extensions import db
from app.models import PortfolioHolding, ProfileItem, SavedGoal
from app.ai.tools.household import build_household_context


def test_extended_context_is_minimised_and_preserves_unknown_states(alice):
    household_id = alice.household("AI Context")
    user_id = alice.user["id"]
    with alice.app.app_context():
        db.session.add(SavedGoal(
            household_id=household_id, name="Emergency fund",
            inputs={"purpose": "reserve", "target_month": "2027-12",
                    "target_minor": 5000000, "saved_minor": 100000,
                    "assigned_minor": 20000, "ongoing": [], "loan": None},
            created_by=user_id, visibility="household", revision=1))
        db.session.add(ProfileItem(
            household_id=household_id, section="income", kind="salary", label="Salary",
            state="amount", amount_minor=4500000, frequency="monthly", details={"stability": "steady"},
            created_by=user_id, visibility="household", revision=1))
        db.session.add(ProfileItem(
            household_id=household_id, section="assets", kind="bank", label="Bank balance",
            state="unknown", amount_minor=None, frequency=None, details={"accessible": "unknown"},
            created_by=user_id, visibility="household", revision=1))
        db.session.add(PortfolioHolding(
            household_id=household_id, asset_name="Index fund", asset_type="mutual_fund",
            quantity=1, invested_minor=100000, current_value_minor=110000,
            as_of_date=date(2026, 11, 1), created_by=user_id))
        db.session.commit()
        context = build_household_context(user_id, household_id)

    assert len(context["visible_goals"]) == 1
    assert context["visible_goals"][0]["name"] == "Emergency fund"
    unknown = next(x for x in context["profile_items"] if x["label"] == "Bank balance")
    assert unknown["state"] == "unknown"
    assert unknown["amount_minor"] is None
    assert context["manual_portfolio_holdings"][0]["pricing_basis"] == "manual_user_entered_value"
    assert "id" not in context["visible_goals"][0]
    assert "monthly plan values are omitted" in context["limitations"][-2].lower()


def test_assistant_status_never_returns_api_key(alice, app):
    app.config["OPENAI_API_KEY"] = "test-secret-key-not-for-response"
    app.config["GEMINI_API_KEY"] = "test-gemini-secret"
    response = alice.get("/assistant/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["providers"]["openai"]["configured"] is True
    assert payload["providers"]["gemini"]["configured"] is True
    assert "test-secret-key-not-for-response" not in response.get_data(as_text=True)
    assert "test-gemini-secret" not in response.get_data(as_text=True)


def test_chat_response_identifies_specialist_and_discloses_read_only(alice, monkeypatch):
    import app.api.routes as routes
    monkeypatch.setattr(routes, "assistant_answer", lambda *a, **kw: ("A practical budget answer.", "budget_planner"))
    response = alice.post("/assistant/chat", {
        "provider": "openai",
        "messages": [{"role": "user", "content": "Help me build a monthly budget"}],
    })
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["agent"] == "budget_planner"
    assert payload["agent_label"] == "Budget Planner"
    assert payload["action_approval"]["enabled"] is False
