# Inbox (the CEO inbox)

**Status:** Done (Phase 3): approvals, the PM's questions, blocked work and the team's replies in one place; tried live Oct 5, 2026  
**Code:** `backend/app/features/inbox/` · `frontend/src/features/inbox/` · page `/admin/inbox`  
**Last updated:** 2026-10-05

## What it is

The founder's one screen for everything the team needs from them:
- **Releases waiting for approval:** the rules' reasons, security warnings and a preview link, with **Approve** / **Reject** right there.
- **Mira's open questions** on each project. Answers are kept for every later plan, with an option to have her plan again now.
- **Blocked backlog items** (rejected, failed or cancelled), with **Retry** / **Skip**.
- **The latest replies from the team** to the founder's messages ([messages.md](messages.md)).

The nav shows **Inbox** with a count of what needs the founder.

## How it works

1. `InboxService.for_company` reads what's already stored. The inbox stores nothing of its own.
   - **Approvals:** the company's runs that are `waiting_for_approval`, from their `gate`.
   - **Questions:** each live project's `questions`.
   - **Blocked:** each live project's items in `blocked`, with their `note`.
   - **Replies:** the 5 latest messages from agents.
2. **The count** = approvals + unanswered questions + blocked items. Replies are for reading, so they aren't counted.
3. **Acting on an item** uses the usual endpoints: `/runs/{id}/approval`, `/projects/{id}/answers`, `/projects/{id}/items/{item}/retry|skip`.
4. **Answers** (`POST /projects/{id}/answers`) are added to `projects.answers`, and the questions they answer leave the list. Mira's planning brief includes every answer ("follow them"). With `replan: true` she plans again at once.

## Code map

| File | Responsibility |
| --- | --- |
| `inbox/schemas.py` | `Approval`, `Questions`, `Blocked`, `Inbox` (`count`), `InboxCount` |
| `inbox/interfaces.py` | `RunsReader`, `ProjectsReader`, `MessagesReader` |
| `inbox/service.py` | `InboxService.for_company` |
| `inbox/router.py` | `/inbox`, `/inbox/count` |
| `projects/service.py` · `router.py` | `answer()`, `POST /projects/{id}/answers` |
| `frontend/…/inbox/` | `InboxPage`, `AnswerForm`, server actions, `getInboxCount` (nav badge) |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/inbox` | `{approvals, questions, blocked, replies}` for the caller's company | Bearer |
| GET | `/inbox/count` | `{count}` | Bearer |
| POST | `/projects/{id}/answers` | `{answers: [{question, answer}], replan}` → the project | Bearer, own project |

## Data model

`projects.answers` (jsonb, migration 0010): `[{question, answer}]`, kept in order.

## Events

None of its own.

## Dependencies

- **Uses:** `runs`, `projects` and `messages` services (through `interfaces.py`), `auth` (`SignedIn`)

## Design decisions

- 2026-10-05 — **Built from existing records, nothing duplicated:** an item leaves the inbox as soon as it's handled anywhere (run page, project page, inbox).
- 2026-10-05 — **Answers persist and steer every later plan**, rather than being one-off edits to the goal.

## How to run and test

- `uv run pytest app/features/inbox app/features/projects/tests/test_service.py`
- Live: `/admin/inbox` after signing in.

## Known limitations and gotchas

- One request per live project to find blocked items: fine for tens of projects, not for hundreds.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The Inbox count shows 0 but there's work | The backend isn't reachable | The count hides errors; open `/admin/inbox` to see the error |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-06 | "Plans to read and approve": blueprints that are ready, counted in the badge |
| 2026-10-05 | Restyled with the shared shell, page header and cards |
| 2026-10-05 | Created: approvals, PM questions with answers, blocked items, team replies, nav count |
