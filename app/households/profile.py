"""Ongoing financial profile: section definitions and deterministic summaries. Money is INR paise.

Every item has an explicit answer state, so a blank is never read as zero.
Nothing here changes the monthly plan, goals or ledger.
"""
from decimal import Decimal, ROUND_HALF_UP

STATES = {"amount": "Amount known", "zero": "Zero", "not_applicable": "Doesn't apply", "unknown": "Don't know yet"}
FREQUENCIES = {"monthly": ("Monthly", 1), "quarterly": ("Every 3 months", 3), "half_yearly": ("Every 6 months", 6),
               "yearly": ("Yearly", 12), "one_time": ("One time", None)}
NONE_KIND = "_none"

SECTIONS = {
    "income": {
        "title": "Income", "amount": "Amount each time it is paid", "frequency": True, "date": None,
        "intro": "Take-home income sources. For a family profile, include each earner's income you want to plan with.",
        "kinds": {"salary": "Salary", "business": "Business or freelance", "rental": "Rental income",
                  "family": "Support received from family", "other": "Other income"},
        "extra": {"stability": ("choice", "How steady is it?", {"steady": "Steady", "varies": "Varies month to month",
                                                                  "uncertain": "Uncertain", "unknown": "Not sure"})}},
    "assets": {
        "title": "Assets", "amount": "Current value", "frequency": False, "date": "Value checked on",
        "intro": "What you own. Values are your own estimates on the date you give.",
        "kinds": {"bank": "Bank account", "cash": "Cash", "fixed_deposit": "Fixed deposit", "mutual_funds": "Mutual funds",
                  "stocks": "Shares", "gold": "Gold", "property": "Property", "vehicle": "Vehicle", "other": "Other asset"},
        "extra": {"accessible": ("choice", "Could you use this money within about a week?",
                                 {"yes": "Yes", "no": "No", "unknown": "Not sure"})}},
    "liabilities": {
        "title": "Loans and debts", "amount": "Amount still owed", "frequency": False, "date": "Balance checked on",
        "intro": "What you owe. Interest rates are the ones you enter; they are not checked against lenders.",
        "kinds": {"home_loan": "Home loan", "education_loan": "Education loan", "vehicle_loan": "Vehicle loan",
                  "personal_loan": "Personal loan", "credit_card": "Credit card balance", "family_loan": "Loan from family or friends",
                  "other": "Other debt"},
        "extra": {"monthly_payment": ("money", "Monthly payment (EMI)", None),
                  "rate": ("rate", "Yearly interest rate (%)", None)}},
    "bills": {
        "title": "Periodic bills", "amount": "Amount each time", "frequency": True, "date": "Next due date",
        "intro": "Bills that are not paid every month, or that you want tracked with their real schedule, such as school fees or insurance premiums.",
        "kinds": {"school_fees": "School or college fees", "medical_insurance": "Medical insurance premium",
                  "term_insurance": "Term life insurance premium", "vehicle_insurance": "Vehicle insurance",
                  "property_tax": "Property tax", "subscription": "Subscription", "other": "Other bill"},
        "extra": {}},
    "savings": {
        "title": "Savings: deposits and reserve", "amount": "Amount saved so far", "frequency": False, "date": "Checked on",
        "intro": "Recurring deposits and the rainy-day reserve you have actually set aside.",
        "kinds": {"recurring_deposit": "Recurring deposit", "reserve": "Rainy-day reserve", "other": "Other savings"},
        "extra": {"monthly_deposit": ("money", "Monthly deposit", None), "term_months": ("months", "Term in months", None),
                  "rate": ("rate", "Yearly interest rate (%)", None)}},
}


def monthly_equivalent(amount_minor, frequency):
    """Spread a periodic amount evenly per month for planning; one-time amounts have none."""
    months = FREQUENCIES.get(frequency, (None, None))[1]
    if amount_minor is None or months is None:
        return None
    return int((Decimal(amount_minor) / months).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def summarize(section, items):
    """Totals over known amounts, with counts of unknown answers so partial totals are labelled."""
    real = [i for i in items if i.kind != NONE_KIND]
    known = [i for i in real if i.state == "amount"]
    out = {"count": len(real), "unknown": sum(i.state == "unknown" for i in real),
           "none": any(i.kind == NONE_KIND for i in items) and not real,
           "total_minor": sum(i.amount_minor for i in known)}
    if SECTIONS[section]["frequency"]:
        monthly = [monthly_equivalent(i.amount_minor, i.frequency) for i in known]
        out["monthly_minor"] = sum(m for m in monthly if m is not None)
        out["one_time"] = sum(m is None for m in monthly)
    if section == "assets":
        out["accessible_minor"] = sum(i.amount_minor for i in known if (i.details or {}).get("accessible") == "yes")
    if section == "liabilities":
        out["payments_minor"] = sum((i.details or {}).get("monthly_payment") or 0 for i in real)
    if section == "savings":
        out["deposits_minor"] = sum((i.details or {}).get("monthly_deposit") or 0 for i in real)
        out["reserve_minor"] = sum(i.amount_minor for i in known if i.kind == "reserve")
    if section == "bills":
        out["upcoming"] = sorted((i for i in real if i.date), key=lambda i: i.date)[:3]
    return out
