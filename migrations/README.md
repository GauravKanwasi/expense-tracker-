# Database migrations

Alembic is the source of truth for database schema changes.

For a new database, run:

```powershell
alembic upgrade head
```

For the existing development database, first make a backup and confirm it already has the current `transactions` finance fields and fixed-precision money columns. Then register that schema as the initial Alembic revision and apply the index migration:

```powershell
alembic stamp 20260905_01
alembic upgrade head
```

This applies the dashboard indexes, makes transaction descriptions optional, adds the default `Asia/Kolkata` financial timezone for each user, and adds recurring schedules plus their idempotent transaction link. It also preserves the original monthly day, so a schedule on the 31st returns to the 31st after a shorter month. New and generated transactions are stored in UTC while date filters, monthly budgets, and recurrence due dates use that financial timezone.

The older `0002_add_finance_fields.sql` and `0003_use_fixed_precision_money.sql` files are legacy records. Do not run them after using Alembic.
