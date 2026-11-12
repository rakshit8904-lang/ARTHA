"""Read-only household calculators for reserve planning and recurring deposits."""

from flask import Blueprint, render_template, request

from app.households.calculations import emergency_reserve, recurring_deposit, savings_goal, rupees_to_paise
from app.households.service import get_household
from app.session import require_user

calculators = Blueprint("calculators", __name__)


@calculators.route("/households/<household_id>/calculators", methods=["GET", "POST"])
def index(household_id):
    user = require_user()
    household, role = get_household(user.id, household_id)
    reserve_result = None
    rd_result = None
    goal_result = None
    error = None
    values = dict(request.form) if request.method == "POST" else {}

    if request.method == "POST":
        try:
            calculator = request.form.get("calculator")
            if calculator == "reserve":
                reserve_result = emergency_reserve(
                    rupees_to_paise(request.form.get("essential_monthly_expenses", "")),
                    int(request.form.get("target_months", "")),
                    rupees_to_paise(request.form.get("current_reserve", "")),
                    rupees_to_paise(request.form.get("monthly_contribution", "")),
                )
            elif calculator == "goal":
                goal_result = savings_goal(
                    rupees_to_paise(request.form.get("goal_amount", "")),
                    rupees_to_paise(request.form.get("current_saved", "")),
                    rupees_to_paise(request.form.get("goal_monthly_contribution", "")),
                )
            elif calculator == "rd":
                rd_result = recurring_deposit(
                    rupees_to_paise(request.form.get("monthly_deposit", "")),
                    int(request.form.get("duration_months", "")),
                    request.form.get("annual_rate", ""),
                    request.form.get("compounding", "quarterly"),
                    request.form.get("deposit_timing", "end"),
                )
            else:
                raise ValueError("Choose a calculator to run.")
        except (ValueError, TypeError) as exc:
            error = str(exc) or "Check the values and try again."

    return render_template("calculators.html", household=household, role=role,
                           reserve_result=reserve_result, rd_result=rd_result, goal_result=goal_result,
                           error=error, values=values)
