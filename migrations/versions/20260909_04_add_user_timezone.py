"""Store each user's financial timezone."""

from alembic import op
import sqlalchemy as sa


revision = "20260909_04"
down_revision = "20260905_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "timezone",
                sa.String(length=64),
                nullable=False,
                server_default="Asia/Kolkata",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("timezone")
