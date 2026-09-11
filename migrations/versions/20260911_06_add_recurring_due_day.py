"""preserve the intended day for monthly schedules

Revision ID: 20260911_06
Revises: 20260910_05
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alembic import op
import sqlalchemy as sa


revision = "20260911_06"
down_revision = "20260910_05"
branch_labels = None
depends_on = None


def local_day(due_at, timezone_name: str | None) -> int:
    if isinstance(due_at, str):
        due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
    utc_due_at = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
    try:
        return utc_due_at.astimezone(ZoneInfo(timezone_name or "Asia/Kolkata")).day
    except ZoneInfoNotFoundError:
        return utc_due_at.astimezone(ZoneInfo("Asia/Kolkata")).day


def upgrade() -> None:
    with op.batch_alter_table("recurring_transactions") as batch:
        batch.add_column(
            sa.Column("due_day", sa.Integer(), nullable=False, server_default=sa.text("1"))
        )

    bind = op.get_bind()
    rules = sa.table(
        "recurring_transactions",
        sa.column("id", sa.Integer()),
        sa.column("user_id", sa.Integer()),
        sa.column("next_due_at", sa.DateTime(timezone=True)),
        sa.column("due_day", sa.Integer()),
    )
    users = sa.table(
        "users", sa.column("id", sa.Integer()), sa.column("timezone", sa.String())
    )
    rows = bind.execute(
        sa.select(rules.c.id, rules.c.next_due_at, users.c.timezone).join(
            users, rules.c.user_id == users.c.id
        )
    )
    for rule_id, due_at, timezone_name in rows:
        bind.execute(
            rules.update().where(rules.c.id == rule_id).values(due_day=local_day(due_at, timezone_name))
        )

    with op.batch_alter_table("recurring_transactions") as batch:
        batch.alter_column("due_day", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("recurring_transactions") as batch:
        batch.drop_column("due_day")
