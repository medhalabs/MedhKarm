# Backend

FastAPI API and background workers for MedhKarm. Setup and commands: [docs/technical/local-setup.md](../docs/technical/local-setup.md). Structure and rules: [docs/05-architecture-and-conventions.md](../docs/05-architecture-and-conventions.md).

```
app/
├── main.py      creates the app, registers each feature's router
├── core/        config, database, errors, logging — no business logic
├── shared/      small generic helpers (SQLAlchemy Base, mixins)
├── features/    one folder per feature (router, schemas, service, repository, models, tests)
└── workers/     background worker entry point
alembic/         database migrations
tests/           whole-app tests
```

| Command | What it does |
| --- | --- |
| `uv run uvicorn app.main:app --reload` | API on http://127.0.0.1:8000 (docs at `/docs`) |
| `uv run pytest` | Tests |
| `uv run ruff check . && uv run ruff format .` | Lint and format |
| `uv run mypy app tests` | Strict type check |
| `uv run lint-imports` | Layer rules: entry points > features > shared > core |
| `uv run alembic revision --autogenerate -m "..."` / `uv run alembic upgrade head` | Migrations |
