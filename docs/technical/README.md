# Technical documentation

Knowledge transfer for anyone working on the code: what each part is, how it works, where its code lives, and why it's built that way. Start with the system overview, then read the feature you're working on.

## Rules

- **Every feature has a doc** at `features/<feature>.md`, named exactly like its code folder, created from [features/_TEMPLATE.md](features/_TEMPLATE.md).
- **A feature isn't done until its doc is.** The doc is written in the same change as the code.
- **Any change to behaviour, API, data model, events or config updates the doc** in the same change, with a changelog line.
- **Cross-cutting pieces** (setup, deployment, auth flow, the event log, the workflow engine) get their own doc in this folder.
- Write for a newcomer: plain language first, then detail. Diagrams (Mermaid) wherever a flow branches or crosses services.

## Index

### System

| Doc | What it covers |
| --- | --- |
| [overview.md](overview.md) | How frontend, backend, workers, database and external services fit together |
| [local-setup.md](local-setup.md) | Getting the project running on a new machine |

### Features

| Feature | Doc | Status |
| --- | --- | --- |
| health | [features/health.md](features/health.md) | Done |
| models | [features/models.md](features/models.md) | Done (Phase 0) |
| sandbox | [features/sandbox.md](features/sandbox.md) | Docker and OpenHands agent server, local development |
| developer_engine | [features/developer_engine.md](features/developer_engine.md) | Built-in and OpenHands engines done |
| workflows | [features/workflows.md](features/workflows.md) | Build graph with swappable checking step |
| teams | [features/teams.md](features/teams.md) | Team templates; software team |
| events | [features/events.md](features/events.md) | Activity log: append-only, API with live stream, live feed in the admin page |
| evals | [features/evals.md](features/evals.md) | 20 tasks, validator, runner, reports |
| standups | [features/standups.md](features/standups.md) | Daily standup from the activity log: API, CLI, admin page, sent each morning by the worker |
| runs | [features/runs.md](features/runs.md) | Start, list and approve build runs over HTTP and in the admin page (`/admin`) |
| jobs | [features/jobs.md](features/jobs.md) | Postgres job queue and the worker: builds and the morning standup |
| integrations | [features/integrations.md](features/integrations.md) | MCP servers as agent tools, with per-role limits; `python_docs` server |
| approvals | [features/approvals.md](features/approvals.md) | Approval rules at the release gate: ask, approve or reject, with reasons |
