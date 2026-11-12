from datetime import timedelta
import os
import sqlite3
import subprocess
import sys

import pytest

from app.extensions import db
from app import create_app
from app.imports.expiry import purge_due_reviews
from app.models import Import, Transaction, utcnow
from tests.conftest import Api, csv_text


@pytest.mark.parametrize("kind, category, confirmed", [
    ("purchase", "Groceries", "₹5,000.00"), ("internal_transfer", "", "₹0.00"),
])
def test_deferred_expense_end_to_end(app, alice, bob, kind, category, confirmed):
    hid = alice.household()
    account = alice.account(hid)
    csv = csv_text(["2026-11-01,Unknown payment,5000,debit,,",
                    "2026-11-02,Pending item,100,debit,,"])
    imp = alice.upload(account, csv).get_json()["import"]["id"]
    row = alice.rows(imp)[0]["id"]
    action = f"/imports/{imp}/approve"
    assert not alice.post("/staged/approve", {"ids": [row]}).get_json()["results"][0]["ok"]
    assert b"Approve &amp; review later" in alice.client.get(f"/imports/{imp}").data
    assert alice.client.post(action, data={"ids": row, "review_later": "yes"}).status_code == 302
    with app.app_context():
        db.session.get(Import, imp).review_expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
        purge_due_reviews()
        saved = Transaction.query.one()
        assert saved.transaction_type is None and saved.approval_status == "approved"
        txn = saved.id
    alice.post("/auth/logout")
    assert alice.post("/auth/login", {"email": "alice@example.com", "password": "correct-horse-1"}).status_code == 200
    spend = f"/households/{hid}/spend"
    page = alice.client.get(spend).get_data(as_text=True)
    assert "Money out: ₹5,000.00" in page and "<strong>₹0.00</strong>" in page
    queue = alice.client.get(f"/households/{hid}/ledger?type=unclassified")
    assert txn.encode() in queue.data
    assert bob.patch(f"/transactions/{txn}", {"transaction_type": kind}).status_code == 404
    result = alice.client.post(f"/transactions/{txn}/correct", data={"transaction_type": kind, "category": category})
    assert result.status_code == 302
    page = alice.client.get(spend).get_data(as_text=True)
    assert "Awaiting classification" not in page and f"<strong>{confirmed}</strong>" in page
    assert ("Unknown payment" in page) == (kind == "purchase")
    assert alice.get(f"/transactions/{txn}").get_json()["transaction"]["transaction_type"] == kind


def test_deferred_approval_keeps_validation_and_duplicate_checks(alice):
    hid = alice.household()
    acc = alice.account(hid)
    csv = csv_text(["2026-11-01,Unknown,5000,debit,,", "bad-date,Invalid,1,debit,,"])
    imp = alice.upload(acc, csv).get_json()["import"]["id"]
    ids = [row["id"] for row in alice.rows(imp)]
    def approve(ids):
        return alice.post("/staged/approve", {"ids": ids, "review_later": True}).get_json()["results"]
    assert [r["ok"] for r in approve(ids)] == [True, False]
    assert not approve(ids[:1])[0]["ok"]
    other = alice.upload(acc, csv + "\n").get_json()["import"]["id"]
    duplicate = approve([alice.rows(other)[0]["id"]])[0]
    assert not duplicate["ok"] and "duplicate" in duplicate["error"].lower()


def test_upgrade_keeps_existing_refund_links(tmp_path):
    path = tmp_path / "old.db"
    uri = "sqlite:///" + path.as_posix()
    def upgrade(revision):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                       env=dict(os.environ, DATABASE_URL=uri), check=True)
    upgrade("0003")
    app = create_app({"TESTING": True, "CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": uri})
    actor = Api(app)
    acct = actor.account(actor.household())
    data = csv_text(["2026-11-01,Milk,100,debit,purchase,Groceries", "2026-11-02,Return,20,credit,refund,"])
    imp = actor.upload(acct, data).get_json()["import"]["id"]
    results = actor.post("/staged/approve", {"ids": [r["id"] for r in actor.rows(imp)]}).get_json()["results"]
    purchase, refund = [r["transaction_id"] for r in results]
    assert actor.patch("/transactions/" + refund, {"matched_transaction_id": purchase}).status_code == 200
    with app.app_context():
        db.engine.dispose()
    upgrade("0004")
    with sqlite3.connect(path) as con:
        assert dict(con.execute("SELECT id, matched_transaction_id FROM transactions")) == {purchase: None, refund: purchase}
        assert not con.execute("PRAGMA foreign_key_check").fetchall()
