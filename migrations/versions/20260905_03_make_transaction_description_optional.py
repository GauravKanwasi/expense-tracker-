"""Allow transactions without a description."""

from alembic import op
import sqlalchemy as sa


revision = "20260905_03"
down_revision = "20260905_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=255),
            nullable=True,
        )


def downgrade() -> None:
    op.execute("UPDATE transactions SET description = '' WHERE description IS NULL")
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=255),
            nullable=False,
        )
