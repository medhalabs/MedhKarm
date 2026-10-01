# System overview

**Last updated:** 2026-10-01

How the pieces of MedhKarm fit together. This describes what exists today; planned parts are marked *(planned)*.

## Components

```mermaid
flowchart LR
    Browser["Founder's browser"] --> FE["Frontend<br/>Next.js :3000"]
    FE -->|HTTP JSON| API["Backend API<br/>FastAPI :8000"]
    API --> DB[("Postgres + pgvector<br/>:5442 local / Supabase")]
    API -.->|enqueue jobs| Redis[("Redis :6379")]
    Redis -.-> Worker["Workers<br/>LangGraph build runs"]
    Worker --> DB
    Worker --> Ollama["Ollama Cloud<br/>via LiteLLM"]
    Worker --> Sandbox["Sandbox per run<br/>Docker or OpenHands agent server"]
    Worker -.-> Ext["GitHub · Vercel (planned)"]
```

Solid lines exist today; dotted lines are planned. Build runs are started from the command line (`app/workers/build_run.py`) until the job queue arrives in Phase 1.

| Component | Where | Status | Role |
| --- | --- | --- | --- |
| Frontend | `frontend/` | Running | UI. Server components call the API through `src/shared/api/client.ts` |
| Backend API | `backend/app/` | Running | HTTP API; one router per feature, assembled in `app/main.py` |
| Workers | `backend/app/workers/` | Build runs from the command line | Long-running work (agent runs, sandboxes, evals); queue chosen in Phase 1 |
| Build workflow | `backend/app/features/workflows/` | Running | LangGraph graph: plan → develop → verify → release gate → finish, checkpointed in Postgres |
| Models | `backend/app/features/models/` | Running | LiteLLM; default `gpt-oss:120b` on Ollama Cloud |
| Sandbox | `backend/app/features/sandbox/` | Running (Docker) | One isolated container per build run: plain Docker, or an OpenHands agent server |
| Developer engine | `backend/app/features/developer_engine/` | Running | Built-in tool loop or OpenHands, chosen by `DEVELOPER_ENGINE` |
| Postgres | `docker-compose.yml` locally, Supabase in production | Running locally | All data, LangGraph checkpoints, embeddings (pgvector) |
| Redis | `docker-compose.yml` | Running locally, unused yet | Job queue and caching |

## How a request flows today

```mermaid
sequenceDiagram
    participant B as Browser
    participant FE as Next.js (server component)
    participant API as FastAPI
    B->>FE: GET /
    FE->>API: GET /health (via shared/api/client.ts)
    API->>API: router → HealthService
    API-->>FE: {"status":"ok", ...}
    FE-->>B: HTML with "Backend OK · ..."
```

Every future feature follows the same path: route file → feature component → feature `api/` → shared client → backend feature router → service → repository → database.

## Code structure

Both sides are organised by feature, with the same feature names on each side. Full rules: [05-architecture-and-conventions.md](../05-architecture-and-conventions.md).

- **Backend layers** (checked by `import-linter`): `app.main` / `app.workers` → `app.features` → `app.shared` → `app.core`. Lower layers never import higher ones.
- **Frontend boundaries** (checked by ESLint): code imports a feature only via `@/features/<name>`; `src/shared/` never imports features.

## Configuration

| Side | File | Key settings |
| --- | --- | --- |
| Backend | `backend/.env` (from `.env.example`), read by `app/core/config.py` | `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `ENVIRONMENT`, `DEFAULT_MODEL`, `OLLAMA_API_BASE`, `OLLAMA_API_KEY`, `SANDBOX_IMAGE`, `DEVELOPER_ENGINE`, `BUILTIN_MAX_STEPS`, `OPENHANDS_SERVER_IMAGE`, `OPENHANDS_MAX_ITERATIONS`, `EVAL_SANDBOX_IMAGE` |
| Frontend | `frontend/.env.local` (from `.env.example`) | `NEXT_PUBLIC_API_URL` |

## Features

See the index in [README.md](README.md).
