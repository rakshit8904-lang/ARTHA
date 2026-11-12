from decimal import Decimal

from app.cities.affordability import compare_cities, rent_burden, search_cities


def test_city_dataset_loads_unique_cities_and_supports_search():
    rows = search_cities()
    assert len(rows) == 221
    assert len({row["city_key"] for row in rows}) == 221
    assert search_cities("cuttack")
    assert search_cities("not-a-real-city") == []


def test_rent_burden_uses_user_income_and_not_ambiguous_total_cost():
    city = search_cities("adoni")[0]
    result = rent_burden(5_000_000, city)  # ₹50,000/month
    assert result["rent_paise"] == city["rent_paise"]
    assert result["rent_share_percent"] == (Decimal(city["rent_paise"]) * 100 / Decimal(5_000_000)).quantize(Decimal("0.1"))
    assert result["after_rent_paise"] == 5_000_000 - city["rent_paise"]
    assert city["source_cost_paise"] > 0  # retained as provenance context, never used in rent burden


def test_compare_sorts_by_rent_share_and_does_not_relabel_cost_total():
    rows = compare_cities(5_000_000, limit=221)
    assert len(rows) == 221
    assert rows == sorted(rows, key=lambda row: (row["rent_share_percent"], row["city"].casefold()))
    assert all("source_cost_paise" in row for row in rows)
