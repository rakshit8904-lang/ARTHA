"""Explicitly requested, permission-filtered household context for AI.

No raw ledger rows are exposed. Private goals/profile entries follow the same visibility
policy as the household UI. Monthly plans are deliberately excluded because blank answers
are currently stored as zero in that subsystem.
"""
from app.households import visibility
from app.households.service import get_household
from app.models import PortfolioHolding, ProfileItem, SavedGoal


_PROFILE_DETAIL_KEYS = {"stability", "accessible", "monthly_payment", "rate",
                        "monthly_deposit", "term_months"}


def build_household_context(user_id, household_id):
    _, role = get_household(user_id, household_id)

    goal_query = visibility.visible(
        SavedGoal.query.filter_by(household_id=household_id), SavedGoal, user_id, role)
    goals = []
    for goal in goal_query.order_by(SavedGoal.updated_at.desc()).limit(50).all():
        values = goal.inputs or {}
        goals.append({
            "name": goal.name,
            "visibility": goal.visibility,
            "purpose": values.get("purpose"),
            "target_month": values.get("target_month"),
            "target_minor": values.get("target_minor"),
            "saved_minor": values.get("saved_minor"),
            "assigned_minor": values.get("assigned_minor"),
            "ongoing": [
                {"label": line.get("label"), "amount_minor": line.get("amount_minor")}
                for line in (values.get("ongoing") or [])[:3] if isinstance(line, dict)
            ],
            "has_loan_comparison": bool(values.get("loan")),
        })

    profile_query = visibility.visible(
        ProfileItem.query.filter_by(household_id=household_id), ProfileItem, user_id, role)
    profile = []
    for item in profile_query.order_by(ProfileItem.updated_at.desc()).limit(75).all():
        details = item.details or {}
        profile.append({
            "section": item.section,
            "kind": item.kind,
            "label": item.label,
            "state": item.state,
            "amount_minor": item.amount_minor if item.state in ("amount", "zero") else None,
            "frequency": item.frequency,
            "date": item.date.isoformat() if item.date else None,
            "details": {k: details[k] for k in _PROFILE_DETAIL_KEYS if k in details},
            "visibility": item.visibility,
        })

    holdings = PortfolioHolding.query.filter_by(household_id=household_id).order_by(
        PortfolioHolding.updated_at.desc()).limit(50).all()
    portfolio = [{
        "asset_name": row.asset_name,
        "asset_type": row.asset_type,
        "invested_minor": row.invested_minor,
        "current_value_minor": row.current_value_minor,
        "valuation_date": row.as_of_date.isoformat(),
        "pricing_basis": "manual_user_entered_value",
    } for row in holdings]

    return {
        "profile_items": profile,
        "visible_goals": goals,
        "manual_portfolio_holdings": portfolio,
        "limitations": [
            "Profile entries retain explicit states; unknown is not zero.",
            "Goals are user-entered plans, not evidence of completed contributions.",
            "Portfolio values are manual and may be stale; no live prices are available.",
            "Monthly plan values are omitted because blank-answer semantics are still being corrected.",
            "No net-worth total is inferred from incomplete profile or portfolio data.",
        ],
    }
