"""Create one fictional demo household for rehearsals. All names, amounts and merchants are invented.

Usage (from Artha_AI_privacy, with the demo server's DATABASE_URL and APP_ENV=development set):
    .venv/Scripts/python.exe scripts/seed_demo_household.py --owner-email someone@example.invalid

The owner must already have an account. The script refuses to run twice for the same household
name and never touches other households. Back up the database first.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.households.accounts import create_account  # noqa: E402
from app.households.plans import GROUPS  # noqa: E402
from app.households.service import create_household  # noqa: E402
from app.imports.review import approve_staged, edit_staged  # noqa: E402
from app.imports.service import create_import  # noqa: E402
from app.models import (Household, HouseholdMembership, MonthlyPlan, PortfolioHolding, ProfileItem,  # noqa: E402
                        SavedGoal, StagedTransaction, User)

NAME = "Asha's household (fictional demo)"
STATEMENT = """date,description,amount,direction,type,category
2026-11-01,Salary NORTHWIND LABS,52000.00,credit,income,
2026-11-02,Rent transfer to landlord,14000.00,debit,purchase,Housing/Rent
2026-11-03,FreshBasket groceries,2350.00,debit,purchase,Groceries
2026-11-04,Milk subscription DailyDairy,900.00,debit,purchase,Groceries
2026-11-05,City Power electricity bill,1180.00,debit,purchase,Utilities
2026-11-06,Metro card recharge,600.00,debit,purchase,Transportation & Gas
2026-11-07,StreamBox monthly plan,199.00,debit,purchase,Entertainment & Subscriptions
2026-11-08,Cafe Lumen dinner,840.00,debit,purchase,Eating Out
2026-11-09,ThreadCo shirt,1499.00,debit,purchase,Shopping & Clothing
2026-11-10,Recurring deposit instalment,2000.00,debit,investment,
2026-11-11,ThreadCo refund,1499.00,credit,refund,
2026-11-12,UPI to R Kumar,1500.00,debit,,
"""
PLAN = {"Milk": 900, "Fruit": 800, "Vegetables": 1500, "Other groceries": 2500, "Rent": 14000,
        "Electricity": 1200, "Wi-Fi": 700, "Phone and communications": 400, "Transport": 1500,
        "Personal maintenance": 800, "Subscriptions": 400, "Shopping": 2000, "Medical insurance": 600,
        "Pledged to parents": 5000, "Miscellaneous expenses": 1000}


def paise(rupees):
    return int(rupees * 100)


def seed(owner_email):
    owner = User.query.filter_by(email=owner_email).one_or_none()
    if owner is None:
        sys.exit(f"No account for {owner_email}. Create it in the app first.")
    exists = (Household.query.join(HouseholdMembership, HouseholdMembership.household_id == Household.id)
              .filter(HouseholdMembership.user_id == owner.id, Household.name == NAME).first())
    if exists:
        sys.exit("The demo household already exists for this account; nothing changed.")
    uid = owner.id
    hid = create_household(uid, NAME).id
    acc = create_account(uid, hid, "Salary account", "savings", "Example Bank (fictional)").id

    imp, _ = create_import(uid, acc, "asha_november_2026.csv", STATEMENT.encode())
    rows = {r.original_description: r.id for r in StagedTransaction.query.filter_by(import_id=imp.id)}
    refund, unclear = rows.pop("ThreadCo refund"), rows.pop("UPI to R Kumar")
    results = approve_staged(uid, list(rows.values()))
    assert all(r["ok"] for r in results), results
    shirt = next(r["transaction_id"] for d, r in zip(rows, results) if d == "ThreadCo shirt")
    edit_staged(uid, refund, {"matched_transaction_id": shirt})
    assert approve_staged(uid, [refund])[0]["ok"]
    assert approve_staged(uid, [unclear], review_later=True)[0]["ok"]  # shown as an unresolved entry

    limits = {item: paise(PLAN.get(item, 0)) for group, items in GROUPS.items() for item in items
              if item not in ("Society maintenance", "Housing contribution")}
    income, commitments = paise(52000), sum(limits.values())
    surplus = income - commitments
    for month in ("2026-10", "2026-11"):
        allocation = {"emergency_reserve": paise(4000), "savings_goals": paise(6000), "discretionary": paise(2000)}
        allocation["unallocated"] = surplus - sum(allocation.values())
        db.session.add(MonthlyPlan(household_id=hid, month=month, plan_type="individual", city="Pune", housing="rented",
                                   maintenance_included=True, income=income, other_income=0, limits=limits,
                                   revision=1, allocation=allocation))

    goal = lambda name, purpose, target, saved, assigned, month, ongoing=(), loan=None, visibility="household": SavedGoal(
        household_id=hid, name=name, created_by=uid, visibility=visibility,
        inputs={"target_minor": paise(target), "saved_minor": paise(saved), "assigned_minor": paise(assigned),
                "target_month": month, "saved_as_of": "2026-11-10", "purpose": purpose, "loan": loan,
                "ongoing": [{"label": l, "amount_minor": None if a is None else paise(a)} for l, a in ongoing]})
    db.session.add_all([
        goal("Data science course", "education", 120000, 20000, 4000, "2028-06", [("Course materials", 500)]),
        goal("Rainy-day fund top-up", "reserve", 90000, 30000, 2000, "2027-12"),
        goal("Scooter", "purchase", 95000, 10000, 2500, "2028-03", [("Fuel", 800), ("Insurance (monthly share)", None)],
             {"loan_minor": paise(60000), "rate": "10.5", "term_months": 24, "fees_minor": paise(1500)}),
        goal("Surprise trip for parents", "travel", 40000, 0, 1000, "2027-10", visibility="private")])

    item = lambda section, kind, label, state, amount=None, frequency=None, when=None, details=None, visibility="household": ProfileItem(
        household_id=hid, section=section, kind=kind, label=label, state=state, created_by=uid, visibility=visibility,
        amount_minor=None if amount is None else paise(amount), frequency=frequency, date=when, details=details or {})
    db.session.add_all([
        item("income", "salary", "Northwind Labs", "amount", 52000, "monthly", details={"stability": "steady"}),
        item("income", "business", "Weekend tutoring", "unknown", details={"stability": "varies"}),
        item("assets", "bank", "Salary account", "amount", 68000, when=date(2026, 11, 10), details={"accessible": "yes"}),
        item("assets", "gold", "Gift from family", "unknown", details={"accessible": "no"}),
        item("liabilities", "education_loan", "Graduation loan", "amount", 240000, when=date(2026, 11, 1),
             details={"monthly_payment": paise(5200), "rate": "9.25"}),
        item("bills", "medical_insurance", "Family floater", "amount", 7200, "yearly", date(2027, 2, 15)),
        item("bills", "subscription", "Cloud storage", "amount", 1300, "yearly", date(2027, 6, 1)),
        item("savings", "recurring_deposit", "Example Bank RD", "amount", 12000, when=date(2026, 11, 10),
             details={"monthly_deposit": paise(2000), "term_months": 24, "rate": "7"}),
        item("savings", "reserve", "Emergency savings", "amount", 30000, when=date(2026, 11, 10))])

    db.session.add(PortfolioHolding(household_id=hid, asset_name="Index fund (fictional)", asset_type="mutual_fund",
                                    quantity=120, invested_minor=paise(18000), current_value_minor=paise(19250),
                                    as_of_date=date(2026, 11, 8), notes="Demo values only", created_by=uid))
    db.session.commit()
    print(f"Created '{NAME}' with an approved November statement, two monthly plans, four goals, "
          "nine profile entries and one holding.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner-email", required=True)
    args = parser.parse_args()
    app = create_app({"TESTING": True})  # TESTING only skips the background cleanup thread
    with app.app_context():
        seed(args.owner_email)
