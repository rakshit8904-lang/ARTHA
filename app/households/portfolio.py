"""Shared manual-holding validation for HTML and JSON clients."""
from datetime import date
from decimal import Decimal, InvalidOperation
from app.errors import InvalidRequest

ASSET_TYPES = {"mutual_fund": "Mutual fund", "equity": "Equity", "etf": "ETF",
               "debt": "Debt", "gold": "Gold", "fixed_deposit": "Fixed deposit", "other": "Other"}


def validate_holding(data):
    name = data.get("asset_name", "")
    asset_type = data.get("asset_type")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise InvalidRequest("asset_name is required (max 120 characters)")
    name = name.strip()
    if not isinstance(asset_type, str) or asset_type not in ASSET_TYPES:
        raise InvalidRequest("Unsupported asset_type")
    def nonnegative_int(key):
        v = data.get(key)
        if type(v) is not int or not 0 <= v <= 999999999999:
            raise InvalidRequest(key + " must be a non-negative integer amount in paise")
        return v
    try:
        quantity = Decimal(str(data.get("quantity", "")))
        as_of = date.fromisoformat(data.get("as_of_date", ""))
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidRequest("quantity and as_of_date must be valid")
    if (not quantity.is_finite() or quantity <= 0 or quantity > Decimal("999999999999")
            or quantity.as_tuple().exponent < -8):
        raise InvalidRequest("quantity must be positive and finite, with at most eight decimal places")
    notes = data.get("notes", "")
    if not isinstance(notes, str) or len(notes) > 500:
        raise InvalidRequest("notes must be text with at most 500 characters")
    return dict(asset_name=name, asset_type=asset_type, quantity=quantity,
                invested_minor=nonnegative_int("invested_minor"),
                current_value_minor=nonnegative_int("current_value_minor"), as_of_date=as_of, notes=notes)
