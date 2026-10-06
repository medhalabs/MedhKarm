# Waitlist (and the public landing page)

**Status:** Built (Phase 3): a public landing page with a waitlist form, a count, and a command-line export; tried in a browser on Oct 7, 2026.  
**Code:** `backend/app/features/waitlist/` · `backend/app/workers/waitlist.py` (the command) · `frontend/src/features/waitlist/` · page `/` · migration `0017_waitlist`  
**Last updated:** 2026-10-07

## What it is

`/` is no longer a placeholder: it's the public face of MedhKarm.
- **The idea in one screen:** "A whole software team, in a chat", who it's for, and a short **How it works** (talk to your CTO, read the plan, watch it get built, see the demo and approve, ask for changes).
- **Why it's different:** you own the paperwork; checked before you see it; built for India; your keys, your models.
- **The waitlist form:** an email, and optionally what they'd like to build. It says "You're on the list (one of N)".
- **A free community beta** is the framing: no prices, no billing (decided Oct 7, 2026).

The same form is at the bottom of every shared build ([shares.md](shares.md)), with `source=share` so we know where people came from.

## How it works

- **Joining** (`POST /public/waitlist`): the email is checked and tidied (lower case). A new email is saved; the same email again is quietly one entry, and the answer is identical, so the form can't be used to find out whether someone is on the list.
- **Bots:** a hidden field called `website` is off-screen; a person never fills it, a bot fills every field. If it's filled, nothing is saved and the answer is still friendly.
- **Rate limit:** 5 sign-ups an hour from one address.
- **The count** (`GET /public/waitlist/count`) feeds "N builders are waiting" on the page.
- **The emails are never served over HTTP.** There is no endpoint that lists them. The team reads them with the command below.

```bash
cd backend
uv run python -m app.workers.waitlist list          # who is waiting
uv run python -m app.workers.waitlist export > waitlist.csv
uv run python -m app.workers.waitlist invite someone@example.com   # marks them invited
```

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `JoinWaitlist` (validated), `Joined`, `WaitlistEntry` |
| `service.py` | `WaitlistService`: join (bot check), count, export, invite |
| `repository.py` · `memory_repository.py` · `models.py` | The `waitlist` table (unique email) |
| `router.py` · `dependencies.py` | `/public/waitlist`, the rate limiter |
| `workers/waitlist.py` | The `list` / `export` / `invite` command |
| `frontend/…/waitlist/` | `WaitlistForm` (with the hidden field), `joinWaitlistAction`, `getWaitlistCount` |
| `frontend/src/app/page.tsx` | The landing page |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | `/public/waitlist` | `{email, name?, building?, source?, website?}` → `{ok, count}` | None, rate limited |
| GET | `/public/waitlist/count` | `{count}` | None |

## Data model

`waitlist`: `id`, `email` (unique), `name`, `building`, `source`, `created_at`, `invited_at`. It has no `company_id`: these people have no account yet.

## Events

None.

## Dependencies

- **Uses:** nothing else.
- **Used by:** the landing page and the share page.

## Design decisions

- 2026-10-07 — **No endpoint lists emails:** a public product collecting addresses must not leak them through a forgotten route. A command run by the team is enough for a beta of tens of people.
- 2026-10-07 — **Same answer for known and unknown emails and for bots.**
- 2026-10-07 — **Optional "what would you like to build":** it tells us who to invite first, and costs the visitor one line.

## How to run and test

- `uv run pytest app/features/waitlist`; `npx vitest run`
- **Live (Oct 7, 2026):** the form was submitted in a browser: "You're on the list (one of 1)", the count API said 1, and the command listed the address. The test address was deleted afterwards.

## Known limitations and gotchas

- **Joining the waitlist does not gate sign-up:** anyone can still create an account at `/signup` (G-55). The invite only marks who the team has chosen.
- **No confirmation email** (the address isn't verified), and no automatic invite email yet.
- **No admin page:** the list is read with the command.
- **The rate limit is per API process.**
- The landing page is in English only, and has no screenshots yet (the first shared builds will be the proof).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| "Too many sign-ups from here" | 5 an hour from one address | Try later |
| The count is 0 | The API is down (the page hides the error) | Start the API |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-07 | Created: the landing page, the waitlist form, the count and the `list`/`export`/`invite` command |
