# Events (activity log)

**Status:** Done (Phase 1, step 1)  
**Code:** `backend/app/features/events/` · `frontend/src/features/events/` · migrations `backend/alembic/versions/0001_events.py`, `0002_events_time_index.py`  
**Last updated:** 2026-10-01

## What it is

The company's memory: everything that happens in a run, in order, as one plain sentence each. "The CTO wrote the plan", "Developer ran the tests (exit 1)", "Developer installed pytest", "QA: checks passed", "You approved the release". The animated office, the activity feed, the daily standup and cost tracking are all built by reading these events. Nothing else keeps its own record.

The log is **append-only**: the database refuses to change or delete an event, so it's a trustworthy audit trail.

## How it works

1. Features record events through a `RunRecorder`, a small helper bound to one run: `await recorder.record(actor, type, summary, data, tokens)`.
2. The recorder appends them to an `EventStore`: Postgres in real runs, memory in tests and evals.
3. If recording fails (database down), the error is logged and the run carries on. A missing log line must never break a customer's build.
4. The API, the CLI and later the office read them back in order: a list, totals, or a **live stream** (server-sent events) that sends each new event as it happens and ends when the run finishes.

**Who records what:**

| Recorded by | Events |
| --- | --- |
| `WorkflowService` (workflows) | `run.started`, `plan.created`, `task.assigned` (one per task: "Assigned “CSV export” to Isha”), `work.finished`, `review.finished` ("Approved …" or "Sent … back to Isha: …"), `check.finished` (QA: "Checks passed (tests, syntax, ruff)", "Checks failed: sent to Isha to fix" plus a `task.assigned`, "Stopped: the checks still fail"; `data.checks` has each check), `approval.requested`, `approval.decided`, `run.finished`; `model.used` for the CTO's plan and review calls |
| Develop node (workflows) | `work.started` |
| `WorkflowService.continue_run` (workflows) | `run.resumed` ("Picked up again after an interruption") when a worker carries on a run another worker didn't finish |
| Release gate (workflows) | `approval.decided` from `system` when the team's approval rules approve or reject on their own ("Approved the release by your rules: …"); `approval.requested` ends with the rules' reasons when a rule asked ([approvals.md](approvals.md)) |
| Repos (workflows) | `codebase.mapped` from `cto` after the project is mapped ("Read the project before planning: Existing project: 40 files…"); `changes.delivered` from `devops` with the pull request on a released repo run ([repos.md](repos.md)) |
| Build job handlers (worker) | `run.finished` with `status: error` ("Stopped: something went wrong") when a build runs out of retries |
| Developer engines | `tool.used` (one per tool call, e.g. "Wrote calc.py", "Ran `python -m pytest -q` (exit 0)"), `model.used` (one per model call, with tokens; OpenHands records its total once) |

Events about one developer's task carry `member` (e.g. "Isha") and `task_id` in `data` (`RunRecorder.with_context()`), so the office knows who to animate.

Token counts live **only** on `model.used` events, so summing `tokens` gives a run's true cost with no double counting.

A real run, from the CLI:

```
10:59:14  founder   run.started         Asked for: Create calc.py with add(a, b) and divide(a, b) ...
10:59:24  cto       plan.created        Wrote the plan
10:59:24  developer work.started        Started on the task
10:59:28  developer model.used          Thought about the next step  [866 tokens]
10:59:28  developer tool.used           Wrote calc.py
10:59:34  developer tool.used           Ran `python -m pytest -q` (exit 1)
10:59:40  developer tool.used           Ran `pip install pytest` (exit 0)
10:59:42  developer tool.used           Ran `python -m pytest -q` (exit 0)
10:59:46  developer work.finished       All tests passed for calc module and its tests.
10:59:46  qa        check.finished      Checks passed
10:59:46  cto       approval.requested  Waiting for your approval to release
11:00:00  founder   approval.decided    Approved the release: Looks good
11:00:00  system    run.finished        Released

20 events · 9,234 tokens
```

## Activity feed (frontend)

`frontend/src/features/events/`: `ActivityFeed` shows a run's events newest first, with the developer's own name ("Isha") or the role ("Kabir (CTO)"), times in IST and tokens. It starts from the events the server rendered and then follows `/runs/{run_id}/events/stream` in the browser (`EventSource`, one listener per event type). When the backend ends the stream (quiet for 10 minutes), the feed reconnects itself from the last event it has, every 3 s, instead of letting the browser restart from the beginning; it stops once `run.finished` arrives. Steps that can change the run's status (`approval.requested`, `approval.decided`, `run.finished`, `run.resumed`, `plan.created`) refresh the page around it, so the approval panel appears and disappears on its own. "Show model calls" reveals the `model.used` events, hidden by default. Helpers: `describeEvent.ts` (`actorLabel`, `mergeEvents`, `totalTokens`, `isFinished`).

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `EventType`, `Actor`, `NewEvent`, `Event`, `RunTotals`, `FINAL_TYPES` |
| `models.py` | `EventRow`: the `events` table |
| `interfaces.py` | `EventStore` Protocol: `append`, `list_for_run`, `totals_for_run`, and for the standup `run_ids_between` (runs active in a time window) and `latest_per_run` (each run's last event before a time) |
| `stores/sql_store.py` | `SqlEventStore`: Postgres, one short transaction per call |
| `stores/memory_store.py` | `InMemoryEventStore`: tests and evals |
| `service.py` | `RunRecorder` (writing, failure-safe) and `EventService` (reading, live stream) |
| `dependencies.py` | Wires `EventService` with the Postgres store for the API |
| `router.py` | HTTP endpoints |
| `app/workers/build_run.py` | `events <run_id>` command; passes the store to the graph and the workflow service |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/runs/{run_id}/events?after_id=0&limit=500` | Events in order; `after_id` returns only newer ones (limit 1–1000) | None yet |
| GET | `/runs/{run_id}/events/totals` | Number of events and total tokens | None yet |
| GET | `/runs/{run_id}/events/stream?after_id=0` | Live server-sent events (`EventSource` in the browser). Each message has `id`, `event` (the type) and `data` (the event as JSON). Ends after `run.finished`, or after 10 minutes without news | None yet |

## Data model

Table `events` (migration `0001_events`, which also enables the `vector` extension):

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigint, primary key | Increases with every event: the order things happened |
| `occurred_at` | timestamptz | Set by the database. Index `ix_events_occurred_at` (migration `0002`) for time-window queries |
| `company_id` | uuid, nullable | Becomes required, with row-level security, when the companies feature lands |
| `run_id` | varchar(100) | Index `(run_id, id)` for fast "events of this run after X" |
| `actor` | varchar(40) | `founder`, `system`, or a team role id: `pm`, `cto`, `developer`, `qa`, `devops` |
| `type` | varchar(60) | See `EventType` |
| `summary` | text | One sentence, max 500 characters |
| `data` | jsonb | Details: plan text, files changed, tool output, gate, … |
| `tokens` | integer | Only on `model.used` |

Trigger `events_no_update_or_delete` raises "events are append-only" on any `UPDATE` or `DELETE`.

## Events

This feature *is* the event log. Other features call `RunRecorder.record()`.

## Dependencies

- **Used by:** `workflows`, `developer_engine` (through `RunRecorder` and `EventStore`); `standups` (reads through its own `ActivityLog` Protocol, which `EventStore` satisfies)
- **External services:** Postgres
- **Config:** `DATABASE_URL`

## Design decisions

- 2026-10-01 — One append-only table for everything, enforced by a database trigger, not just by code. Every screen reads from it, so the office, feed and standup can never disagree.
- 2026-10-01 — Recording never raises: losing a log line is better than failing a customer's build.
- 2026-10-01 — Live stream by polling the database every second, not in-process pub/sub: it works with any number of API and worker processes without extra infrastructure. Revisit (Postgres `LISTEN/NOTIFY` or Supabase Realtime) if latency or load needs it.
- 2026-10-01 — Tokens only on `model.used` events, so totals are exact.
- 2026-10-01 — Step-level events are recorded by `WorkflowService`, not inside graph nodes, because LangGraph re-runs the approval node on resume; recording there would duplicate events.

## How to run and test

- Apply the migration: `uv run alembic upgrade head`
- Unit tests (in-memory store): `uv run pytest app/features/events`
- Database tests: `uv run pytest -m integration app/features/events`
- See a run's log: `uv run python -m app.workers.build_run events <run_id>`
- Live in a terminal: `curl -N http://127.0.0.1:8000/runs/<run_id>/events/stream`

## Known limitations and gotchas

- No authentication or company scoping yet: anyone who can reach the API can read any run's log. Comes with sign-in and the companies feature.
- Because events can't be deleted, test rows stay in a local database. Use unique run ids in tests; reset a local database with `docker compose down -v`.
- The OpenHands engine records totals only, not each of its actions.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `relation "events" does not exist` | Migration not applied | `uv run alembic upgrade head` |
| "events are append-only" error | Something tried to change or delete an event | By design; append a new event instead |
| Run works but its log is empty | Database unreachable (recording failures are only logged) | Check `DATABASE_URL` and the worker's warnings |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-05 | `project.scaffolded` from `devops`: the stack and the starter set up for a new project |
| 2026-10-04 | QA's `check.finished` lists each check (`data.checks`) and says who got the fix task; QA records `task.assigned` for it |
| 2026-10-04 | `deploy.finished` events from `devops` |
| 2026-10-04 | `security.finished` events and the `security` actor (Vikram) |
| 2026-10-01 | `codebase.mapped` and `changes.delivered` event types; `changes.delivered` refreshes the run page |
| 2026-10-01 | Live activity feed in the admin page (frontend `events` feature) |
| 2026-10-01 | `approval.decided` by `system` for decisions made by approval rules; reasons in `approval.requested` |
| 2026-10-01 | `run.resumed` now recorded (run picked up after an interruption); `run.finished` can carry status `error` |
| 2026-10-01 | `run_ids_between` and `latest_per_run` store queries and an `occurred_at` index (migration `0002`) for the daily standup; `InMemoryEventStore.now` lets tests set event times |
| 2026-10-01 | `task.assigned` and `review.finished` events; `member`/`task_id` context on task events; CTO tokens recorded |
| 2026-10-01 | Created: append-only events table, recorder, store, API with live stream, CLI view; workflow and engines record events |
