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

This applies the dashboard indexes and makes transaction descriptions optional, matching the application model.

The older `0002_add_finance_fields.sql` and `0003_use_fixed_precision_money.sql` files are legacy records. Do not run them after using Alembic.
