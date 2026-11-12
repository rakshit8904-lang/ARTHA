"""Let a saved goal be private to its creator (and household owners)."""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table("saved_goals") as batch:
        batch.add_column(sa.Column("created_by", sa.String(36), nullable=True))
        batch.add_column(sa.Column("visibility", sa.String(10), nullable=False, server_default="household"))
        batch.create_foreign_key("fk_saved_goals_created_by", "users", ["created_by"], ["id"])


def downgrade():
    with op.batch_alter_table("saved_goals") as batch:
        batch.drop_constraint("fk_saved_goals_created_by", type_="foreignkey")
        batch.drop_column("visibility")
        batch.drop_column("created_by")
