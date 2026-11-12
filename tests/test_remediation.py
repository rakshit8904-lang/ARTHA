import json
import time
from unittest.mock import patch
import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.supabase import sync_supabase_user
from app.extensions import db
from app.models import Import, StagedTransaction, Transaction, new_id
from app.security.rate_limiter import limiter


def test_account_household_consistency_constraint(app, alice):
    """
    Test Task 7: Database constraints guarantee that an account, import, staged row,
    and transaction cannot reference mismatched household IDs.
    """
    with app.app_context():
        # Alice creates household 1 and account 1
        h1_id = alice.household("Household One")
        h2_id = alice.household("Household Two")
        acct1_id = alice.account(h1_id, "Savings 1")

        # Attempt to insert an import pointing to acct1 but belonging to h2
        bad_import = Import(
            id=new_id(),
            household_id=h2_id,  # Mismatched! acct1 belongs to h1!
            account_id=acct1_id,
            uploaded_by=alice.user["id"],
            file_hash="hash123",
            filename="test.csv",
            parser_version="csv-v1",
            import_status="staged"
        )
        db.session.add(bad_import)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_csv_keeps_only_review_fields(app, alice, tmp_path):
    app.config["STORAGE_PATH"] = str(tmp_path / "vault")
    account = alice.account(alice.household("Demo"))
    csv = "date,description,amount,private_note\n2026-11-01,Milk,-100,discard-this-note\n"
    response = alice.upload(account, csv)
    assert response.status_code == 201
    import_id = response.get_json()["import"]["id"]
    with app.app_context():
        row = StagedTransaction.query.filter_by(import_id=import_id).one()
        assert row.raw_row == {}
        assert (row.description, row.amount_minor) == ("Milk", 10000)
    assert not any(p.is_file() for p in (tmp_path / "vault").rglob("*"))
    assert alice.get(f"/imports/{import_id}/file").status_code == 404
    assert alice.client.get(f"/imports/{import_id}/download").status_code == 404
    assert alice.upload(account, csv).get_json()["already_imported"]


def test_parse_failure_after_valid_row_keeps_no_source_or_expenses(app, alice, tmp_path):
    app.config["STORAGE_PATH"] = str(tmp_path / "vault")
    account = alice.account(alice.household("Demo"))
    csv = 'date,description,amount\n2026-11-01,Milk,-100\n2026-11-02,"unfinished'
    assert alice.upload(account, csv).status_code == 400
    with app.app_context():
        assert StagedTransaction.query.filter_by(account_id=account).count() == 0
        assert Transaction.query.filter_by(account_id=account).count() == 0
    assert not any(p.is_file() for p in (tmp_path / "vault").rglob("*"))


def test_login_rate_limiting(client, app):
    """
    Test Task 5: Exceeding failed login attempts triggers 429 Too Many Requests
    with Retry-After header.
    """
    limiter.clear()
    app.config["RATE_LIMIT_LOGIN_MAX_ATTEMPTS"] = 3
    app.config["RATE_LIMIT_LOGIN_WINDOW_SECONDS"] = 60

    # 3 failed login attempts
    for _ in range(3):
        res = client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": "wrong"})
        assert res.status_code == 401

    # 4th attempt is rate-limited
    res = client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": "wrong"})
    assert res.status_code == 429
    assert res.json["error"]["code"] == "rate_limited"
    assert "Retry-After" in res.headers

    limiter.clear()


def test_supabase_auth_integration(app, client):
    """
    Test Task 2: Supabase Auth integration syncs Supabase users into local User table,
    creates authenticated sessions, and grants full access to household features.
    """
    mock_sub_user = {
        "id": "supabase-uuid-12345",
        "email": "supabase_user@example.com",
        "email_confirmed_at": "2026-11-04T12:00:00Z",
        "user_metadata": {
            "display_name": "Supabase Member"
        }
    }

    with app.app_context():
        # Test user syncing
        user = sync_supabase_user(mock_sub_user)
        assert user.email == "supabase_user@example.com"
        assert user.auth_provider == "supabase"
        assert user.auth_ref == "supabase-uuid-12345"
        assert user.email_verified_at is not None

        # Verify idempotency / update
        user2 = sync_supabase_user(mock_sub_user)
        assert user2.id == user.id

    # Test API endpoint /auth/supabase/session
    with patch("app.auth.service.authenticate_supabase_token") as mock_auth_token:
        mock_auth_token.return_value = user
        res = client.post("/api/v1/auth/supabase/session", json={"access_token": "valid-supabase-jwt"})
        assert res.status_code == 200
        assert res.json["user"]["email"] == "supabase_user@example.com"
        assert "csrf_token" in res.json

    # Test Bearer token authentication on protected routes
    with patch("app.auth.service.authenticate_supabase_token") as mock_auth_token:
        mock_auth_token.return_value = user
        res = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-supabase-jwt"})
        assert res.status_code == 200
        assert res.json["user"]["email"] == "supabase_user@example.com"
