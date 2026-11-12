"""Persist monthly allocations and user-reviewed recurring expenses."""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = depends_on = None


def upgrade():
    op.add_column("monthly_plans", sa.Column("allocation", sa.JSON(), nullable=True))
    op.create_table(
        "recurring_expenses",
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("fingerprint", sa.String(length=64), primary_key=True),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=True),
        sa.Column("typical_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("confirmed_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('confirmed','dismissed')", name="ck_recurring_expense_status"),
        sa.CheckConstraint("typical_amount_minor >= 0", name="ck_recurring_expense_amount"),
    )


def downgrade():
    op.drop_table("recurring_expenses")
    op.drop_column("monthly_plans", "allocation")
