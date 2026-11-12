from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re

from sqlalchemy.exc import IntegrityError
from flask import Blueprint, redirect, render_template, request, url_for

from app.errors import Conflict, InvalidRequest
from app.extensions import db
from app.households.service import get_household, require_member
from app.ledger.service import spending_aggregation
from app.models import MonthlyPlan
from app.session import require_user

plans = Blueprint("plans", __name__)
GROUPS = {
    "Groceries": ("Milk", "Fruit", "Vegetables", "Other groceries"),
    "Housing/Rent": ("Rent", "Society maintenance", "Housing contribution"),
    "Utilities": ("Electricity", "Wi-Fi", "Phone and communications", "Other utilities"),
    "Transportation & Gas": ("Transport",), "Personal Care": ("Personal maintenance",),
    "Entertainment & Subscriptions": ("Subscriptions",), "Shopping & Clothing": ("Shopping",),
    "Insurance": ("Medical insurance", "Term life insurance"),
    "Education & Children": ("School fees",), "Family support": ("Pledged to parents",),
    "Loan commitments": ("Monthly EMI",), "Other expenses": ("Miscellaneous expenses",),
}


def amount(form, key, required=False):
    raw = form.get(key, "").strip()
    if not raw and not required:
        return 0
    if not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?", raw):
        raise InvalidRequest(f"Enter a nonnegative rupee amount for {key}, with up to two decimal places.")
    return int(Decimal(raw) * 100)


def monthly_actuals(actor_id, household_id, month):
    """Use the ledger's shared accounting rules for monthly category actuals."""
    return spending_aggregation(actor_id, household_id, month)["by_category"]

@plans.route("/households/<household_id>/plan", methods=["GET", "POST"])
def monthly(household_id):
    user = require_user()
    household, role = get_household(user.id, household_id)
    today = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m")
    month = request.args.get("month", today)
    if not re.fullmatch(r"(?:20[0-9]{2}|2100)-(?:0[1-9]|1[0-2])", month):
        raise InvalidRequest("Choose a valid plan month between 2000 and 2100.")
    key = dict(household_id=household_id, month=month)
    plan = db.session.get(MonthlyPlan, (household_id, month))
    if request.method == "POST":
        require_member(user.id, household_id, write=True)
        form = request.form
        kind, city = form.get("plan_type"), form.get("city", "").strip()
        if kind not in ("individual", "family") or not 1 <= len(city) <= 100:
            raise InvalidRequest("Choose individual or family and enter your current city.")
        housing = form.get("housing")
        included = form.get("maintenance_included")
        if housing not in ("owned", "rented", "family"):
            raise InvalidRequest("Choose your housing situation.")
        if housing == "rented" and included not in ("yes", "no"):
            raise InvalidRequest("Specify whether your rent includes maintenance.")
        limits = {item: amount(form, item) for group, items in GROUPS.items()
                  if group != "Housing/Rent" for item in items}
        if housing == "rented":
            limits["Rent"] = amount(form, "Rent", required=True)
        if housing == "owned" or housing == "rented" and included == "no":
            limits["Society maintenance"] = amount(form, "Society maintenance")
        if housing == "family":
            contribution = amount(form, "Housing contribution")
            if contribution > limits["Pledged to parents"]:
                raise InvalidRequest("The housing share cannot exceed the total paid to family.")
            limits["Housing contribution"] = contribution
            limits["Pledged to parents"] -= contribution
        values = dict(plan_type=kind, city=city, income=amount(form, "income", required=True),
                      housing=housing, maintenance_included=(included == "yes") if housing == "rented" else None,
                      other_income=amount(form, "other_income"), limits=limits)
        version = form.get("revision", type=int)
        conflict = "This plan changed. Reopen the saved plan before editing."
        if version == 0:
            db.session.add(MonthlyPlan(**key, **values, revision=1))
        elif not version or not MonthlyPlan.query.filter_by(**key, revision=version).update(dict(**values, revision=version+1)):
            raise Conflict(conflict)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict(conflict) from exc
        return redirect(url_for("plans.monthly", **key))
    budgets = {group: sum(plan.limits.get(i, 0) for i in items) for group, items in GROUPS.items()} if plan else {}
    # A new month starts from the latest earlier plan's answers; nothing is saved until the owner saves.
    prefill = plan or MonthlyPlan.query.filter(MonthlyPlan.household_id == household_id,
                                               MonthlyPlan.month < month).order_by(MonthlyPlan.month.desc()).first()
    return render_template("monthly_plan.html", household=household, role=role, month=month, plan=plan, prefill=prefill,
                           groups=GROUPS, budgets=budgets, actuals=monthly_actuals(user.id, household_id, month),
                           editing=role == "owner" and (not plan or request.args.get("edit") == "1"))


@plans.route("/households/<household_id>/allocation", methods=["GET", "POST"])
def allocation(household_id):
    """Save an editable allocation of planned surplus; never writes ledger transactions."""
    user = require_user()
    household, role = get_household(user.id, household_id)
    month = request.args.get("month") or datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m")
    if not re.fullmatch(r"(?:20[0-9]{2}|2100)-(?:0[1-9]|1[0-2])", month):
        raise InvalidRequest("Choose a valid plan month.")
    plan = db.session.get(MonthlyPlan, (household_id, month))
    if not plan:
        raise InvalidRequest("Create a monthly plan before allocating its surplus.")
    planned_income = plan.income + plan.other_income
    commitments = sum(int(value) for value in plan.limits.values())
    surplus = planned_income - commitments
    if request.method == "POST":
        require_member(user.id, household_id, write=True)
        reserve = amount(request.form, "emergency_reserve")
        goals = amount(request.form, "savings_goals")
        discretionary = amount(request.form, "discretionary")
        total = reserve + goals + discretionary
        if surplus < 0:
            raise InvalidRequest("Your plan has no positive surplus to allocate. Review planned income and commitments first.")
        if total > surplus:
            raise InvalidRequest("Your allocations exceed the planned surplus. Reduce them before saving.")
        revision = request.form.get("revision", type=int)
        saved = {"emergency_reserve": reserve, "savings_goals": goals,
                 "discretionary": discretionary, "unallocated": surplus - total}
        if not revision or not MonthlyPlan.query.filter_by(household_id=household_id, month=month,
                revision=revision).update(dict(allocation=saved, revision=revision + 1)):
            raise Conflict("The monthly plan changed. Reopen this page before saving.")
        db.session.commit()
        return redirect(url_for("plans.allocation", household_id=household_id, month=month))
    current = {key: (plan.allocation or {}).get(key, 0)
               for key in ("emergency_reserve", "savings_goals", "discretionary")}
    current["unallocated"] = surplus - sum(current.values())
    return render_template("allocation.html", household=household, role=role, month=month, plan=plan,
                           surplus=surplus, planned_income=planned_income, commitments=commitments,
                           allocation=current)
