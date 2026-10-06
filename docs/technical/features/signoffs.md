# Sign-offs (the release sign-off card)

**Status:** Built (Phase 3): who signed off a release and what they say, on the run page and in the inbox; tried live through the API on Oct 6, 2026. The card wasn't opened in a browser yet (G-48).  
**Code:** `backend/app/features/signoffs/` · `frontend/src/features/signoffs/`  
**Last updated:** 2026-10-06

## What it is

Before approving a release the founder sees one card: every member of the team, and their word.

| Who | What they say |
| --- | --- |
| Developers (Isha, Arjun…) | "Built 3 tasks (Arjun, Isha)" |
| Kabir, CTO | "Reviewed 3 tasks, sent 2 back for changes, all approved", or "moved on from 1 with open comments" |
| Tara, QA | The latest checks and browser test: "Checks passed (tests, lint) · Browser test passed (…)" |
| Vikram, security | "No security problems found", warnings, or the block |
| Neel, DevOps | "Preview ready" with the link; the pull request or repository |
| Lekha, documentation | "Added to the changelog" with the entry |
| You | "Waiting for your approval", "You approved the release", or "Approved by your rules" |

Each line has a mark: signed off ✓, signed off with notes !, problem ✕, not yet …, or not part of this run –. The header counts them ("5 of 6 signed off", or "1 problem to look at").

It's on the run page (while waiting, and after release, rejection or failure) and, in short form, on each approval in the inbox.

## How it works

`GET /runs/{id}/signoffs` reads the run's activity log and `build()` works each line out. Nothing is stored, so the card is always what the log says.
- **Only the latest check counts:** a failed check that a developer then fixed shows the later pass.
- **Send-backs are shown honestly:** Kabir's line says how many tasks went back for changes.
- **Not yet vs. not part of this run:** a step with no events says "Not yet" while the run is working, and "Not part of this run" once it is at the gate or over, so a run still building doesn't look like it skipped security.
- **Names** come from the software team template (`display_names[0]`).

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Signoff` (role, name, title, state, headline, details, url), `State` |
| `service.py` | `build(events, names)`: one small function per role |
| `router.py` | `GET /runs/{run_id}/signoffs` (own run only) |
| `frontend/…/signoffs/` | `SignoffCard` (server component; `compact` for the inbox), `signoffLabel.ts` (marks and the header line), `getSignoffs` |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/runs/{run_id}/signoffs` | The seven sign-offs, in the order the work happens | Bearer, own run |

## Data model

None.

## Events

Reads `work.finished`, `review.finished`, `check.finished`, `security.finished`, `deploy.finished`, `changes.delivered`, `docs.updated`, `approval.requested`, `approval.decided` and `run.finished`.

## Dependencies

- **Uses:** `events` (the log), `runs` (ownership), `teams` (names)
- **Used by:** the run page and the inbox (frontend)

## Design decisions

- 2026-10-06 — **Built from the log, not stored:** no second source of truth to go stale, and old runs get a card too.
- 2026-10-06 — **Honest, not decorative:** a failure or a send-back is shown as such. The card is the founder's evidence for approving, in the spirit of Dots' "videos with the change" and Grok Bot's "show the real artifact".
- 2026-10-06 — **Per-role functions:** adding a role (Anaya, designs approved) is one more function and one more event.

## How to run and test

- `uv run pytest app/features/signoffs`; `npx vitest run src/features/signoffs`
- **Live (Oct 6, 2026):** a cancelled coffee-shop build showed "Built 3 tasks (Arjun, Isha)", "Reviewed 3 tasks, sent 2 back for changes, all approved", the rest "not yet" or "not part of this run" and "waiting for your approval".

## Known limitations and gotchas

- QA's line is the event summaries, not a pass/fail table of each check (the details are in the activity log).
- Not shown on WhatsApp or email yet (roadmap: WhatsApp two-way).
- The demo video is linked from Tara's line when it exists ([artifacts.md](artifacts.md)).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The card is missing | The API call failed (the page hides errors) | Open `/runs/{id}/signoffs` in the API docs to see the error |
| Everyone says "Not yet" on a finished run | The run's events were deleted or it predates the log | Nothing to fix |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-06 | Tara's line links to the demo video when one was recorded (`video_id`, from `demo.recorded`) |
| 2026-10-06 | Created: the release sign-off card on the run page and in the inbox |
