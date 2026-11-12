"""Server-rendered pages. Every handler calls a service with the session's actor id."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from urllib.parse import urlencode

from app.auth import service as auth
from app.constants import APPROVAL_PENDING
from app.cities.affordability import CityDataError, compare_cities, search_cities
from app.errors import AppError, InvalidRequest
from app.extensions import db
from app.households import accounts as account_service
from app.households import service as household_service
from app.households.calculations import rupees_to_paise
from app.imports import review
from app.imports.excel import ChooseSheet
from app.imports import service as import_service
from app.integrations import finance
from app.ledger import service as ledger
from app.ledger.flow import money_flow
from app.ledger.transfers import decide_transfer, transfer_page
from app.models import Account, Household
from app.session import current_user, login_user, logout_user, require_context, require_user

web = Blueprint("web", __name__)


def role_of(user, household_id):
    return household_service.require_member(user.id, household_id).role


@web.get("/")
def index():
    if current_user():
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            user = auth.register(request.form.get("email"), request.form.get("display_name"),
                                 request.form.get("password"))
            # Keep questionnaire answers scoped to this account. Never persist credentials or CSRF data.
            allowed_prefixes = ("personal_", "income_", "expenses_", "loan_", "savings_", "goal_")
            answers = {key: value.strip()[:500] for key, value in request.form.items()
                       if key.startswith(allowed_prefixes) and value.strip()}
            user.onboarding_answers = answers
            user.onboarding_completed = True
            db.session.commit()
            # Give every new account a personal workspace immediately; users can add family members later.
            personal_household = household_service.create_household(user.id, "My finances")
            # A blank savings account lets the user open CSV/Excel import straight after signup.
            account_service.create_account(user.id, personal_household.id, "Primary bank account", "savings")
        except AppError as exc:
            db.session.rollback()
            flash(exc.message, "error")
            return render_template("register.html", form=request.form), exc.status
        login_user(user)
        flash("Account created. Your financial profile is ready. You can import a statement whenever you are ready.", "ok")
        return redirect(url_for("web.dashboard"))
    return render_template("register.html", form={})


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = auth.authenticate(request.form.get("email"), request.form.get("password"))
        except AppError as exc:
            flash(exc.message, "error")
            return render_template("login.html", form=request.form), exc.status
        login_user(user)
        return redirect(url_for("web.dashboard"))
    return render_template("login.html", form={})


@web.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "ok")
    return redirect(url_for("web.login"))


@web.get("/verify/<token>")
def verify(token):
    try:
        auth.verify_email(token)
    except AppError as exc:
        return render_template("error.html", status=400, message=exc.message), 400
    flash("Email verified.", "ok")
    return redirect(url_for("web.dashboard") if current_user() else url_for("web.login"))


@web.get("/verify-needed")
def verify_needed():
    require_user(allow_unverified=True)
    return render_template("verify_needed.html")


@web.post("/verify/resend")
def verify_resend():
    user = require_user(allow_unverified=True)
    sent = auth.send_verification(user)
    flash("Verification email sent." if sent else "We could not send the email. Email delivery may not be set up yet.",
          "ok" if sent else "error")
    return redirect(url_for("web.verify_needed"))


@web.get("/assistant")
def assistant_page():
    """Conversational workspace with optional, explicitly selected household context."""
    user = require_user()
    from datetime import datetime, timedelta, timezone
    households = household_service.list_households(user.id)
    current_month = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m")
    return render_template("assistant.html", households=households, current_month=current_month,
                           default_provider=current_app.config.get("AI_DEFAULT_PROVIDER", "openai"))


@web.get("/dashboard")
def dashboard():
    user = require_user()
    households = household_service.list_households(user.id)
    onboarding = user.onboarding_answers or {}
    def _amount(key):
        try:
            from decimal import Decimal
            value = Decimal(str(onboarding.get(key, "") or ""))
            return value if value.is_finite() and value >= 0 else None
        except Exception:
            return None
    income = _amount("income_primary")
    expense_keys = ("expenses_rent", "expenses_maintenance", "expenses_groceries",
                    "expenses_food", "expenses_transport", "expenses_utilities",
                    "expenses_connectivity", "expenses_health", "expenses_personal",
                    "expenses_subscriptions", "expenses_other", "loan_other_commitments")
    known_expenses = [_amount(k) for k in expense_keys]
    known_expenses = [v for v in known_expenses if v is not None]
    expenses = sum(known_expenses) if known_expenses else None
    debt = _amount("loan_1_outstanding")
    emi = _amount("loan_1_emi")
    savings = sum(v for v in (_amount("savings_bank"), _amount("savings_reserve"),
                              _amount("savings_fd"), _amount("savings_rd"),
                              _amount("savings_mutual_funds"), _amount("savings_stocks")) if v is not None)
    return render_template("dashboard.html", households=households,
                           onboarding=onboarding, onboarding_completed=user.onboarding_completed,
                           primary_household=households[0][0] if households else None,
                           household=households[0][0] if households else None,
                           onboarding_metrics={"income": income, "expenses": expenses, "debt": debt,
                                               "emi": emi, "savings": savings,
                                               "surplus": income - expenses if income is not None and expenses is not None else None})


@web.route("/profile", methods=["GET", "POST"])
def profile():
    user = require_user()
    if request.method == "POST":
        try:
            auth.update_profile(user, request.form.get("display_name"))
            flash("Profile saved.", "ok")
        except AppError as exc:
            flash(exc.message, "error")
            return render_template("profile.html"), exc.status
        return redirect(url_for("web.profile"))
    return render_template("profile.html")


@web.post("/households")
def create_household():
    user = require_user()
    try:
        household = household_service.create_household(user.id, request.form.get("name"))
    except AppError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.household", household_id=household.id))


@web.get("/households/<household_id>")
def household(household_id):
    user = require_user()
    h, role = household_service.get_household(user.id, household_id)
    return render_template("household.html", household=h, role=role,
                           members=household_service.list_members(user.id, household_id),
                           accounts=account_service.list_accounts(user.id, household_id),
                           imports=import_service.list_imports(user.id, household_id)[:5])


@web.route("/households/<household_id>/city-affordability", methods=["GET", "POST"])
def city_affordability(household_id):
    """Compare one-person rent benchmarks against a user's take-home income."""
    user = require_user()
    household, role = household_service.get_household(user.id, household_id)
    query = request.values.get("city", "").strip()[:100]
    income_raw = request.form.get("monthly_income", "").strip() if request.method == "POST" else ""
    results = []
    error = None
    if request.method == "POST":
        try:
            from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
            if not income_raw or len(income_raw) > 14:
                raise InvalidRequest("Enter your monthly take-home income in rupees.")
            try:
                income = Decimal(income_raw)
            except InvalidOperation as exc:
                raise InvalidRequest("Enter a valid monthly income.") from exc
            if not income.is_finite() or income <= 0 or income > Decimal("100000000"):
                raise InvalidRequest("Income must be greater than ₹0 and no more than ₹10 crore.")
            income_paise = int((income * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            results = compare_cities(income_paise, query)
            if not results:
                error = "No matching city was found in the current dataset."
        except (InvalidRequest, CityDataError) as exc:
            error = exc.message if isinstance(exc, InvalidRequest) else str(exc)
    try:
        city_options = search_cities(query, 30)
    except CityDataError as exc:
        city_options, error = [], str(exc)
    return render_template("city_affordability.html", household=household, role=role,
                           query=query, income_raw=income_raw, results=results,
                           city_options=city_options, error=error)


@web.get("/households/<household_id>/learning")
def learning_centre(household_id):
    user = require_user()
    household, role = household_service.get_household(user.id, household_id)
    return render_template("learning.html", household=household, role=role)


@web.get("/households/<household_id>/spend")
def spend_page(household_id):
    user = require_user()
    household, role = household_service.get_household(user.id, household_id)
    rows, total = ledger.list_transactions(user.id, household_id, expense_activity=True, limit=20)
    return render_template("spend.html", household=household, role=role, rows=rows, total=total,
                           totals=ledger.spend_totals(user.id, household_id))


@web.get("/households/<household_id>/money-flow")
def flow_page(household_id):
    user = require_user()
    household, role = household_service.get_household(user.id, household_id)
    selection = tuple(request.args.get(key) for key in ("account", "direction", "node"))
    page = request.args.get("page", 1, type=int)
    edges, selected, rows = money_flow(user.id, household_id, selection, page)
    pair_page = max(1, request.args.get("pairs", 1, type=int))
    confirmed, possible, more = transfer_page(user.id, household_id, pair_page)
    return render_template("money_flow.html", household=household, edges=edges,
                           selected=selected, rows=rows, page=page, confirmed=confirmed, possible=possible,
                           pair_page=pair_page, more=more, role=role)


@web.post("/households/<household_id>/money-flow/transfer")
def transfer_decision(household_id):
    decide_transfer(require_user().id, household_id, request.form.get("debit_id"),
                    request.form.get("credit_id"), request.form.get("choice"))
    return redirect(url_for("web.flow_page", household_id=household_id))


@web.post("/households/<household_id>/rename")
def rename_household(household_id):
    user = require_user()
    try:
        household_service.rename_household(user.id, household_id, request.form.get("name"))
        flash("Household renamed.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
    return redirect(url_for("web.household", household_id=household_id))


@web.post("/households/<household_id>/accounts")
def create_account(household_id):
    user = require_user()
    try:
        account_service.create_account(user.id, household_id, request.form.get("account_name"),
                                       request.form.get("account_type"), request.form.get("institution_name", ""))
        flash("Account added.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
    return redirect(url_for("web.household", household_id=household_id))


@web.post("/accounts/<account_id>")
def edit_account(account_id):
    user = require_user()
    account = account_service.get_account(user.id, account_id)
    try:
        account_service.update_account(user.id, account_id, request.form.get("account_name"),
                                       request.form.get("account_type"), request.form.get("institution_name"),
                                       request.form.get("account_status"))
        flash("Account updated.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
    return redirect(url_for("web.household", household_id=account.household_id))


@web.get("/households/<household_id>/imports")
def imports_page(household_id):
    user = require_user()
    h, role = household_service.get_household(user.id, household_id)
    accounts = [a for a in account_service.list_accounts(user.id, household_id) if a.account_status == "active"]
    return render_template("imports.html", household=h, role=role, accounts=accounts,
                           imports=import_service.list_imports(user.id, household_id))


@web.post("/accounts/<account_id>/imports")
def upload_import(account_id):
    user = require_user()
    account = account_service.get_account(user.id, account_id)
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        flash("Choose a CSV or Excel file to upload.", "error")
        return redirect(url_for("web.imports_page", household_id=account.household_id))
    try:
        imp, already = import_service.create_import(user.id, account_id, upload.filename, upload.read(),
                                                    request.form.get("layout", "signed_amount"), sheet=request.form.get("sheet") or None)
    except ChooseSheet as exc:
        if request.accept_mimetypes.best == "application/json":
            return {"sheets": exc.details["sheets"]}
        flash("Choose a worksheet and reattach the workbook to continue.", "ok")
        household, role = household_service.get_household(user.id, account.household_id)
        return render_template("imports.html", household=household, role=role, accounts=[account],
                               sheets=exc.details["sheets"], layout=request.form.get("layout"),
                               imports=import_service.list_imports(user.id, household.id))
    except AppError as exc:
        if request.accept_mimetypes.best == "application/json":
            return {"error": exc.message}, exc.status
        flash(exc.message, "error")
        return redirect(url_for("web.imports_page", household_id=account.household_id))
    if already:
        flash("This exact file was already imported for this account. No new rows were added.", "ok")
    destination = url_for("web.import_review", import_id=imp.id)
    if request.accept_mimetypes.best == "application/json":
        return {"review": destination}
    return redirect(destination)


@web.get("/imports/<import_id>")
def import_review(import_id):
    user = require_user()
    imp = import_service.get_import(user.id, import_id)
    status = request.args.get("status") or None
    role = role_of(user, imp.household_id)
    if role == "owner" and imp.review_expires_at:
        import_service.review_activity(user.id, imp.id)
    rows = import_service.list_staged(user.id, import_id, status)
    return render_template("review.html", imp=imp, rows=rows, status=status,
                           stats=import_service.import_stats(imp),
                           role=role,
                           display_status=import_service.display_status)


@web.post("/imports/<import_id>/cancel")
def cancel_review(import_id):
    household_id = import_service.cancel_review(require_user().id, import_id)
    flash("Review closed. Unapproved rows discarded.", "ok")
    return redirect(url_for("web.imports_page", household_id=household_id))


@web.get("/staged/<staged_id>")
def staged_detail(staged_id):
    user = require_user()
    row = review.get_staged(user.id, staged_id)
    imp = import_service.get_import(user.id, row.import_id)
    role = role_of(user, row.household_id)
    if role == "owner" and imp.review_expires_at:
        import_service.review_activity(user.id, imp.id)
    return render_template("staged.html", row=row, imp=imp, role=role,
                           display_status=import_service.display_status)


@web.post("/staged/<staged_id>/edit")
def staged_edit(staged_id):
    user = require_user()
    changes = {k: request.form[k] for k in review.EDITABLE_FIELDS if k in request.form}
    try:
        review.edit_staged(user.id, staged_id, changes)
        flash("Row updated.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
    return redirect(url_for("web.staged_detail", staged_id=staged_id))


@web.post("/staged/<staged_id>/reject")
def staged_reject(staged_id):
    user = require_user()
    try:
        row = review.reject_staged(user.id, staged_id)
        flash("Row rejected. It will not count in any totals.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
        row = review.get_staged(user.id, staged_id)
    return redirect(url_for("web.import_review", import_id=row.import_id))


@web.post("/staged/<staged_id>/reopen")
def staged_reopen(staged_id):
    user = require_user()
    try:
        row = review.reopen_staged(user.id, staged_id)
    except AppError as exc:
        flash(exc.message, "error")
        row = review.get_staged(user.id, staged_id)
    return redirect(url_for("web.import_review", import_id=row.import_id))


@web.post("/imports/<import_id>/approve")
def approve(import_id):
    user = require_user()
    imp = import_service.get_import(user.id, import_id)
    ids = request.form.getlist("ids")
    if not ids:
        flash("Select at least one row.", "error")
        return redirect(url_for("web.import_review", import_id=imp.id))
    # Only ids that belong to this import are accepted from the form.
    own = {r.id for r in import_service.list_staged(user.id, imp.id)}
    ids = [i for i in ids if i in own]
    confirm = request.form.get("confirm_duplicates") == "yes"
    try:
        results = review.approve_staged(user.id, ids, confirm, review_later=request.form.get("review_later") == "yes")
    except AppError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.import_review", import_id=imp.id))
    done = sum(1 for r in results if r["ok"])
    flash("%d row(s) approved into the ledger." % done, "ok")
    for r in results:
        if not r["ok"]:
            flash("Row not approved: " + r["error"], "error")
    return redirect(url_for("web.import_review", import_id=imp.id))


@web.post("/imports/<import_id>/set-type")
def set_type(import_id):
    user = require_user()
    imp = import_service.get_import(user.id, import_id)
    own = {r.id for r in import_service.list_staged(user.id, imp.id)}
    ids = [i for i in request.form.getlist("ids") if i in own]
    if not ids:
        flash("Select at least one row.", "error")
    else:
        results = review.set_type_for_rows(user.id, ids, request.form.get("type", ""))
        failed = [r for r in results if not r["ok"]]
        flash("Type set on %d row(s)." % (len(results) - len(failed)), "ok")
        for r in failed:
            flash("Row not changed: " + r["error"], "error")
    return redirect(url_for("web.import_review", import_id=imp.id))


@web.get("/households/<household_id>/ledger")
def ledger_page(household_id):
    user = require_user()
    h, role = household_service.get_household(user.id, household_id)
    month = request.args.get("month") or None
    try:
        rows, total = ledger.list_transactions(
            user.id, household_id, month=month, account_id=request.args.get("account_id") or None,
            transaction_type=request.args.get("type") or None, category=request.args.get("category") or None,
            offset=int(request.args.get("offset", 0) or 0))
    except (AppError, ValueError) as exc:
        flash(getattr(exc, "message", "Invalid filter"), "error")
        rows, total = [], 0
    accounts = {a.id: a for a in account_service.list_accounts(user.id, household_id)}
    return render_template("ledger.html", household=h, role=role, rows=rows, total=total,
                           accounts=accounts, filters=request.args)


@web.get("/transactions/<transaction_id>")
def transaction_detail(transaction_id):
    user = require_user()
    txn = ledger.get_transaction(user.id, transaction_id)
    return render_template("transaction.html", txn=txn, role=role_of(user, txn.household_id),
                           account=db.session.get(Account, txn.account_id))


@web.post("/transactions/<transaction_id>/correct")
def transaction_correct(transaction_id):
    user = require_user()
    changes = {k: request.form[k] for k in ("category", "transaction_type", "matched_transaction_id", "description")
               if k in request.form}
    try:
        ledger.correct_transaction(user.id, transaction_id, changes)
        flash("Correction saved. The previous values are kept in the history.", "ok")
    except AppError as exc:
        flash(exc.message, "error")
    return redirect(url_for("web.transaction_detail", transaction_id=transaction_id))


@web.route("/households/<household_id>/rental-search", methods=["GET", "POST"])
def rental_search(household_id):
    """Build a user-controlled external rental search; no listings are scraped or stored."""
    user = require_user()
    household, role = household_service.get_household(user.id, household_id)
    search_url = None
    values = dict(request.form) if request.method == "POST" else {}
    error = None
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        budget = request.form.get("max_rent", "").strip()
        bedrooms = request.form.get("bedrooms", "any").strip()
        property_type = request.form.get("property_type", "any").strip()
        if not 1 <= len(city) <= 100:
            error = "Enter a city or locality (1-100 characters)."
        elif bedrooms not in ("any", "1", "2", "3", "4"):
            error = "Choose a valid bedroom count."
        elif property_type not in ("any", "apartment", "independent house", "shared room"):
            error = "Choose a valid property type."
        else:
            query_parts = ["Magicbricks rental properties", city]
            if budget:
                try:
                    amount_paise = rupees_to_paise(budget)
                    if amount_paise <= 0:
                        raise ValueError
                    query_parts.append("under INR " + str(amount_paise // 100))
                except ValueError:
                    error = "Enter a valid maximum monthly rent."
            if not error:
                if bedrooms != "any":
                    query_parts.append(bedrooms + " BHK")
                if property_type != "any":
                    query_parts.append(property_type)
                search_url = "https://www.google.com/search?" + urlencode({"q": " ".join(query_parts)})
    return render_template("rental_search.html", household=household, role=role,
                           search_url=search_url, values=values, error=error)


@web.get("/households/<household_id>/summary")
def summary_page(household_id):
    from datetime import datetime, timedelta, timezone
    ctx = require_context()
    h, role = household_service.get_household(ctx.user_id, household_id)
    month = request.args.get("month") or datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m")
    result, problem = None, None
    if month:
        try:
            result = finance.get_monthly_summary(ctx, household_id, month)
        except AppError as exc:
            problem = exc.message
    return render_template("summary.html", household=h, role=role, month=month, result=result,
                           problem=problem, connected=finance.is_connected())
