"""Deterministic recurring-payment candidates with explicit household review."""
import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, redirect, render_template, request, url_for, flash

from app.errors import InvalidRequest
from app.extensions import db
from app.households.service import get_household, require_member
from app.models import RecurringExpense, Transaction
from app.session import require_user

recurring = Blueprint("recurring", __name__)


def _key(description, category):
    normalized = re.sub(r"[^a-z0-9 ]", " ", (description or "").casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    # Strip long reference-like numeric tokens, retaining ordinary merchant names.
    normalized = re.sub(r"\b\d{5,}\b", "", normalized).strip()
    return (normalized[:180] or "unknown", category or "")


def recurring_candidates(actor_id, household_id):
    require_member(actor_id, household_id)
    rows = (Transaction.query.filter_by(household_id=household_id, direction="debit")
            .filter(Transaction.transaction_type.in_(("purchase", "fee")))
            .order_by(Transaction.transaction_date.asc()).all())
    grouped = defaultdict(list)
    for row in rows:
        key = _key(row.description, row.category)
        grouped[key].append(row)
    saved = {r.fingerprint: r for r in RecurringExpense.query.filter_by(household_id=household_id).all()}
    candidates, confirmed = [], []
    for (description, category), items in grouped.items():
        months = sorted({item.transaction_date.strftime("%Y-%m") for item in items})
        if len(months) < 3:
            continue
        amounts = sorted(item.amount_minor for item in items)
        median = amounts[len(amounts) // 2]
        if median <= 0 or any(abs(value - median) / median > 0.15 for value in amounts):
            continue
        fingerprint = hashlib.sha256((description + "|" + category).encode("utf-8")).hexdigest()
        record = saved.get(fingerprint)
        item = {"fingerprint": fingerprint, "description": items[-1].description,
                "category": category or "Unclassified", "typical_amount_minor": median,
                "occurrences": len(items), "months": months, "status": record.status if record else "candidate"}
        if record and record.status == "confirmed":
            confirmed.append(item)
        elif not record:
            candidates.append(item)
    return candidates, confirmed


@recurring.get("/households/<household_id>/recurring")
def index(household_id):
    user = require_user()
    household, role = get_household(user.id, household_id)
    candidates, confirmed = recurring_candidates(user.id, household_id)
    return render_template("recurring.html", household=household, role=role,
                           candidates=candidates, confirmed=confirmed)


@recurring.post("/households/<household_id>/recurring/<fingerprint>")
def decide(household_id, fingerprint):
    user = require_user()
    require_member(user.id, household_id, write=True)
    choice = request.form.get("choice")
    if choice not in ("confirmed", "dismissed") or not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
        raise InvalidRequest("Invalid recurring-payment review decision.")
    candidates, confirmed = recurring_candidates(user.id, household_id)
    candidate = next((item for item in candidates if item["fingerprint"] == fingerprint), None)
    existing = db.session.get(RecurringExpense, (household_id, fingerprint))
    if not candidate and not existing:
        raise InvalidRequest("This recurring-payment candidate is no longer available.")
    if candidate:
        description, category = candidate["description"], (candidate["category"] if candidate["category"] != "Unclassified" else None)
        amount = candidate["typical_amount_minor"]
    else:
        description, category, amount = existing.description, existing.category, existing.typical_amount_minor
    if existing is None:
        existing = RecurringExpense(household_id=household_id, fingerprint=fingerprint,
                                    description=description, category=category,
                                    typical_amount_minor=amount, status=choice, confirmed_by=user.id,
                                    updated_at=datetime.now(timezone.utc))
        db.session.add(existing)
    else:
        existing.status, existing.confirmed_by = choice, user.id
        existing.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Recurring payment confirmed." if choice == "confirmed" else "Candidate dismissed.", "ok")
    return redirect(url_for("recurring.index", household_id=household_id))
