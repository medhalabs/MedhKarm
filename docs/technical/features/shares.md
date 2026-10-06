# Shares (a public link to a finished build)

**Status:** Built (Phase 3): the founder turns on a public link; anyone can watch the office time-lapse and the demo video, no sign-in; tried in a browser on Oct 7, 2026.  
**Code:** `backend/app/features/shares/` · `backend/app/shared/rate_limit.py` · `frontend/src/features/shares/` · pages `/share/{token}` and `/api/shares/{token}/demo` · migration `0016_run_shares`  
**Last updated:** 2026-10-07

## What it is

On a run's page, **Share this build** creates a link such as `/share/imRrsa…`. Anyone who opens it sees:
- the title, and facts ("2 tasks built, in 3 minutes, tests passed, security checked"),
- the **demo video** (QA using the app), playable and skippable,
- the **office time-lapse**: the team working, replayed, with Play, speed and a slider,
- "Try the app" when it was put online, and a **waitlist form** ([waitlist.md](waitlist.md)).

It's the community's way in: a founder posts the link and people see a finished, tested build. **Stop sharing** ends the link at once. The page also shows how often it was opened.

## What the public never sees

The request text (only its first line, as a title), the founder's messages, model and tool activity, file names and contents, repository links and pull requests, and anything the founder typed at the gate (their feedback). Only these steps are shown: run started, scaffolded, plan, task assigned, work started and finished, review, checks, security, deploy, docs updated, demo recorded, approval asked and decided, run finished. Their text is the team's own sentence, except: "Asked for" shows the title, and the founder's decision reads "The founder approved the release" or "The release was not approved". The run's real id is replaced by the link's token. A test feeds the log private text and checks none of it comes out.

## How it works

1. **Turning on** (`POST /runs/{id}/share`): the run must be the caller's company's. It makes an unguessable token (`secrets.token_urlsafe(16)`, 128 bits) and returns the same link if one exists.
2. **The public page** (`GET /public/shares/{token}`, no sign-in): `ShareService.public()` builds the whitelisted view (`public_events`, `stats`, `live_url`) and counts a view.
3. **The demo** (`GET /public/shares/{token}/demo`): the run's demo video, with byte ranges so browsers can play and skip. The Next.js route `/api/shares/{token}/demo` passes it through, with no session involved.
4. **Rate limit:** 60 opens a minute from one address (`RateLimiter`), then 429.
5. **Turning off** (`DELETE /runs/{id}/share`) deletes the row: the link and the video both stop (404).
6. **The page** (`/share/[token]`) renders the facts, the video, and the same `OfficeView` used for the founder, in replay-only mode (`live={false}`, no "back" link). Link previews get a title and a description; the page is marked `noindex`: it's a link you share, not a page for search engines.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Share`, `PublicShare`, `PublicEvent`, `PublicStats`, `PublicMember` |
| `service.py` | `ShareService` (create, get, revoke, public, demo); `public_events` (the whitelist), `stats`, `live_url`, `title_of` |
| `repository.py` · `memory_repository.py` · `models.py` | The `run_shares` table |
| `router.py` | Owner routes (`/runs/{id}/share`) and public routes (`/public/shares/{token}`) |
| `dependencies.py` | `TeamRoster`, the public rate limiter |
| `shared/rate_limit.py` | `RateLimiter`: a small sliding window, in memory |
| `frontend/…/shares/` | `ShareCard` and `CopyLink` (run page), `getPublicShare`, `facts` |
| `frontend/src/app/share/[token]/` | The public page and its "not found" page |
| `frontend/src/app/api/shares/[token]/demo/route.ts` | The public video route |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | `/runs/{run_id}/share` | Turn the link on (same link if on) | Bearer, own run |
| GET | `/runs/{run_id}/share` | The link and its views, or `null` | Bearer, own run |
| DELETE | `/runs/{run_id}/share` | Turn it off | Bearer, own run |
| GET | `/public/shares/{token}` | The whitelisted view; counts a view | None, rate limited |
| GET | `/public/shares/{token}/demo` | The demo video (ranges) | None, rate limited |

## Data model

`run_shares`: `token` (PK), `run_id` (indexed), `company_id` (FK, cascade), `views`, `created_at`.

## Events

None of its own. Reads the run's log through the whitelist above.

## Dependencies

- **Uses:** `runs` (ownership, title), `events` (the log), `artifacts` (the demo video), `teams` (the roster for the office)
- **Used by:** the run page, and the public pages

## Design decisions

- 2026-10-07 — **A whitelist, not a blacklist:** new event types are private until someone decides to show them.
- 2026-10-07 — **The founder opts in per build,** and can end it.
- 2026-10-07 — **The link is the permission** (no login): an unguessable token, like a shared document link. Anyone with it can pass it on.
- 2026-10-07 — **The time-lapse is the existing replay, in the browser,** not a rendered video: nothing to render or store, and it shows the real office. A downloadable or social-card version is later.
- 2026-10-07 — **Same office code for the founder and the public:** one `OfficeView`, two modes.

## How to run and test

- `uv run pytest app/features/shares tests/test_rate_limit.py`; `npx vitest run src/features/shares`
- **Live (Oct 7, 2026):** a finished test build was shared.
  - The public data had no request text and no real run id.
  - The public page loaded in the browser with the demo video playing (1.76 s, no errors), the office replay with Lekha on the top row, and the waitlist form.
  - Opened 3 times (counted); turning it off made both the API and the page return 404.

## Known limitations and gotchas

- **No download, no social-card image, no MP4 of the time-lapse** (G-54).
- **A shared run that's still going shows what's known so far;** the page doesn't update live.
- **The rate limit is per API process,** which is fine for one process and weaker with many.
- **The link can't be password-protected or given an expiry.**
- **The "views" count includes the founder's own opens of the public page.**
- **A shared build's title** is the first line of its request: a long, messy first line makes a long title.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| "This link doesn't work" | The owner turned it off, or the address is wrong | Make a new link |
| No demo on the page | The run had no passing browser test ([artifacts.md](artifacts.md)) | Nothing to fix; the replay still shows |
| 429 | More than 60 opens a minute from one address | Wait a minute |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-07 | Created: public share links with the demo video, the office time-lapse and facts |
