# Companies

**Status:** Done (Phase 3): one company per founder, created at sign-up  
**Code:** `backend/app/features/companies/` · migration `0009_companies_users`  
**Last updated:** 2026-10-05

## What it is

A company is the founder's business. Everything the AI teams do belongs to one: runs, projects and their backlogs, and what standups report. Signing up creates it ([auth.md](auth.md)).

## How it works

- `AuthService.sign_up` creates the company, then the user.
- Runs and projects store `company_id`, and every API route filters by the signed-in founder's company.
- Events and backlog items are reached through their run or project, so they are scoped too.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Company` |
| `models.py` | `companies` table |
| `interfaces.py` | `CompanyRepository` (create, get, count) |
| `repository.py` · `memory_repository.py` | Postgres and in-memory |

## API

None of its own: the company comes back from `/auth/signup`, `/auth/login` and `/auth/me`.

## Data model

`companies`: `id` (uuid), `name`, `created_at`. `runs.company_id` and `projects.company_id` reference it (cascade on delete). `events` and `jobs` carry a `company_id` column that isn't filled yet; they're scoped through the run.

## Events

None.

## Dependencies

- **Used by:** `auth`

## Design decisions

- 2026-10-05 — One company per user to start; teammates and several companies per person come when founders ask.

## How to run and test

Covered by `uv run pytest app/features/auth`.

## Known limitations and gotchas

- No renaming, members, invites or roles yet.

## Troubleshooting

None yet.

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-05 | Created with sign-in |
