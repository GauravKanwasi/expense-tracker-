# Security and sharing

## If a private `.env` file was shared

1. Change the password for the PostgreSQL role used by `DATABASE_URL` in your database host or with a database administrator account.
2. Update the private `.env` file with the new password. Do not commit or send that file.
3. Rotate the JWT signing secret by running:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\rotate-jwt-secret.ps1
```

4. Restart the API. Everyone must log in again after a JWT secret rotation.

## Share the project safely

Do not use File Explorer to zip the whole project folder. From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create-share-archive.ps1
```

This uses `git archive`, which includes tracked source files only. It refuses to run if a private environment file is tracked, and leaves out virtual environments, `node_modules`, caches, and build output. It archives the latest committed snapshot, so commit the changes you want to share first.

## Rules

- Keep `.env` private and use `.env.example` as the shareable template.
- Never log passwords, authorization headers, JWTs, or request bodies.
- Use a new secret for each environment: local, staging, and production.
