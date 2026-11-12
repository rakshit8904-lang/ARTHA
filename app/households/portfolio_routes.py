"""Manual portfolio screens; no prices fetched and no ledger entries created."""
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from app.errors import InvalidRequest, NotFound
from app.extensions import db
from app.households.calculations import rupees_to_paise
from app.households.portfolio import ASSET_TYPES, validate_holding
from app.households.service import get_household, require_member
from app.models import PortfolioHolding, utcnow
from app.session import require_user

portfolio = Blueprint("portfolio", __name__)


@portfolio.route("/households/<household_id>/portfolio", methods=["GET", "POST"])
@portfolio.route("/households/<household_id>/portfolio/<holding_id>", methods=["GET", "POST"])
def index(household_id, holding_id=None):
    user = require_user()
    household, role = get_household(user.id, household_id)
    holding = None
    if holding_id:
        holding = PortfolioHolding.query.filter_by(id=holding_id, household_id=household_id).first()
        if holding is None:
            raise NotFound("Portfolio holding not found")
    values = {}
    if holding:
        values = {key: str(getattr(holding, key)) for key in ('asset_name','asset_type','quantity','as_of_date','notes')}
        values['version'] = holding.updated_at.isoformat()
        for key in ('invested_minor','current_value_minor'):
            amount = getattr(holding,key)
            values[key] = f'{amount//100}.{amount%100:02d}'
    error, status = None, 200
    if request.method == 'POST':
        require_member(user.id, household_id, write=True)
        values = request.form.to_dict()
        try:
            data = dict(values)
            for key in ('invested_minor','current_value_minor'):
                data[key] = rupees_to_paise(values.get(key,''))
            data = validate_holding(data)
            if holding:
                try:
                    version = datetime.fromisoformat(values.get('version',''))
                except ValueError:
                    raise InvalidRequest('Reopen this holding before saving.') from None
                changed = PortfolioHolding.query.filter_by(id=holding.id, household_id=household_id,
                    updated_at=version).update(dict(**data,updated_at=utcnow()))
                if not changed:
                    db.session.rollback()
                    error, status = 'This holding changed in another tab. Reopen it before saving; these inputs have not been saved.', 409
            else:
                db.session.add(PortfolioHolding(household_id=household_id, created_by=user.id, **data))
            if not error:
                db.session.commit()
                flash('Manual holding saved. Your budget and ledger are unchanged.', 'ok')
                return redirect(url_for('portfolio.index',household_id=household_id))
        except (InvalidRequest, ValueError) as exc:
            error, status = getattr(exc,'message',str(exc)), 400
    rows = PortfolioHolding.query.filter_by(household_id=household_id).order_by(PortfolioHolding.asset_name).all()
    invested = sum(row.invested_minor for row in rows)
    current = sum(row.current_value_minor for row in rows)
    dates = sorted({row.as_of_date for row in rows})
    return render_template('portfolio.html', household=household, role=role, holding=holding,
        rows=rows, values=values, types=ASSET_TYPES, invested=invested, current=current,
        dates=dates, error=error), status
