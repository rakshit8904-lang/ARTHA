"""Persist signup questionnaire answers per user."""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = depends_on = None


def upgrade():
    op.add_column("users", sa.Column("onboarding_answers", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "onboarding_answers")
