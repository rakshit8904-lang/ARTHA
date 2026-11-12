"""User-reviewed, saved relocation estimates; never update budgets or transactions."""
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.cities.affordability import CityDataError, search_cities
from app.errors import NotFound
from app.extensions import db
from app.households.calculations import rupees_to_paise
from app.households.relocation import calculate_relocation
from app.households.service import get_household, require_member
from app.models import RelocationScenario, utcnow
from app.session import require_user

relocation = Blueprint("relocation", __name__)
MONTHLY = {"rent_minor": "Rent", "utilities_minor": "Utilities and maintenance",
           "food_minor": "Groceries and food", "transport_minor": "Transport",
           "other_minor": "Other monthly costs, including commitments"}
UPFRONT = {"moving_cost_minor": "Moving costs", "setup_cost_minor": "Setup costs"}
MONEY = {"monthly_income_minor": "Monthly take-home income", **MONTHLY, **UPFRONT}


def rupees(paise):
    return f"{paise // 100}.{paise % 100:02d}"


@relocation.route("/households/<household_id>/relocation", methods=["GET", "POST"])
@relocation.route("/households/<household_id>/relocation/<scenario_id>", methods=["GET", "POST"])
def index(household_id, scenario_id=None):
    user = require_user()
    household, role = get_household(user.id, household_id)
    scenario = None
    if scenario_id:
        scenario = RelocationScenario.query.filter_by(id=scenario_id, household_id=household_id).first()
        if scenario is None:
            raise NotFound("Relocation scenario not found")
    saved = RelocationScenario.query.filter_by(household_id=household_id).order_by(RelocationScenario.updated_at.desc()).all()
    error, result, inputs, status = None, None, None, 200
    try:
        cities = sorted(search_cities(), key=lambda item: item["city"].casefold())
    except CityDataError as exc:
        cities, error = [], str(exc)
    city_key = request.form.get("city", "") if request.method == "POST" else request.args.get("city", scenario.city_key if scenario else "")
    city = next((item for item in cities if item["city_key"] == city_key), None)
    values = {"name": scenario.name if scenario else "", "revision": str(scenario.revision if scenario else 0)}
    reset = request.args.get("reset") == "1" or "city" in request.args
    if scenario and not reset:
        inputs = dict(scenario.inputs)
        values.update({key: rupees(inputs[key]) for key in MONEY})
        values["deposit_months"] = str(inputs["deposit_months"])
        result = calculate_relocation(**inputs)
    elif city:
        values["rent_minor"] = rupees(city["rent_paise"])
    if request.method == "POST":
        values = request.form.to_dict()
        result = None
        action = values.get("action")
        if action == "save":
            require_member(user.id, household_id, write=True)
        try:
            if action not in ("calculate", "save"):
                raise ValueError("Choose Calculate or Save scenario.")
            if city is None:
                raise ValueError("Choose a city from the dataset before calculating.")
            inputs = {}
            for key, label in MONEY.items():
                try:
                    inputs[key] = rupees_to_paise(values.get(key, ""))
                except ValueError as exc:
                    raise ValueError(f"{label}: {exc}") from None
            months = values.get("deposit_months", "")
            if not re.fullmatch(r"[0-9]{1,2}", months):
                raise ValueError("Enter deposit months as a whole number from 0 to 24.")
            inputs["deposit_months"] = int(months)
            result = calculate_relocation(**inputs)
            if action == "save":
                name = values.get("name", "").strip()
                if not 1 <= len(name) <= 100:
                    raise ValueError("Name the scenario using 1 to 100 characters.")
                data = dict(name=name, city_key=city_key, inputs=inputs, updated_at=utcnow())
                if scenario:
                    version = request.form.get("revision", type=int)
                    changed = RelocationScenario.query.filter_by(id=scenario.id, household_id=household_id,
                                revision=version).update(dict(**data, revision=RelocationScenario.revision + 1)) if version else 0
                    if not changed:
                        db.session.rollback()
                        error, status = "This scenario changed in another tab. Reopen it before saving; your inputs below have not been saved.", 409
                else:
                    scenario = RelocationScenario(household_id=household_id, **data)
                    db.session.add(scenario)
                if status == 200:
                    db.session.commit()
                    flash("Relocation scenario saved. Your monthly budget and ledger are unchanged.", "ok")
                    return redirect(url_for("relocation.index", household_id=household_id, scenario_id=scenario.id))
        except ValueError as exc:
            error, status, result = str(exc), 400, None
    return render_template("relocation.html", household=household, role=role, scenario=scenario,
        saved=saved, cities=cities, city=city, values=values, result=result, inputs=inputs,
        error=error, monthly=MONTHLY, upfront=UPFRONT), status
