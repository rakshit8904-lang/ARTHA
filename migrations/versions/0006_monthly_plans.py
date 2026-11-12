"""Save one monthly plan per household and month."""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = depends_on = None


def upgrade():
    op.create_table("monthly_plans",
        sa.Column("household_id", sa.String(36), sa.ForeignKey("households.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("month", sa.String(7), primary_key=True),
        sa.Column("plan_type", sa.String(10), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("income", sa.BigInteger(), nullable=False),
        sa.Column("other_income", sa.BigInteger(), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False))


def downgrade():
    op.drop_table("monthly_plans")
