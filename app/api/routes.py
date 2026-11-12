"""JSON API under /api/v1. Same services and same authorization as the pages."""

from flask import Blueprint, current_app, jsonify, request

from app.api import serializers as ser
from app.ai.orchestrator import answer as assistant_answer, route_agent
from app.ai.agents.registry import AGENTS
from app.ai.providers.base import ProviderError
from app.auth import service as auth
from app.errors import InvalidRequest
from app.households import accounts as account_service
from app.households import service as household_service
from app.imports import review
from app.imports import service as import_service
from app.integrations import finance
from app.ledger import service as ledger
from app.session import login_user, logout_user, require_context, require_user, csrf_token

api = Blueprint("api", __name__)


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise InvalidRequest("Send a JSON object")
    return data


@api.get("/csrf")
def get_csrf():
    """API clients call this first to get a token (and a session cookie) for register/login."""
    return jsonify({"csrf_token": csrf_token()})


@api.post("/auth/register")
def register():
    data = body()
    user = auth.register(data.get("email"), data.get("display_name"), data.get("password"))
    login_user(user)
    return jsonify({"user": ser.user_json(user), "csrf_token": csrf_token()}), 201


@api.post("/auth/login")
def login():
    data = body()
    user = auth.authenticate(data.get("email"), data.get("password"))
    login_user(user)
    return jsonify({"user": ser.user_json(user), "csrf_token": csrf_token()})


@api.post("/auth/supabase/session")
def supabase_session():
    data = body()
    token = data.get("access_token")
    if not token:
        raise InvalidRequest("access_token is required")
    user = auth.authenticate_supabase_token(token)
    login_user(user)
    return jsonify({"user": ser.user_json(user), "csrf_token": csrf_token()})


@api.post("/auth/logout")
def logout():
    logout_user()
    return jsonify({"ok": True})


@api.get("/me")
def me():
    return jsonify({"user": ser.user_json(require_user(allow_unverified=True))})


@api.patch("/me")
def update_me():
    user = require_user()
    return jsonify({"user": ser.user_json(auth.update_profile(user, body().get("display_name")))})


@api.get("/households")
def households():
    user = require_user()
    return jsonify({"households": [ser.household_json(h, r) for h, r in household_service.list_households(user.id)]})


@api.post("/households")
def create_household():
    user = require_user()
    h = household_service.create_household(user.id, body().get("name"))
    return jsonify({"household": ser.household_json(h, "owner")}), 201


@api.get("/households/<household_id>")
def household(household_id):
    user = require_user()
    h, role = household_service.get_household(user.id, household_id)
    return jsonify({"household": ser.household_json(h, role),
                    "members": household_service.list_members(user.id, household_id)})


@api.get("/households/<household_id>/accounts")
def list_accounts(household_id):
    user = require_user()
    return jsonify({"accounts": [ser.account_json(a) for a in account_service.list_accounts(user.id, household_id)]})


@api.post("/households/<household_id>/accounts")
def create_account(household_id):
    user = require_user()
    d = body()
    a = account_service.create_account(user.id, household_id, d.get("account_name"), d.get("account_type"),
                                       d.get("institution_name", ""), d.get("currency", "INR"))
    return jsonify({"account": ser.account_json(a)}), 201


@api.patch("/accounts/<account_id>")
def update_account(account_id):
    user = require_user()
    d = body()
    a = account_service.update_account(user.id, account_id, d.get("account_name"), d.get("account_type"),
                                       d.get("institution_name"), d.get("account_status"))
    return jsonify({"account": ser.account_json(a)})


@api.post("/accounts/<account_id>/imports")
def upload(account_id):
    user = require_user()
    upload_file = request.files.get("file")
    if upload_file is None:
        raise InvalidRequest("Attach a file in the 'file' field")
    imp, already = import_service.create_import(user.id, account_id, upload_file.filename, upload_file.read(),
                                                request.form.get("layout", "signed_amount"), sheet=request.form.get("sheet") or None)
    return jsonify({"import": ser.import_json(imp, import_service.import_stats(imp)),
                    "already_imported": already}), 200 if already else 201


@api.get("/households/<household_id>/imports")
def list_imports(household_id):
    user = require_user()
    return jsonify({"imports": [ser.import_json(i) for i in import_service.list_imports(user.id, household_id)]})


@api.get("/imports/<import_id>")
def get_import(import_id):
    user = require_user()
    imp = import_service.get_import(user.id, import_id)
    return jsonify({"import": ser.import_json(imp, import_service.import_stats(imp))})


@api.post("/imports/<import_id>/cancel")
def cancel_review(import_id):
    import_service.cancel_review(require_user().id, import_id)
    return "", 204


@api.post("/imports/<import_id>/activity")
def review_activity(import_id):
    deadline = import_service.review_activity(require_user().id, import_id)
    return jsonify({"expires_at": deadline.strftime("%Y-%m-%dT%H:%M:%S.%fZ")})


@api.get("/imports/<import_id>/rows")
def import_rows(import_id):
    user = require_user()
    rows = import_service.list_staged(user.id, import_id, request.args.get("status") or None)
    return jsonify({"rows": [ser.staged_json(r, import_service.display_status(r)) for r in rows]})


@api.patch("/staged/<staged_id>")
def edit_row(staged_id):
    user = require_user()
    row = review.edit_staged(user.id, staged_id, {k: str(v) if v is not None else "" for k, v in body().items()})
    return jsonify({"row": ser.staged_json(row, import_service.display_status(row))})


@api.post("/staged/<staged_id>/reject")
def reject_row(staged_id):
    user = require_user()
    row = review.reject_staged(user.id, staged_id)
    return jsonify({"row": ser.staged_json(row, import_service.display_status(row))})


@api.post("/staged/<staged_id>/reopen")
def reopen_row(staged_id):
    user = require_user()
    row = review.reopen_staged(user.id, staged_id)
    return jsonify({"row": ser.staged_json(row, import_service.display_status(row))})


@api.post("/staged/approve")
def approve_rows():
    user = require_user()
    d = body()
    ids = d.get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        raise InvalidRequest("ids must be a list of row ids")
    later = d.get("review_later", False)
    if not isinstance(later, bool):
        raise InvalidRequest("review_later must be true or false")
    return jsonify({"results": review.approve_staged(user.id, ids, d.get("confirm_duplicates") is True,
                                                     review_later=later)})


@api.get("/households/<household_id>/transactions")
def transactions(household_id):
    user = require_user()
    rows, total = ledger.list_transactions(
        user.id, household_id, month=request.args.get("month"), account_id=request.args.get("account_id"),
        transaction_type=request.args.get("type"), category=request.args.get("category"),
        limit=request.args.get("limit", 200, type=int), offset=request.args.get("offset", 0, type=int))
    return jsonify({"total": total, "transactions": [ser.transaction_json(t) for t in rows]})


@api.get("/transactions/<transaction_id>")
def transaction(transaction_id):
    user = require_user()
    return jsonify({"transaction": ser.transaction_json(ledger.get_transaction(user.id, transaction_id))})


@api.patch("/transactions/<transaction_id>")
def correct(transaction_id):
    user = require_user()
    t = ledger.correct_transaction(user.id, transaction_id, body())
    return jsonify({"transaction": ser.transaction_json(t)})


@api.get("/households/<household_id>/summary")
def summary(household_id):
    ctx = require_context()
    return jsonify(finance.get_monthly_summary(ctx, household_id, request.args.get("month", "")))


@api.post("/households/<household_id>/relocation/estimate")
def relocation_estimate(household_id):
    from app.households.service import require_member
    from app.households.relocation import calculate_relocation
    from app.session import require_user
    user = require_user()
    require_member(user.id, household_id)
    data = body()
    def amount(key):
        value = data.get(key, None if key in ("monthly_income_minor", "rent_minor") else 0)
        if type(value) is not int or not 0 <= value <= 999999999999:
            raise InvalidRequest(key + " must be a non-negative integer amount in paise")
        return value
    try:
        result = calculate_relocation(
            monthly_income_minor=amount("monthly_income_minor"), rent_minor=amount("rent_minor"),
            utilities_minor=amount("utilities_minor"), food_minor=amount("food_minor"),
            transport_minor=amount("transport_minor"), other_minor=amount("other_minor"),
            deposit_months=data.get("deposit_months", 0),
            moving_cost_minor=amount("moving_cost_minor"), setup_cost_minor=amount("setup_cost_minor"))
    except ValueError as exc:
        raise InvalidRequest(str(exc))
    return jsonify(result)


@api.get("/households/<household_id>/portfolio")
def portfolio_list(household_id):
    from app.households.service import require_member
    from app.models import PortfolioHolding
    user = require_user()
    require_member(user.id, household_id)
    rows = PortfolioHolding.query.filter_by(household_id=household_id).order_by(PortfolioHolding.asset_name).all()
    invested = sum(x.invested_minor for x in rows)
    current = sum(x.current_value_minor for x in rows)
    return jsonify({"holdings": [{"id": x.id, "asset_name": x.asset_name, "asset_type": x.asset_type,
        "quantity": str(x.quantity), "invested_minor": x.invested_minor,
        "current_value_minor": x.current_value_minor, "gain_loss_minor": x.current_value_minor-x.invested_minor,
        "as_of_date": x.as_of_date.isoformat(), "notes": x.notes} for x in rows],
        "totals": {"invested_minor": invested, "current_value_minor": current,
                   "gain_loss_minor": current-invested,
                   "return_ratio": ((current-invested)/invested if invested else None)},
        "pricing_basis": "user_entered_values_no_live_market_prices"})


@api.post("/households/<household_id>/portfolio")
def portfolio_create(household_id):
    from app.extensions import db
    from app.households.service import require_member
    from app.households.portfolio import validate_holding
    from app.models import PortfolioHolding
    user = require_user()
    require_member(user.id, household_id, write=True)
    holding = PortfolioHolding(household_id=household_id, created_by=user.id, **validate_holding(body()))
    db.session.add(holding)
    db.session.commit()
    return jsonify({"id": holding.id, "asset_name": holding.asset_name}), 201


@api.delete("/portfolio/<holding_id>")
def portfolio_delete(holding_id):
    from app.extensions import db
    from app.households.service import require_member
    from app.models import PortfolioHolding
    user = require_user()
    holding = db.session.get(PortfolioHolding, holding_id)
    if holding is None:
        from app.errors import NotFound
        raise NotFound("Portfolio holding not found")
    require_member(user.id, holding.household_id, write=True)
    db.session.delete(holding)
    db.session.commit()
    return jsonify({"deleted": True})


@api.post("/assistant/chat")
def assistant_chat():
    """General education plus explicitly selected, permission-filtered read-only context."""
    user = require_user()
    data = body()
    provider = "gemini"  # Server-enforced: clients cannot select a different provider.
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > 10:
        raise InvalidRequest("Send between 1 and 10 recent messages.")
    clean = []
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            raise InvalidRequest("Each message must have a user or assistant role.")
        content = item.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 3000:
            raise InvalidRequest("Messages must contain 1–3000 characters.")
        clean.append({"role": item["role"], "content": content.strip()})
    if clean[-1]["role"] != "user":
        raise InvalidRequest("The latest message must be from the user.")
    financial_context = None
    household_id = data.get("household_id")
    if household_id:
        if not isinstance(household_id, str) or len(household_id) > 128:
            raise InvalidRequest("Invalid household selection.")
        month = data.get("month")
        if not isinstance(month, str) or len(month) != 7:
            raise InvalidRequest("Choose a valid month for the financial summary.")
        # The finance gateway validates membership using the trusted server-side context.
        summary = finance.get_monthly_summary(require_context(), household_id, month)
        # Minimise context before sending it to a model: no household IDs or transaction rows.
        monthly_summary = {key: summary.get(key) for key in (
            "month", "currency", "transaction_count", "income_minor", "confirmed_spending_minor",
            "net_after_confirmed_spending_minor", "coverage_status", "coverage",
            "spending_by_category_minor", "excluded_movements", "notes")}
        financial_context = {"monthly_summary": monthly_summary}
        include_extended = data.get("include_extended_context", False)
        if not isinstance(include_extended, bool):
            raise InvalidRequest("include_extended_context must be true or false.")
        if include_extended:
            from app.ai.tools.household import build_household_context
            financial_context["extended_household_context"] = build_household_context(user.id, household_id)
    elif data.get("include_extended_context", False):
        raise InvalidRequest("Select a household before including profile, goals or portfolio context.")
    agent_name = route_agent(clean)
    try:
        reply, selected_agent = assistant_answer(
            clean, provider_name=provider, financial_context=financial_context, agent_name=agent_name)
    except ProviderError as exc:
        return jsonify({"error": {"code": "ai_provider_unavailable", "message": str(exc)}}), 503
    return jsonify({
        "reply": reply,
        "provider": provider,
        "agent": selected_agent,
        "agent_label": AGENTS[selected_agent]["label"],
        "mode": "read_only_monthly_analysis" if financial_context is not None else "general_education",
        "action_approval": {"enabled": False, "reason": "State-changing tools are not connected yet."},
    })


@api.get("/assistant/status")
def assistant_status():
    """Expose provider readiness without ever returning secrets."""
    require_user()
    return jsonify({
        "default_provider": "gemini",
        "providers": {
            "gemini": {"configured": bool(current_app.config.get("GEMINI_API_KEY")),
                       "model": current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")},
        },
        "agent_count": len(AGENTS),
        "actions_require_approval": True,
        "state_changing_tools_enabled": False,
    })
