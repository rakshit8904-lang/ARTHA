"""Leave housing choices unknown on existing plans until the owner edits them."""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = depends_on = None


def upgrade():
    op.add_column("monthly_plans", sa.Column("housing", sa.String(12)))
    op.add_column("monthly_plans", sa.Column("maintenance_included", sa.Boolean()))


def downgrade():
    op.drop_column("monthly_plans", "maintenance_included")
    op.drop_column("monthly_plans", "housing")
