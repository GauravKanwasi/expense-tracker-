# Contributing

Run `pytest -q -p no:cacheprovider` and `npm.cmd run build` from `frontend/` before committing.

Use short, descriptive commit messages that explain the change and its reason. A useful pattern is:

```text
type(scope): concise change
```

Examples: `fix(budgets): keep overspending out of available cash` and `feat(auth): revoke access tokens on logout`.

Do not commit `.env`, database dumps, virtual environments, `node_modules`, or build output.
