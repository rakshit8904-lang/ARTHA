"""Allow an explicitly approved ledger record to await classification."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = depends_on = None


def set_nullable(nullable):
    # SQLite rebuilds this table. Preserve self-referencing refund links across the swap.
    sqlite = op.get_bind().dialect.name == "sqlite"
    if sqlite:
        op.execute("CREATE TEMP TABLE review_later_links AS SELECT id, matched_transaction_id "
                   "FROM transactions WHERE matched_transaction_id IS NOT NULL")
        op.execute("UPDATE transactions SET matched_transaction_id = NULL WHERE matched_transaction_id IS NOT NULL")
    with op.batch_alter_table("transactions") as table:
        table.alter_column("transaction_type", existing_type=sa.String(30), nullable=nullable)
    if sqlite:
        op.execute("UPDATE transactions SET matched_transaction_id = "
                   "(SELECT matched_transaction_id FROM review_later_links WHERE id = transactions.id) "
                   "WHERE id IN (SELECT id FROM review_later_links)")
        op.execute("DROP TABLE review_later_links")


def upgrade():
    set_nullable(True)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM transactions WHERE transaction_type IS NULL LIMIT 1")).first():
        raise RuntimeError("Classify outstanding transactions before downgrading.")
    set_nullable(False)
