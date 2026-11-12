from datetime import timedelta
from unittest.mock import patch

from app.extensions import db
from app.imports.expiry import purge_due_reviews
from app.models import Import, StagedTransaction, Transaction, utcnow
from tests.conftest import csv_text


def upload_review(alice):
    household = alice.household("Review home")
    account = alice.account(household)
    csv = csv_text([f"2026-11-01,Item {n},10,debit,purchase,Groceries" for n in range(3)])
    imp = alice.upload(account, csv).get_json()["import"]["id"]
    return account, csv, imp, [r["id"] for r in alice.rows(imp)]


def test_cancel_mixed_review(app, alice, bob):
    _, _, imp, (approved, rejected, pending) = upload_review(alice)
    alice.post("/staged/approve", {"ids": [approved]})
    alice.post(f"/staged/{rejected}/reject")
    assert bob.post(f"/imports/{imp}/cancel").status_code == 404
    assert alice.client.post(f"/imports/{imp}/cancel").status_code == 302
    assert alice.post(f"/imports/{imp}/cancel").status_code == 204
    with app.app_context():
        assert Transaction.query.filter_by(import_id=imp).count() == 1
        assert db.session.get(StagedTransaction, approved)
        assert not db.session.get(StagedTransaction, rejected)
        assert not db.session.get(StagedTransaction, pending)


def test_inactivity_and_late_activity(app, alice, bob):
    account, csv, imp, ids = upload_review(alice)
    original = utcnow()
    later = original + timedelta(minutes=14)
    with patch("app.imports.expiry.utcnow", return_value=later):
        assert bob.post(f"/imports/{imp}/activity").status_code == 404
        assert alice.post(f"/imports/{imp}/activity").status_code == 200
    with patch("app.imports.expiry.utcnow", return_value=later + timedelta(minutes=14, seconds=59)):
        with app.app_context():
            purge_due_reviews()
            assert db.session.get(StagedTransaction, ids[0])
    with patch("app.imports.expiry.utcnow", return_value=later + timedelta(minutes=15)):
        assert alice.post(f"/imports/{imp}/activity").status_code == 404
        assert not alice.post("/staged/approve", {"ids": ids}).get_json()["results"][0]["ok"]
    with app.app_context():
        assert not db.session.get(Import, imp)
        assert StagedTransaction.query.count() == Transaction.query.count() == 0
    assert alice.upload(account, csv).status_code == 201


def test_cleanup_with_browser_closed(app, alice):
    _, _, imp, (approved, rejected, _) = upload_review(alice)
    alice.post("/staged/approve", {"ids": [approved]})
    alice.post(f"/staged/{rejected}/reject")
    with app.app_context(), patch("app.imports.expiry.utcnow", return_value=utcnow() + timedelta(minutes=16)):
        purge_due_reviews()
        purge_due_reviews()
        assert [r.id for r in StagedTransaction.query.filter_by(import_id=imp)] == [approved]
        assert Transaction.query.filter_by(import_id=imp).count() == 1
