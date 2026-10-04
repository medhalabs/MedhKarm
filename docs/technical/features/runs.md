# Runs (build runs over HTTP)

**Status:** Done (Phase 1, step 5): start, list, get and approve runs over HTTP  
**Code:** `backend/app/features/runs/` · `frontend/src/features/runs/` · pages `frontend/src/app/admin/` · migration `backend/alembic/versions/0003_jobs_and_runs.py`  
**Last updated:** 2026-10-01

## What it is

The founder's handle on a build: ask for something, see where it stands, and approve or reject the release. Each call returns at once, because the work happens in background workers ([jobs.md](jobs.md)). Progress arrives through the activity log (`/runs/{run_id}/events` and its live stream, [events.md](events.md)). This replaces the command line (`build_run`) as the way runs start and get approved.

## How it works

```mermaid
stateDiagram-v2
    [*] --> queued: POST /runs
    queued --> running: worker claims build.start
    running --> waiting_for_approval: tests passed, release gate
    running --> failed: final checks failed
    running --> error: something broke, retries ran out
    waiting_for_approval --> queued: POST /runs/{id}/approval
    queued --> running: worker claims build.resume
    running --> released: approved
    running --> rejected: not approved
```

1. `POST /runs` with the request and test command → a `runs` row (`queued`) and a `build.start` job. The answer is the run, with its id.
2. A worker runs the graph and keeps the row's `status` up to date. At the release gate it stores what the founder is asked (`gate`: summary, files changed, test output) and sets `waiting_for_approval`.
3. `POST /runs/{id}/approval` with `approved` and optional `feedback`. This moves the run from `waiting_for_approval` to `queued` in one conditional update, so a double click or two people approving at once queues only one decision (the other gets 409), and queues a `build.resume` job.
4. A worker resumes the graph with the decision and sets `released` or `rejected`.

## The admin page (frontend)

A bare page to start runs, watch them and approve releases: http://localhost:3000/admin (no sign-in yet; local only).

| Page | What it shows |
| --- | --- |
| `/admin` | A form to start a run (request, optional GitHub repo and branch, test command), and every run with its status. Refreshes every 5 s while a run is queued or working |
| `/admin/runs/[runId]` | The request, status and any error; when waiting, the **approval panel** (why you're asked, summary, files, tokens, QA's test output, an optional note, Approve / Reject); the live activity feed ([events.md](events.md)) |
| `/admin/standup` | The daily standup ([standups.md](standups.md)) |

Forms are React forms with **server actions** (`api/actions.ts`): the Next.js server checks the input (`parseForms.ts`), calls the backend (`POST /runs`, `POST /runs/{id}/approval`) and then opens the new run or refreshes the page. Errors from the backend (e.g. 409 already decided) show under the form.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Run`, `RunStatus`, `StartRun`, `ApprovalDecision` |
| `interfaces.py` | `RunRepository` Protocol |
| `models.py` | `RunRow`: the `runs` table |
| `repository.py` | `SqlRunRepository` |
| `memory_repository.py` | `InMemoryRunRepository`: tests |
| `service.py` | `RunService`: start (row + job), decide (guarded), get, list, `set_status` for workers; job kind names `START_JOB`, `RESUME_JOB` |
| `exceptions.py` | `RunNotFoundError` (404), `RunNotWaitingError` (409) |
| `dependencies.py`, `router.py` | API |
| `frontend/…/runs/types.ts` | `Run`, `RunStatus`, `Gate` (mirror the backend schemas) |
| `frontend/…/runs/describeStatus.ts` | Status label, colour and whether it's still active; `shortRequest()` |
| `frontend/…/runs/parseForms.ts` | Checks the start and approval forms |
| `frontend/…/runs/api/` | `listRuns`, `getRun`, server actions `startRunAction`, `decideAction` |
| `frontend/…/runs/components/` | `RunsOverview`, `RunsTable`, `RunStatusBadge`, `StartRunForm`, `RunPage`, `RunHeader`, `ApprovalPanel` |
| `frontend/src/app/admin/` | Thin route files and the admin layout (nav: Runs, Standup) |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | `/runs` | Start a run: `{"request": "...", "test_command": "pytest -q", "repo": {"url": "https://github.com/owner/name", "branch": null}}` → 202 with the run. `repo` is optional ([repos.md](repos.md)); without it, `create_repo` (default `true`) and `new_repo_name` ask for a new private repository on release; `test_command` is optional: `pytest -q` for a new project, detected from the project with a repo | None yet |
| GET | `/runs?limit=50` | Runs, newest first (limit 1–200) | None yet |
| GET | `/runs/{run_id}` | One run: status, `gate` while waiting, `error` if it broke | None yet |
| POST | `/runs/{run_id}/approval` | `{"approved": true, "feedback": ""}` → 202 | None yet |

Errors: 404 `run_not_found`; 409 `run_not_waiting_for_approval`; 422 for an empty or over-long request. The activity log for a run stays at `/runs/{run_id}/events` (events feature).

```bash
curl -X POST 127.0.0.1:8000/runs -H 'content-type: application/json' \
  -d '{"request": "Create greet.py with greet(name) and pytest tests", "test_command": "python -m pytest -q"}'
curl 127.0.0.1:8000/runs/<run_id>
curl -X POST 127.0.0.1:8000/runs/<run_id>/approval -H 'content-type: application/json' -d '{"approved": true}'
```

## Data model

| Table | Key columns | Notes |
| --- | --- | --- |
| `runs` | `id` (same as the LangGraph thread id and the events' `run_id`), `request`, `test_command` (empty: detected when the run starts), `repo` (jsonb, the GitHub repository), `delivery` (jsonb, the pull request with the released work), `status`, `gate` (jsonb: question, `reasons` and `rules` from the approval rules, summary, files, tokens, tests), `error`, `created_at`, `updated_at`, `company_id` (nullable) | Index on `created_at`. The detail of a run lives in the event log and the checkpoint; this row is its current status, for lists and approvals |

## Events

None of its own. The workflow records the run's events ([workflows.md](workflows.md)).

## Dependencies

- **Other features used:** `jobs` (through the `JobQueue` interface)
- **Used by:** the worker's build handlers (status updates)
- **External services:** Postgres
- **Config:** `BUILD_MAX_ATTEMPTS`

## Design decisions

- 2026-10-01 — A `runs` table, although the checkpoint and the event log hold everything: listing runs and checking "is it waiting?" must not mean opening LangGraph checkpoints, and the API stays free of LangGraph.
- 2026-10-01 — Approval is a guarded status change (`waiting_for_approval` → `queued`) plus a job with a unique key, so one decision wins.
- 2026-10-01 — The founder's request and test command go into the row, not only the job, so a retry or another worker always has them.

## How to run and test

- Run the API and a worker (see [jobs.md](jobs.md)), then use the `curl` lines above.
- Tests: `uv run pytest app/features/runs tests/test_build_jobs.py`; database: `uv run pytest -m integration app/features/runs` (deletes the run it creates). Frontend: `npm test` (`describeStatus`, `parseForms`).
- Admin page: start the API, a worker and `npm run dev`, then open http://localhost:3000/admin.

## Known limitations and gotchas

- No sign-in or companies yet: anyone who can reach the API or the admin page can start and approve runs (server actions are reachable by POST too). Keep both on localhost until auth lands.
- The default test command `pytest -q` relies on the default sandbox image (`medhkarm-sandbox:3`), which has pytest. With another `SANDBOX_IMAGE`, install the test tools in the test command.
- Cancelling a running build isn't supported yet.
- Runs started from the command line (`build_run start`) have no `runs` row, so they don't appear in `GET /runs` (their events and standup still work).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Stays `queued` | No worker running | `uv run python -m app.workers.main` |
| `error` | Retries ran out (model or sandbox kept failing) | `error` on the run; `last_error` on its job |
| 409 on approval | Already decided, or not at the gate yet | `GET /runs/{id}` for its status |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-01 | New projects: `create_repo` / `new_repo_name` on start, `new_repo` on runs (migration `0005`); admin form checkbox and name; run page shows the created repository |
| 2026-10-01 | Runs on an existing GitHub repository: optional `repo` on start, `repo` and `delivery` on runs (migration `0004`), test command optional; admin form and run page show the repo and the pull request ([repos.md](repos.md)) |
| 2026-10-01 | Admin page: start, list, watch and approve runs in the browser |
| 2026-10-01 | `gate` carries the approval rules' reasons; runs the rules approve or reject never wait ([approvals.md](approvals.md)) |
| 2026-10-01 | Created: runs table, start/list/get/approve API, statuses kept up to date by workers |
