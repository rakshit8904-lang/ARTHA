from app.ai.agents.registry import AGENTS, select_agent
from app.ai.tools.finance import build_financial_insights, paise_to_rupees


def test_specialist_routing_is_deterministic():
    assert select_agent("Where is my money going?") == "financial_analyst"
    assert select_agent("Help me make a monthly budget") == "budget_planner"
    assert select_agent("I need to save for a car by next year") == "goal_planner"
    assert select_agent("Can I afford moving to Bengaluru?") == "relocation_advisor"
    assert select_agent("Explain SIP and mutual fund risk") == "investment_educator"
    assert select_agent("Hello Artha") == "financial_companion"


def test_agent_registry_has_six_specialists():
    assert len(AGENTS) == 6
    assert all(spec.get("instructions") and spec.get("label") for spec in AGENTS.values())


def test_financial_insights_convert_paise_without_filling_missing_values():
    assert paise_to_rupees(12345) == "123.45"
    insights = build_financial_insights({
        "income_minor": 1000000,
        "confirmed_spending_minor": 350000,
        "coverage_status": "partial",
    })
    assert insights["net_after_confirmed_spending_inr"] == "6500.00"
    assert insights["confirmed_spending_to_income_ratio"] == 0.35
    assert insights["coverage_status"] == "partial"
    assert build_financial_insights({
        "income_minor": None, "confirmed_spending_minor": 200
    }) == {"availability": "partial", "reason": "Income or spending is not fully available."}
