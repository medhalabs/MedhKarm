# Architecture and coding conventions

Decided Oct 1, 2026. Every change to the codebase follows these rules. The short version lives in [CLAUDE.md](../CLAUDE.md); this file has the full layout, examples and reasons.

## Goals

1. **Find code by feature.** Everything about approvals lives in one folder on each side, so fixing an approvals bug means opening two folders, not ten.
2. **Change one thing in one place.** Each file has one job (SOLID), so a change doesn't spread across the codebase.
3. **Grow without rewrites.** New features are new folders; new providers (models, sandboxes, deploy targets) are new classes behind existing interfaces.

## Repository layout

```
MedhKarm/
├── frontend/          Next.js app (TypeScript)
├── backend/           FastAPI app + agent workers (Python, uv)
├── docs/              Plans, decisions, conventions
└── CLAUDE.md          Rules for anyone (human or AI) writing code here
```

Frontend and backend are fully separate projects: their own dependencies, their own tests, their own Dockerfile. They talk only over the HTTP/WebSocket API.

## Feature list

The same feature names are used on both sides, so `frontend/src/features/approvals` and `backend/app/features/approvals` are the two halves of one feature.

| Feature | What it owns |
| --- | --- |
| `health` | API health check; the reference example of the feature pattern |
| `auth` | Sign-in, sign-up, sessions (via Supabase) |
| `companies` | The founder's company: name, settings, members |
| `projects` | An app being built: idea, status, repo link |
| `teams` | Team templates: roles, instructions, tools, models, workflow, checker |
| `workflows` | LangGraph graphs, runs, checkpoints, gates |
| `tasks` | Task board items and their lifecycle |
| `approvals` | CEO inbox: gates and approval rules |
| `events` | Append-only event log and live streaming |
| `office` | The office floor, meeting-room feed (frontend-heavy; reads `events`) |
| `reports` | Milestone updates and weekly reports |
| `models` | LLM providers, API keys, model picker, cost tracking |
| `sandbox` | Isolated sandbox per project: Docker locally, a hosted sandbox from Phase 2 |
| `developer_engine` | OpenHands (and later Claude Agent SDK) behind one interface |
| `integrations` | GitHub, Vercel, Supabase (customer's), MCP servers |
| `billing` | Plans, usage limits, Stripe |
| `evals` | 20 eval tasks (in `backend/evals/`), validator, runner and reports |

New features get a new folder with the same name on both sides. Names are plural nouns, lowercase, `snake_case` in Python and `kebab-case` folders in the frontend (`developer-engine`).

## Backend layout

```
backend/
├── pyproject.toml                 uv project
├── alembic/                       database migrations
├── app/
│   ├── main.py                    creates the FastAPI app, includes each feature's router
│   ├── core/                      shared plumbing, no business logic
│   │   ├── config.py              settings from environment (pydantic-settings)
│   │   ├── database.py            async engine, session factory
│   │   ├── security.py            verify Supabase token, current user
│   │   ├── errors.py              base exception types + handlers
│   │   └── logging.py
│   ├── shared/                    small, generic helpers used by many features
│   │   ├── base_model.py          SQLAlchemy Base, id/timestamps mixin
│   │   ├── pagination.py
│   │   └── types.py
│   ├── features/
│   │   ├── auth/
│   │   ├── projects/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          HTTP endpoints only: parse input, call service, return output
│   │   │   ├── schemas.py         Pydantic request/response models
│   │   │   ├── service.py         business rules; no HTTP, no SQL
│   │   │   ├── repository.py      all database access for this feature
│   │   │   ├── models.py          SQLAlchemy tables
│   │   │   ├── interfaces.py      Protocols this feature depends on (if any)
│   │   │   ├── dependencies.py    FastAPI Depends() wiring
│   │   │   ├── exceptions.py      feature errors (ProjectNotFound, ...)
│   │   │   └── tests/
│   │   ├── models/                LLM providers
│   │   │   ├── interfaces.py      LLMProvider Protocol
│   │   │   ├── providers/
│   │   │   │   ├── litellm_provider.py
│   │   │   │   └── fake_provider.py   for tests
│   │   │   └── ...
│   │   ├── workflows/
│   │   │   ├── graphs/            one file per LangGraph graph
│   │   │   ├── nodes/             one file per node (pm.py, cto.py, qa.py, ...)
│   │   │   ├── state.py           graph state types
│   │   │   └── ...
│   │   └── ...
│   └── workers/
│       └── main.py                background worker entry point (runs graphs)
└── tests/                         cross-feature and end-to-end tests
```

Not every feature needs every file. Start with `router.py`, `schemas.py`, `service.py`; add `repository.py` and `models.py` when it stores data. When a file grows past about 300 lines, split it into a subfolder (for example `service.py` → `service/create.py`, `service/update.py`).

### The layers and who may call whom

```
router  →  service  →  repository  →  database
              ↓
         interfaces (Protocols)  ←  implemented by providers / other features
```

- **router** knows HTTP. It never touches the database or contains business rules.
- **service** holds the rules. It never imports FastAPI, never writes SQL.
- **repository** is the only place with queries.
- A feature uses another feature **only through that feature's `service.py` (or an interface)**, never its repository, models or internals.

## Frontend layout

```
frontend/
├── package.json
├── src/
│   ├── app/                       Next.js routes only — thin files that render feature components
│   │   ├── (auth)/login/page.tsx          → renders <LoginForm /> from features/auth
│   │   ├── (dashboard)/projects/page.tsx  → renders <ProjectList /> from features/projects
│   │   └── layout.tsx
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/        LoginForm.tsx, SignUpForm.tsx
│   │   │   ├── hooks/             useSession.ts
│   │   │   ├── api/               calls to the backend for this feature
│   │   │   ├── types.ts
│   │   │   └── index.ts           the feature's public exports
│   │   ├── projects/
│   │   ├── approvals/
│   │   ├── office/
│   │   └── ...
│   └── shared/
│       ├── ui/                    generic components: Button, Dialog, Table
│       ├── api/
│       │   ├── client.ts          fetch wrapper with auth
│       │   └── generated/         TypeScript client generated from FastAPI's OpenAPI — never edited by hand
│       ├── hooks/
│       └── lib/                   small generic helpers
└── tests/                         end-to-end (Playwright)
```

The example from the brief, `frontend > login > login.tsx` / `backend > login > login.py`, maps to:

- `frontend/src/features/auth/components/LoginForm.tsx` (plus a thin route at `frontend/src/app/(auth)/login/page.tsx`, because Next.js requires routes under `app/`)
- `backend/app/features/auth/router.py` + `service.py`

Rules:

- Route files in `app/` stay under about 30 lines: fetch nothing themselves, just render a feature component.
- Other code imports a feature only from its `index.ts`, never from deep inside it. The one other public entry is `client.ts`: browser-safe exports (helpers, types) for client components, because `index.ts` may export server-only code (the API client reads the session cookie). ESLint enforces both.
- **Look and feel:** shared building blocks in `frontend/src/app/globals.css` (`card`, `card-header`, `card-title`, `btn-primary`, `btn-secondary`, `field`) and `frontend/src/shared/ui/` (`PageHeader`, `Stat`, `NavLink`, `Markdown`, `Collapsible`, icons). New pages use them instead of one-off styles. Indigo is the brand colour; the Geist font is used throughout.
- `shared/` never imports from `features/`.
- One component per file; the file is named after the component (`LoginForm.tsx`).

## SOLID, applied here

| Principle | What it means in this codebase |
| --- | --- |
| **Single responsibility** | One file, one job: router = HTTP, service = rules, repository = queries. One agent node per file. One React component per file. |
| **Open/closed** | Add a model provider, sandbox, deploy target or developer engine by writing a new class that implements the existing interface and registering it — no edits to the code that uses it. |
| **Liskov substitution** | Every implementation of an interface must be usable wherever the interface is expected: `FakeLLMProvider` in tests behaves like `LiteLLMProvider` in production (same inputs, same kinds of outputs and errors). |
| **Interface segregation** | Small, focused Protocols: `SandboxRunner` (run commands) is separate from `SandboxFiles` (read/write files). A consumer depends only on what it uses. |
| **Dependency inversion** | Services depend on Protocols in `interfaces.py`, not on concrete classes. Concrete classes are wired in `dependencies.py` (API) or the worker's setup. That's what lets us swap OpenHands for the Claude Agent SDK, or the local Docker sandbox for a hosted one. |

Example of the pattern:

```python
# backend/app/features/developer_engine/interfaces.py
class DeveloperEngine(Protocol):
    async def run_task(self, task: DevTask, repo: RepoRef) -> DevResult: ...

# backend/app/features/developer_engine/engines/openhands_engine.py
class OpenHandsEngine:
    async def run_task(self, task: DevTask, repo: RepoRef) -> DevResult: ...

# backend/app/features/workflows/nodes/developer.py
async def developer_node(state: BuildState, engine: DeveloperEngine) -> BuildState:
    result = await engine.run_task(state.current_task, state.repo)
    ...
```

## Scalability rules

- **Features don't reach into each other.** Cross-feature calls go through the other feature's service or an interface. Side effects that many features care about (task finished, gate approved) are published as events; the interested features react.
- **Stateless API.** No state kept in the API process; everything is in Postgres or Redis, so we can run many API and worker processes.
- **Long work runs in workers**, never in a request. The API starts a run and returns; progress arrives through events.
- **Async I/O throughout** the backend (async SQLAlchemy, httpx).
- **Every table has a `company_id`** (tenant) and row-level security, so data never leaks between customers.
- **Config from environment**, never hard-coded; secrets never logged.
- **Boundaries are checked by tools**, not just by review: `import-linter` in Python and `eslint-plugin-boundaries` in TypeScript fail the build if a feature imports another feature's internals.

## Code style and quality

| Area | Backend | Frontend |
| --- | --- | --- |
| Formatting and lint | `ruff` (format + lint) | `eslint` + `prettier` |
| Types | `mypy --strict` or `pyright` | TypeScript `strict: true` |
| Tests | `pytest`, tests next to the feature in `tests/` | `vitest` next to the feature; Playwright end-to-end |
| Naming | `snake_case` files and functions, `PascalCase` classes | `PascalCase.tsx` components, `camelCase.ts` hooks and helpers |

- Functions stay short (aim for under 40 lines) and do one thing.
- No business logic in routers, route files or React components beyond display logic.
- Every new feature ships with tests for its service layer.
- Errors are specific (`ProjectNotFound`, not a bare `Exception`) and mapped to HTTP codes in one place (`core/errors.py`).

## Checklist for a new feature

1. Create `backend/app/features/<name>/` with `router.py`, `schemas.py`, `service.py` (+ `repository.py`, `models.py` if it stores data).
2. Register the router in `backend/app/main.py`; add an Alembic migration if tables changed.
3. Regenerate the frontend API client.
4. Create `frontend/src/features/<name>/` with `components/`, `api/`, `index.ts`; add thin route files under `app/` if it has pages.
5. Add tests on both sides.
6. Add the feature to the table above.
7. Write `docs/technical/features/<name>.md` from the template and add it to the index in `docs/technical/README.md`. The feature isn't done until this is.
