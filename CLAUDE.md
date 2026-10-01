# MedhKarm — AI Virtual Office

An AI workforce for solo founders, creators and small businesses in India: ready-made AI teams for specific jobs, all on one engine. The **software team** (PM, tech lead, developers, QA, DevOps) launches first, then a content and video team, then an operations team. The founder approves what matters and gets a daily standup. Current plan: [docs/08-product-plan-v2.md](docs/08-product-plan-v2.md); all docs: [docs/](docs/README.md).

## Stack

Next.js frontend · Python backend (uv, FastAPI, Pydantic) · Postgres on Supabase (pgvector) · LangGraph with Postgres checkpoints · LiteLLM · OpenHands developer engine · Docker sandbox locally (hosted sandbox chosen in Phase 2) · Langfuse. Details: [docs/04-tech-stack.md](docs/04-tech-stack.md).

## Code organisation (must follow)

Full rules and examples: [docs/05-architecture-and-conventions.md](docs/05-architecture-and-conventions.md).

- `frontend/` and `backend/` are separate projects; they talk only over the API.
- **Organise by feature.** Each feature has its own folder, with the same name on both sides:
  - `backend/app/features/<feature>/` → `router.py` (HTTP only), `schemas.py`, `service.py` (business rules), `repository.py` (all queries), `models.py`, `interfaces.py`, `dependencies.py`, `exceptions.py`, `tests/`
  - `frontend/src/features/<feature>/` → `components/`, `hooks/`, `api/`, `types.ts`, `index.ts` (public exports)
- `frontend/src/app/` holds thin Next.js route files that only render feature components.
- Shared plumbing: `backend/app/core/` and `backend/app/shared/`; `frontend/src/shared/`. Shared code never imports from features.
- A feature uses another feature only through its `service.py` / `index.ts` or an interface — never its internals.
- Split a file into a subfolder once it passes ~300 lines.

## SOLID (must follow)

- One file, one job; one component per file; one agent node per file.
- Services depend on Protocols (`interfaces.py`), not concrete classes; wire concrete classes in `dependencies.py`.
- New providers (models, sandboxes, developer engines, deploy targets) are new classes behind existing interfaces — don't edit the callers.
- Keep interfaces small and focused.

## Scalability

- API is stateless; long work runs in background workers, progress flows through the event log.
- Async I/O throughout the backend.
- Every table carries `company_id` with row-level security.
- Config from environment; never log secrets.

## Technical documentation (must follow)

Rules and index: [docs/technical/README.md](docs/technical/README.md).

- Every feature has a doc at `docs/technical/features/<feature>.md` (same name as its code folder), created from [`_TEMPLATE.md`](docs/technical/features/_TEMPLATE.md).
- A feature isn't done until its doc is written — in the same change as the code — and listed in the index.
- Any change to behaviour, API, data model, events or config updates the doc in the same change, with a changelog line.
- Cross-cutting pieces (overview, local setup, auth flow, event log, workflow engine, deployment) get their own doc in `docs/technical/`.
- Write for a newcomer: plain language first, then the code map, API, data model, decisions and troubleshooting.

## Quality

- Backend: `ruff`, `mypy --strict` (or pyright), `pytest`. Frontend: `eslint`, `prettier`, TypeScript strict, `vitest`, Playwright.
- Every feature ships with service-layer tests.
- `frontend/src/shared/api/generated/` is generated from FastAPI's OpenAPI spec — never edit it by hand.
