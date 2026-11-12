"""Give existing unfinished reviews a deadline based on their last recorded edit."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = depends_on = None


def upgrade():
    op.add_column("imports", sa.Column("review_expires_at", sa.DateTime(timezone=True)))
    last_edit = "(SELECT MAX(updated_at) FROM staged_transactions WHERE import_id = imports.id)"
    deadline = (f"datetime({last_edit}, '+15 minutes')" if op.get_bind().dialect.name == "sqlite"
                else f"{last_edit} + interval '15 minutes'")
    op.execute(f"UPDATE imports SET review_expires_at = {deadline} WHERE EXISTS "
               "(SELECT 1 FROM staged_transactions WHERE import_id = imports.id AND approval_status <> 'approved')")
    op.create_index("ix_imports_review_expires_at", "imports", ["review_expires_at"])


def downgrade():
    op.drop_index("ix_imports_review_expires_at", table_name="imports")
    op.drop_column("imports", "review_expires_at")
