"""Audited city comparison using rent burden only; never invent a total living cost.

The source snapshot's total-cost semantics and extraction date are unverified. We
therefore expose that field as source-reported context only and do not use it in
any affordability calculation.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "processed" / "city_master.csv"
REQUIRED = {"City", "city_key", "rent_one_person_inr", "monthly_salary_after_tax_inr",
            "cost_one_person_inr", "source_url", "usd_to_inr_rate_used"}


class CityDataError(RuntimeError):
    """Raised when the packaged city dataset is unavailable or malformed."""


def _money(value: str) -> int:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        raise CityDataError("A city dataset contains an invalid numeric value.")
    if not amount.is_finite() or amount < 0:
        raise CityDataError("A city dataset contains a negative or non-finite value.")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@lru_cache(maxsize=1)
def _load_rows():
    try:
        with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not REQUIRED.issubset(set(reader.fieldnames or [])):
                raise CityDataError("The city dataset is missing required columns.")
            rows = []
            seen = set()
            for raw in reader:
                key = (raw.get("city_key") or "").strip().casefold()
                name = (raw.get("City") or "").strip()
                if not key or not name or key in seen:
                    raise CityDataError("The city dataset contains a blank or duplicate city.")
                seen.add(key)
                rows.append({
                    "city": name,
                    "city_key": key,
                    "rent_paise": _money(raw["rent_one_person_inr"]),
                    "source_cost_paise": _money(raw["cost_one_person_inr"]),
                    "source_salary_paise": _money(raw["monthly_salary_after_tax_inr"]),
                    "fx_rate": raw["usd_to_inr_rate_used"],
                    "source_url": raw["source_url"],
                })
    except OSError as exc:
        raise CityDataError("The city comparison dataset is unavailable.") from exc
    if not rows:
        raise CityDataError("The city comparison dataset is empty.")
    return tuple(rows)


def search_cities(query: str = "", limit: int = 221):
    """Return city rows; query matches city names and stable keys."""
    needle = (query or "").strip().casefold()
    rows = _load_rows()
    matches = [row for row in rows if not needle or needle in row["city"].casefold()
               or needle in row["city_key"]]
    return matches[:max(1, min(int(limit), 221))]


def rent_burden(income_paise: int, city: dict):
    """Calculate rent share against user-entered take-home income."""
    if not isinstance(income_paise, int) or income_paise <= 0:
        raise ValueError("Monthly take-home income must be a positive integer number of paise.")
    rent = city["rent_paise"]
    ratio = Decimal(rent) * 100 / Decimal(income_paise)
    if ratio < 20:
        band = "Lower rent burden"
    elif ratio < 30:
        band = "Moderate rent burden"
    elif ratio < 40:
        band = "High rent burden"
    else:
        band = "Very high rent burden"
    return {
        "rent_paise": rent,
        "income_paise": income_paise,
        "rent_share_percent": ratio.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
        "after_rent_paise": income_paise - rent,
        "band": band,
        "within_income": rent <= income_paise,
    }


def compare_cities(income_paise: int, query: str = "", limit: int = 221):
    """Compare cities using only the auditable one-person rent benchmark."""
    results = []
    for city in search_cities(query, limit):
        results.append({**city, **rent_burden(income_paise, city)})
    return sorted(results, key=lambda row: (row["rent_share_percent"], row["city"].casefold()))
