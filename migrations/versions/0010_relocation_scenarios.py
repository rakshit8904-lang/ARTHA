"""Save household relocation scenarios separately from budgets and ledger."""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = depends_on = None


def upgrade():
    op.create_table("relocation_scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("household_id", sa.String(36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("city_key", sa.String(100), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_relocation_scenarios_household_id", "relocation_scenarios", ["household_id"])


def downgrade():
    op.drop_index("ix_relocation_scenarios_household_id", table_name="relocation_scenarios")
    op.drop_table("relocation_scenarios")
