"""Add manually maintained portfolio holdings."""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("household_id", sa.String(36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_name", sa.String(120), nullable=False),
        sa.Column("asset_type", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("invested_minor", sa.BigInteger(), nullable=False),
        sa.Column("current_value_minor", sa.BigInteger(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("invested_minor >= 0", name="ck_portfolio_invested_nonneg"),
        sa.CheckConstraint("current_value_minor >= 0", name="ck_portfolio_value_nonneg"),
        sa.CheckConstraint("quantity > 0", name="ck_portfolio_quantity_positive"),
        sa.CheckConstraint("asset_type in ('mutual_fund','equity','etf','debt','gold','fixed_deposit','other')", name="ck_portfolio_asset_type"),
    )
    op.create_index("ix_portfolio_holdings_household_id", "portfolio_holdings", ["household_id"])


def downgrade():
    op.drop_index("ix_portfolio_holdings_household_id", table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")
