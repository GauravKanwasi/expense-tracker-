"""add recurring transaction schedules

Revision ID: 20260910_05
Revises: 20260909_04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260910_05"
down_revision = "20260909_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(31, 2), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("debt_direction", sa.String(20), nullable=True),
        sa.Column("interest_amount", sa.Numeric(31, 2), nullable=True),
        sa.Column("investment_action", sa.String(20), nullable=True),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_recurring_transactions_user"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_recurring_transactions_category"
        ),
    )
    op.create_index(
        "ix_recurring_transactions_user_due",
        "recurring_transactions",
        ["user_id", "next_due_at"]
    )
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("recurring_transaction_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_transactions_recurring_transaction",
            "recurring_transactions",
            ["recurring_transaction_id"],
            ["id"],
            ondelete="SET NULL"
        )
        batch.create_unique_constraint(
            "uq_transactions_recurring_date",
            ["recurring_transaction_id", "date"]
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_constraint("uq_transactions_recurring_date", type_="unique")
        batch.drop_constraint("fk_transactions_recurring_transaction", type_="foreignkey")
        batch.drop_column("recurring_transaction_id")
    op.drop_index("ix_recurring_transactions_user_due", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
