import pytest

from app.errors import NotFound
from app.ledger.service import spending_aggregation, spend_totals
from tests.conftest import csv_text


def _approve(actor, import_id, row_ids, *, review_later=False):
    data = {"ids": row_ids}
    if review_later:
        data["review_later"] = "yes"
    response = actor.client.post(f"/imports/{import_id}/approve", data=data)
    assert response.status_code == 302


def _import(actor, account_id, lines):
    result = actor.upload(account_id, csv_text(lines)).get_json()
    import_id = result["import"]["id"]
    rows = actor.rows(import_id)
    return import_id, {row["original_description"]: row["id"] for row in rows}


def test_shared_aggregation_preserves_spend_and_monthly_refund_semantics(app, alice):
    household_id = alice.household()
    account_id = alice.account(household_id)

    first_id, first_rows = _import(alice, account_id, [
        "2026-11-01,Groceries,100.00,debit,purchase,Groceries",
        '2026-11-01,Bank fee,5.00,debit,fee,"Bank Fees & Charges"',
        "2026-11-01,Own transfer,50.00,debit,internal_transfer,",
    ])
    _approve(alice, first_id, list(first_rows.values()))
    # Resolve the purchase by its original description rather than relying on row ordering.
    purchase_response = alice.get(f"/households/{household_id}/transactions?month=2026-11").get_json()["transactions"]
    purchase_id = next(row["id"] for row in purchase_response if row["description"] == "Groceries")

    unmatched_id, unmatched_rows = _import(alice, account_id, [
        "2026-11-02,Unmatched refund,7.00,credit,refund,Shopping & Clothing",
    ])
    _approve(alice, unmatched_id, list(unmatched_rows.values()))

    matched_id, matched_rows = _import(alice, account_id, [
        "2026-11-03,Matched refund,20.00,credit,refund,Travel",
    ])
    refund_row_id = next(iter(matched_rows.values()))
    patched = alice.patch(f"/staged/{refund_row_id}", {"matched_transaction_id": purchase_id})
    assert patched.status_code == 200
    _approve(alice, matched_id, [refund_row_id])

    deferred_id, deferred_rows = _import(alice, account_id, [
        "2026-11-04,Unknown debit,9.00,debit,,",
        "2026-11-04,Unknown credit,3.00,credit,,",
    ])
    _approve(alice, deferred_id, list(deferred_rows.values()), review_later=True)

    with app.app_context():
        all_time = spending_aggregation(alice.user["id"], household_id)
        month = spending_aggregation(alice.user["id"], household_id, "2026-11")
        legacy_shape = spend_totals(alice.user["id"], household_id)

    assert all_time["confirmed"] == 8_500
    assert all_time["debit"] == 900
    assert all_time["credit"] == 300
    assert month["by_category"] == {"Groceries": 8_000, "Bank Fees & Charges": 500}
    assert month["debit"] == 900 and month["credit"] == 300
    assert legacy_shape == {"confirmed": 8_500, "debit": 900, "credit": 300}


def test_shared_aggregation_enforces_household_membership(app, alice, bob):
    household_id = alice.household()
    with app.app_context(), pytest.raises(NotFound):
        spending_aggregation(bob.user["id"], household_id)
