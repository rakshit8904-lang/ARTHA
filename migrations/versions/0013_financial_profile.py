"""Ongoing financial profile items, separate from monthly plans and the ledger."""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = depends_on = None


def upgrade():
    op.create_table("profile_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("household_id", sa.String(36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("frequency", sa.String(12), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("visibility", sa.String(10), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_profile_items_household_id", "profile_items", ["household_id"])


def downgrade():
    op.drop_index("ix_profile_items_household_id", table_name="profile_items")
    op.drop_table("profile_items")
