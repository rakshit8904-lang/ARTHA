"""Saved household goals with a deadline-first plan; never update budgets or transactions."""
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.errors import NotFound
from app.extensions import db
from app.households.calculations import rupees_to_paise
from app.households.goals import ONGOING_LINES, PURPOSES, calculate_goal
from app.households import visibility as vis
from app.households.service import get_household
from app.models import MonthlyPlan, SavedGoal, utcnow
from app.session import require_user

goals = Blueprint("goals", __name__)
GOAL = {"target_minor": "Target amount", "saved_minor": "Money already set aside",
        "assigned_minor": "Monthly amount you assign"}
LOAN = {"loan_minor": "Loan amount", "fees_minor": "One-time loan fees"}
MONTH_RE = r"(?:20[0-9]{2}|2100)-(?:0[1-9]|1[0-2])"


def india_today():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def rupees(paise):
    return "" if paise is None else f"{paise // 100}.{paise % 100:02d}"


def money_field(values, key, label, optional=False):
    text = (values.get(key) or "").strip()
    if optional and not text:
        return None
    try:
        return rupees_to_paise(text)
    except ValueError as exc:
        raise ValueError(f"{label}: {exc}") from None


def parse_inputs(values):
    inputs = {key: money_field(values, key, label) for key, label in GOAL.items()}
    if not re.fullmatch(MONTH_RE, values.get("target_month", "")):
        raise ValueError("Choose a target month.")
    inputs["target_month"] = values["target_month"]
    try:
        as_of = date.fromisoformat(values.get("saved_as_of", ""))
    except ValueError:
        raise ValueError("Enter the date your set-aside amount was last checked.") from None
    if as_of > india_today():
        raise ValueError("The set-aside date cannot be in the future.")
    inputs["saved_as_of"] = as_of.isoformat()
    if values.get("purpose") not in PURPOSES:
        raise ValueError("Choose what the goal is for.")
    inputs["purpose"] = values["purpose"]
    inputs["ongoing"] = []
    for i in range(1, ONGOING_LINES + 1):
        label = (values.get(f"ongoing_label_{i}") or "").strip()
        has_amount = bool((values.get(f"ongoing_amount_{i}") or "").strip())
        if not label and not has_amount:
            continue
        if not 1 <= len(label) <= 60:
            raise ValueError(f"Ongoing cost {i}: give it a name of up to 60 characters.")
        inputs["ongoing"].append({"label": label, "amount_minor": money_field(values, f"ongoing_amount_{i}", label, optional=True)})
    loan_keys = ("loan_minor", "rate", "term_months", "fees_minor")
    filled = [key for key in loan_keys if (values.get(key) or "").strip()]
    if filled and len(filled) < len(loan_keys):
        raise ValueError("Fill in every loan field (use 0 for no fees), or leave them all blank.")
    inputs["loan"] = None
    if filled:
        rate, term = values["rate"].strip(), values["term_months"].strip()
        if not re.fullmatch(r"[0-9]{1,2}(?:\.[0-9]{1,2})?", rate) or Decimal(rate) > 50:
            raise ValueError("Enter the yearly interest rate as a percentage from 0 to 50, with up to two decimals.")
        if not re.fullmatch(r"[0-9]{1,3}", term) or not 1 <= int(term) <= 360:
            raise ValueError("Enter the loan term as a whole number of months from 1 to 360.")
        inputs["loan"] = {**{key: money_field(values, key, label) for key, label in LOAN.items()},
                          "rate": rate, "term_months": int(term)}
    return inputs


def evaluate(inputs):
    return calculate_goal(target_minor=inputs["target_minor"], saved_minor=inputs["saved_minor"],
                          assigned_minor=inputs["assigned_minor"], target_month=inputs["target_month"],
                          current_month=india_today().strftime("%Y-%m"), ongoing=inputs.get("ongoing"), loan=inputs.get("loan"))


def form_values(goal):
    inputs = goal.inputs
    values = {"name": goal.name, "revision": str(goal.revision), "visibility": goal.visibility, "target_month": inputs["target_month"],
              "saved_as_of": inputs["saved_as_of"], **{key: rupees(inputs[key]) for key in GOAL},
              "purpose": inputs.get("purpose", "")}
    for i, line in enumerate(inputs.get("ongoing") or [], 1):
        values[f"ongoing_label_{i}"], values[f"ongoing_amount_{i}"] = line["label"], rupees(line["amount_minor"])
    loan = inputs.get("loan")
    if loan:
        values.update({key: rupees(loan[key]) for key in LOAN}, rate=loan["rate"], term_months=str(loan["term_months"]))
    return values


def overview(household_id, saved):
    """Each goal's current plan, plus total assigned versus this month's saved goal allocation."""
    rows = []
    for goal in saved:
        try:
            rows.append((goal, evaluate(goal.inputs), None))
        except ValueError as exc:
            rows.append((goal, None, str(exc)))
    month = india_today().strftime("%Y-%m")
    plan = db.session.get(MonthlyPlan, (household_id, month))
    allocated = (plan.allocation or {}).get("savings_goals") if plan and plan.allocation else None
    # Private goals are never part of the household total compared with the household allocation.
    shared = [g for g in saved if g.visibility == vis.HOUSEHOLD]
    private = [g for g in saved if g.visibility == vis.PRIVATE]
    return rows, {"month": month, "assigned_minor": sum(g.inputs["assigned_minor"] for g in shared),
                  "private_minor": sum(g.inputs["assigned_minor"] for g in private), "private_count": len(private),
                  "allocated_minor": allocated}


@goals.route("/households/<household_id>/goals", methods=["GET", "POST"])
@goals.route("/households/<household_id>/goals/<goal_id>", methods=["GET", "POST"])
def index(household_id, goal_id=None):
    user = require_user()
    household, role = get_household(user.id, household_id)
    goal = None
    if goal_id:
        goal = vis.visible(SavedGoal.query.filter_by(id=goal_id, household_id=household_id),
                           SavedGoal, user.id, role).first()
        if goal is None:
            raise NotFound("Goal not found")
    error, result, status = None, None, 200
    values = form_values(goal) if goal else {"revision": "0", "saved_as_of": india_today().isoformat(),
                                              "visibility": vis.HOUSEHOLD if role == "owner" else vis.PRIVATE}
    if goal:
        try:
            result = evaluate(goal.inputs)
        except ValueError as exc:
            error = str(exc)
    if request.method == "POST":
        values, result = request.form.to_dict(), None
        action = values.get("action")
        try:
            if action not in ("calculate", "save"):
                raise ValueError("Choose Calculate or Save goal.")
            if action == "save":
                vis.check_write(goal, values.get("visibility"), user.id, role)
            inputs = parse_inputs(values)
            result = evaluate(inputs)
            if action == "save":
                name = values.get("name", "").strip()
                if not 1 <= len(name) <= 100:
                    raise ValueError("Name the goal using 1 to 100 characters.")
                data = dict(name=name, inputs=inputs, visibility=values["visibility"], updated_at=utcnow())
                if goal:
                    version = request.form.get("revision", type=int)
                    changed = SavedGoal.query.filter_by(id=goal.id, household_id=household_id, revision=version).update(
                        dict(**data, revision=SavedGoal.revision + 1)) if version else 0
                    if not changed:
                        db.session.rollback()
                        error, status = "This goal changed in another tab. Reopen it before saving; your inputs below have not been saved.", 409
                else:
                    goal = SavedGoal(household_id=household_id, created_by=user.id, **data)
                    db.session.add(goal)
                if status == 200:
                    db.session.commit()
                    flash("Goal saved. Your monthly plan and ledger are unchanged.", "ok")
                    return redirect(url_for("goals.index", household_id=household_id, goal_id=goal.id))
        except ValueError as exc:
            error, status, result = str(exc), 400, None
    saved = vis.visible(SavedGoal.query.filter_by(household_id=household_id), SavedGoal, user.id, role
                        ).order_by(SavedGoal.updated_at.desc()).all()
    rows, totals = overview(household_id, saved)
    return render_template("goals.html", household=household, role=role, goal=goal, rows=rows, totals=totals,
                           values=values, result=result, error=error, goal_fields=GOAL, purposes=PURPOSES, ongoing_lines=ONGOING_LINES,
                           loan_fields=LOAN, choices=vis.CHOICES, user_id=user.id,
                           can_save=vis.can_edit(goal, user.id, role) if goal else True), status
