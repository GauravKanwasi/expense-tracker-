"""Add indexes used by the dashboard queries."""

from alembic import op


revision = "20260905_02"
down_revision = "20260905_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_categories_user_id", "categories", ["user_id"], unique=False)
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "date"], unique=False)
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_index("ix_categories_user_id", table_name="categories")
