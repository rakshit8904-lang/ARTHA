"""Store explicit decisions about pairs of approved ledger entries."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = depends_on = None


def upgrade():
    op.create_table("transfer_decisions",
        sa.Column("debit_id", sa.String(36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("credit_id", sa.String(36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.CheckConstraint("decision in ('confirmed','dismissed','unsure')", name="ck_transfer_decision"))
    for leg in ("debit_id", "credit_id"):
        op.create_index("uq_confirmed_" + leg, "transfer_decisions", [leg], unique=True,
                        sqlite_where=sa.text("decision = 'confirmed'"), postgresql_where=sa.text("decision = 'confirmed'"))


def downgrade():
    op.drop_table("transfer_decisions")
