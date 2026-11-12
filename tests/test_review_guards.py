"""Guards added after the 9 November code review: refund caps, auth throttling, input types, config."""

import os
import subprocess
import sys
from unittest.mock import patch

from app.auth.supabase import supabase_auth
from app.errors import InvalidRequest
from tests.conftest import csv_text


def purchase_and_refunds(alice, purchase, refunds):
    hid = alice.household()
    acc = alice.account(hid)
    imp = alice.upload(acc, csv_text(["2026-11-01,Shop,%s,debit,purchase," % purchase])).get_json()["import"]["id"]
    row = alice.rows(imp)[0]
    purchase_id = alice.post("/staged/approve", {"ids": [row["id"]]}).get_json()["results"][0]["transaction_id"]
    lines = ["2026-11-0%d,Refund %d,%s,credit,refund," % (i + 2, i, a) for i, a in enumerate(refunds)]
    imp2 = alice.upload(acc, csv_text(lines)).get_json()["import"]["id"]
    return hid, acc, purchase_id, alice.rows(imp2)


def match(alice, row, target):
    return alice.patch("/staged/" + row["id"], {"matched_transaction_id": target}).get_json()["row"]


def test_refund_larger_than_purchase_is_invalid(alice):
    _, _, purchase_id, rows = purchase_and_refunds(alice, "100.00", ["150.00"])
    r = match(alice, rows[0], purchase_id)
    assert r["status"] == "invalid" and "exceed" in r["validation_errors"][0]["message"]


def test_combined_refunds_cannot_exceed_purchase(alice):
    _, _, purchase_id, rows = purchase_and_refunds(alice, "100.00", ["60.00", "60.00"])
    assert all(not match(alice, r, purchase_id)["validation_errors"] for r in rows)  # each alone fits
    results = alice.post("/staged/approve", {"ids": [r["id"] for r in rows]}).get_json()["results"]
    assert results[0]["ok"] and not results[1]["ok"] and "exceed" in results[1]["error"]


def test_refund_cannot_match_income(alice):
    hid = alice.household()
    acc = alice.account(hid)
    imp = alice.upload(acc, csv_text(["2026-11-01,Salary,100.00,credit,income,",
                                      "2026-11-02,Refund,10.00,credit,refund,"])).get_json()["import"]["id"]
    salary, refund = alice.rows(imp)
    income_id = alice.post("/staged/approve", {"ids": [salary["id"]]}).get_json()["results"][0]["transaction_id"]
    r = match(alice, refund, income_id)
    assert r["status"] == "invalid" and "only be matched to a purchase" in r["validation_errors"][0]["message"]


def test_ledger_correction_respects_refund_cap(alice):
    _, _, purchase_id, rows = purchase_and_refunds(alice, "100.00", ["70.00", "70.00"])
    match(alice, rows[0], purchase_id)
    ids = [r["transaction_id"] for r in alice.post("/staged/approve", {"ids": [r["id"] for r in rows]}).get_json()["results"]]
    res = alice.patch("/transactions/" + ids[1], {"matched_transaction_id": purchase_id})
    assert res.status_code == 400 and "exceed" in res.get_json()["error"]["message"]
    # Re-saving the already matched refund must not count itself twice.
    assert alice.patch("/transactions/" + ids[0], {"description": "Refund A"}).status_code == 200


def test_register_attempts_are_rate_limited(app, client):
    app.config["RATE_LIMIT_REGISTER_MAX_ATTEMPTS"] = 2
    body = lambda n: {"email": "u%d@example.com" % n, "display_name": "U", "password": "correct-horse-1"}
    assert client.post("/api/v1/auth/register", json=body(1)).status_code == 201
    assert client.post("/api/v1/auth/register", json=body(1)).status_code == 409
    assert client.post("/api/v1/auth/register", json=body(2)).status_code == 429


def test_successful_login_does_not_clear_ip_failures(app, client, alice):
    app.config["RATE_LIMIT_LOGIN_MAX_ATTEMPTS"] = 3
    login = lambda email, pw: client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login("v1@example.com", "wrong").status_code == 401
    assert login("v2@example.com", "wrong").status_code == 401
    assert login("alice@example.com", "correct-horse-1").status_code == 200
    assert login("v3@example.com", "wrong").status_code == 401
    assert login("v4@example.com", "wrong").status_code == 429


def test_supabase_wrong_password_is_counted(app, client):
    app.config.update(AUTH_PROVIDER="supabase", RATE_LIMIT_LOGIN_MAX_ATTEMPTS=2)
    with patch.object(supabase_auth, "is_configured", return_value=True), \
         patch.object(supabase_auth, "sign_in_with_password", side_effect=InvalidRequest("invalid_grant")):
        login = lambda: client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "nope"})
        assert login().status_code == 401
        assert login().status_code == 401
        assert login().status_code == 429


def test_non_text_json_values_are_rejected(alice, client):
    assert alice.post("/households", {"name": 5}).status_code == 400
    hid = alice.household()
    acc = alice.account(hid)
    assert alice.patch("/accounts/" + acc, {"institution_name": 5}).status_code == 400
    assert client.post("/api/v1/auth/login", json={"email": 5, "password": "x"}).status_code == 400
    assert client.post("/api/v1/auth/register",
                       json={"email": "n@example.com", "display_name": "N", "password": 12345678901}).status_code == 400


def test_edit_keeps_in_file_repeats_unflagged(alice):
    hid = alice.household()
    acc = alice.account(hid)
    imp = alice.upload(acc, csv_text(["2026-11-01,Coffee,50.00,debit,purchase,",
                                      "2026-11-01,Coffee,50.00,debit,purchase,"])).get_json()["import"]["id"]
    first, second = alice.rows(imp)
    assert not second["potential_duplicate"]
    alice.post("/staged/approve", {"ids": [first["id"]]})
    assert not alice.patch("/staged/" + second["id"], {"category": "Food & Dining"}).get_json()["row"]["potential_duplicate"]


def test_edit_flags_duplicate_of_other_pending_import(alice):
    hid = alice.household()
    acc = alice.account(hid)
    alice.upload(acc, csv_text(["2026-11-01,Coffee,50.00,debit,purchase,"]))
    imp2 = alice.upload(acc, csv_text(["2026-11-01,Coffee,51.00,debit,purchase,"])).get_json()["import"]["id"]
    row = alice.rows(imp2)[0]
    assert alice.patch("/staged/" + row["id"], {"amount": "50.00"}).get_json()["row"]["potential_duplicate"]


def test_wsgi_without_app_env_refuses_unsafe_config():
    env = {k: v for k, v in os.environ.items() if k not in ("APP_ENV", "SECRET_KEY", "DATABASE_URL")}
    result = subprocess.run([sys.executable, "-c", "import wsgi"], env=env, capture_output=True, text=True,
                            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), timeout=60)
    assert result.returncode != 0 and "SECRET_KEY must be set" in result.stderr
