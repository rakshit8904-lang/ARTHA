from unittest.mock import patch

import pytest
from app.auth.supabase import sync_supabase_user
from app.errors import Conflict
from app.security.rate_limiter import get_client_ip
from tests.conftest import csv_text


def test_invalid_bearer_cannot_reuse_session_or_skip_csrf(app, alice):
    app.config["CSRF_ENABLED"] = True
    headers = {"Authorization": "Bearer invalid"}
    assert alice.client.get("/api/v1/me", headers=headers).status_code == 401
    assert alice.client.post("/api/v1/households", json={"name":"Denied"}, headers=headers).status_code == 401
    assert alice.client.post("/households", data={"name":"Denied"}, headers=headers).status_code == 400
    assert alice.client.get("/api/v1/households").get_json()["households"] == []


def test_legacy_statement_is_inaccessible_even_when_file_exists(app, alice, tmp_path):
    h = alice.household()
    acct = alice.account(h)
    imp = alice.upload(acct, csv_text(["2026-11-01,Salary,100,credit,income,"])).get_json()["import"]["id"]
    app.config["STORAGE_PATH"] = str(tmp_path)
    old = tmp_path / h / acct / (imp + ".csv.enc")
    old.parent.mkdir(parents=True)
    old.write_bytes(b"fictional old file")
    assert alice.client.get("/imports/"+imp+"/download").status_code == 404
    assert alice.get("/imports/"+imp+"/file").status_code == 404


def test_provider_signup_without_session_and_email_collision(app, alice):
    app.config.update(AUTH_PROVIDER="supabase", SUPABASE_URL="https://example.invalid", SUPABASE_ANON_KEY="test")
    with app.app_context(), pytest.raises(Conflict):
        sync_supabase_user({"id":"other-provider-id", "email":"alice@example.com"})
    client = app.test_client()
    with patch("app.auth.service.supabase_auth.sign_up", return_value={"id":"other-provider-id","email":"alice@example.com"}):
        assert client.post("/api/v1/auth/register", json={"email":"alice@example.com","password":"strong-password","display_name":"A"}).status_code == 400
    assert client.get("/api/v1/me").status_code == 401


def test_untrusted_forwarded_ip_cannot_change_rate_limit_key(app):
    with app.test_request_context(headers={"X-Forwarded-For":"192.0.2.1"}, environ_base={"REMOTE_ADDR":"127.0.0.1"}):
        assert get_client_ip() == "127.0.0.1"
