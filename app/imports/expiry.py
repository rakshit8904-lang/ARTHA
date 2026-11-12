"""Serialize review activity, cancellation and expiry on the import record."""
from datetime import timedelta
from threading import Thread
from time import sleep

from sqlalchemy.exc import SQLAlchemyError

from app.errors import Conflict
from app.extensions import db
from app.models import Import, StagedTransaction, utcnow

IDLE_LIMIT = timedelta(minutes=15)


def new_deadline():
    return utcnow() + IDLE_LIMIT


def extend_review(import_id):
    # This conditional write also locks the parent until the row mutation commits.
    changed = Import.query.filter(Import.id == import_id, Import.review_expires_at > utcnow()).update(
        {"review_expires_at": new_deadline()}, synchronize_session=False)
    if not changed:
        raise Conflict("This review has ended. Return to your imports.")


def discard_review(import_id, *, expired_by=None):
    claim = Import.query.filter(Import.id == import_id, Import.review_expires_at.isnot(None))
    if expired_by is not None:
        claim = claim.filter(Import.review_expires_at <= expired_by)
    if not claim.update({"review_expires_at": None}, synchronize_session=False):
        return
    rows = StagedTransaction.query.filter_by(import_id=import_id)
    rows.filter(StagedTransaction.approval_status != "approved").delete(synchronize_session=False)
    approved = rows.count()
    parent = Import.query.filter_by(id=import_id)
    if approved:
        parent.update(dict(import_status="completed", total_rows=approved, valid_rows=approved, invalid_rows=0))
    else:
        parent.delete(synchronize_session=False)  # Allows a fresh upload of a wholly discarded file.


def purge_due_reviews():
    now = utcnow()
    due = db.session.query(Import.id).filter(Import.review_expires_at <= now).order_by(Import.id).all()
    for (import_id,) in due:
        discard_review(import_id, expired_by=now)
    if due:
        db.session.commit()


def start_cleanup(app):
    def run():
        while True:
            with app.app_context():
                try:
                    purge_due_reviews()
                except SQLAlchemyError:
                    db.session.rollback()
                    app.logger.warning("Review cleanup could not access the database. Retrying.")
            sleep(5)

    Thread(target=run, name="review-expiry", daemon=True).start()
