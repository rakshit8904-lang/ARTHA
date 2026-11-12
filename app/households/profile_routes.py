"""Financial profile screens: an overview plus one form per section, each saved on its own."""
import re
from datetime import date
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.errors import AppError, Conflict, NotFound
from app.extensions import db
from app.households import visibility as vis
from app.households.calculations import rupees_to_paise
from app.households.goal_routes import india_today, rupees
from app.households.profile import FREQUENCIES, NONE_KIND, SECTIONS, STATES, monthly_equivalent, summarize
from app.households.service import get_household
from app.models import ProfileItem, utcnow
from app.session import require_user

profile = Blueprint("profile", __name__)
NEW_ROWS = 3
MAX_ROWS = 60


def section_items(household_id, section, user_id, role):
    query = ProfileItem.query.filter_by(household_id=household_id, section=section)
    return vis.visible(query, ProfileItem, user_id, role).order_by(ProfileItem.kind, ProfileItem.label).all()


def item_values(item):
    return {"id": item.id, "revision": str(item.revision), "created_by": item.created_by, "kind": item.kind, "label": item.label, "state": item.state,
            "amount": rupees(item.amount_minor), "frequency": item.frequency or "",
            "date": item.date.isoformat() if item.date else "", "visibility": item.visibility,
            "x": {k: (rupees(v) if isinstance(v, int) and k in ("monthly_payment", "monthly_deposit") else str(v))
                  for k, v in (item.details or {}).items() if v is not None}}


def form_values(form, n):
    get = lambda key: (form.get(f"{n}-{key}") or "").strip()
    return {"id": get("id"), "revision": get("revision"), "kind": get("kind"), "label": get("label"), "state": get("state"),
            "amount": get("amount"), "frequency": get("frequency"), "date": get("date"), "visibility": get("visibility"),
            "remove": get("remove") == "1", "x": {k[len(f"{n}-x-"):]: v.strip() for k, v in form.items() if k.startswith(f"{n}-x-")}}


def parse_row(cfg, row):
    """Validate one posted row; returns column values. Raises ValueError with a readable message."""
    if row["kind"] not in cfg["kinds"]:
        raise ValueError("choose what it is.")
    if row["state"] not in STATES:
        raise ValueError("choose whether the amount is known, zero, doesn't apply or unknown.")
    if len(row["label"]) > 100:
        raise ValueError("keep the name to 100 characters.")
    amount = None
    if row["state"] == "amount":
        amount = rupees_to_paise(row["amount"]) if row["amount"] else 0
        if amount <= 0:
            raise ValueError("enter an amount above zero, or choose Zero.")
    elif row["amount"]:
        raise ValueError("clear the amount, or choose 'Amount known'.")
    frequency = None
    if cfg["frequency"] and row["state"] == "amount":
        if row["frequency"] not in FREQUENCIES:
            raise ValueError("choose how often it is paid.")
        frequency = row["frequency"]
    when = None
    if cfg["date"] and row["date"]:
        try:
            when = date.fromisoformat(row["date"])
        except ValueError:
            raise ValueError("enter a valid date.") from None
    details = {}
    for key, (kind, label, options) in cfg["extra"].items():
        text = row["x"].get(key, "")
        if not text:
            details[key] = None
        elif kind == "money":
            details[key] = rupees_to_paise(text)
        elif kind == "rate":
            if not re.fullmatch(r"[0-9]{1,2}(?:\.[0-9]{1,2})?", text) or Decimal(text) > 50:
                raise ValueError(f"{label}: enter a percentage from 0 to 50.")
            details[key] = text
        elif kind == "months":
            if not re.fullmatch(r"[0-9]{1,3}", text) or not 1 <= int(text) <= 600:
                raise ValueError(f"{label}: enter whole months from 1 to 600.")
            details[key] = int(text)
        elif text not in options:
            raise ValueError(f"{label}: choose one of the options.")
        else:
            details[key] = text
    return dict(kind=row["kind"], label=row["label"], state=row["state"], amount_minor=amount,
                frequency=frequency, date=when, details=details, visibility=row["visibility"])


def save_section(household_id, section, cfg, form, user, role):
    real_rows = 0
    for n in range(MAX_ROWS):
        if f"{n}-kind" not in form and f"{n}-id" not in form:
            break
        row = form_values(form, n)
        try:
            if row["id"]:
                item = vis.visible(ProfileItem.query.filter_by(id=row["id"], household_id=household_id, section=section),
                                   ProfileItem, user.id, role).first()
                if item is None:
                    raise NotFound("Profile entry not found")
                if str(item.revision) != row["revision"]:
                    raise Conflict("Someone changed this section in another tab. Reopen it before saving; nothing was saved.")
                if row["remove"]:
                    vis.check_write(item, item.visibility, user.id, role)
                    db.session.delete(item)
                    continue
                values = parse_row(cfg, row)
                vis.check_write(item, values["visibility"], user.id, role)
                for key, value in values.items():
                    setattr(item, key, value)
                item.revision += 1
                item.updated_at = utcnow()
            elif row["kind"] or row["label"] or row["amount"] or row["state"]:
                values = parse_row(cfg, row)
                vis.check_write(None, values["visibility"], user.id, role)
                db.session.add(ProfileItem(household_id=household_id, section=section, created_by=user.id, **values))
            else:
                continue
            real_rows += 1
        except ValueError as exc:
            raise ValueError(f"Entry {n + 1}: {exc}") from None
    marker = ProfileItem.query.filter_by(household_id=household_id, section=section, kind=NONE_KIND).first()
    if form.get("none") == "1":
        vis.check_write(marker, vis.HOUSEHOLD, user.id, role)  # only owners record "none" for the household
        others = ProfileItem.query.filter(ProfileItem.household_id == household_id, ProfileItem.section == section,
                                          ProfileItem.kind != NONE_KIND).count()
        if real_rows or others:
            raise ValueError("You ticked 'I have none of these' but entries remain. Remove them or untick the box.")
        if marker is None:
            db.session.add(ProfileItem(household_id=household_id, section=section, kind=NONE_KIND, label="",
                                       state="not_applicable", details={}, created_by=user.id))
    elif marker is not None and role == "owner":  # the checkbox is only offered to owners
        db.session.delete(marker)


@profile.route("/households/<household_id>/profile")
def overview(household_id):
    user = require_user()
    household, role = get_household(user.id, household_id)
    summaries = {key: summarize(key, section_items(household_id, key, user.id, role)) for key in SECTIONS}
    return render_template("profile_overview.html", household=household, role=role, sections=SECTIONS,
                           summaries=summaries, frequencies=FREQUENCIES)


@profile.route("/households/<household_id>/profile/<section>", methods=["GET", "POST"])
def edit(household_id, section):
    user = require_user()
    household, role = get_household(user.id, household_id)
    cfg = SECTIONS.get(section)
    if cfg is None:
        raise NotFound("Profile section not found")
    error, status, posted = None, 200, None
    if request.method == "POST":
        try:
            save_section(household_id, section, cfg, request.form, user, role)
            db.session.commit()
            flash(f"{cfg['title']} saved. Your monthly plan, goals and transactions are unchanged.", "ok")
            return redirect(url_for("profile.edit", household_id=household_id, section=section))
        except (ValueError, AppError) as exc:
            db.session.rollback()
            if isinstance(exc, AppError) and exc.status not in (400, 409):
                raise
            error = exc.message if isinstance(exc, AppError) else str(exc)
            status = exc.status if isinstance(exc, AppError) else 400
            posted = request.form
    items = section_items(household_id, section, user.id, role)
    rows, readonly = [], []
    for item in items:
        if item.kind == NONE_KIND:
            continue
        (rows if vis.can_edit(item, user.id, role) else readonly).append(item)
    default_vis = vis.HOUSEHOLD if role == "owner" else vis.PRIVATE
    if posted is not None:
        editable = [form_values(posted, n) for n in range(MAX_ROWS) if f"{n}-kind" in posted or f"{n}-id" in posted]
        none_checked = posted.get("none") == "1"
    else:
        editable = [item_values(i) for i in rows] + [{"kind": "", "visibility": default_vis, "x": {}} for _ in range(NEW_ROWS)]
        none_checked = any(i.kind == NONE_KIND for i in items)
    return render_template("profile_section.html", household=household, role=role, key=section, cfg=cfg,
                           rows=editable, readonly=readonly, none_checked=none_checked, error=error,
                           states=STATES, frequencies=FREQUENCIES, choices=vis.CHOICES, user_id=user.id,
                           summary=summarize(section, items), monthly_equivalent=monthly_equivalent,
                           today=india_today().isoformat()), status
