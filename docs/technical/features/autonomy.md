# Autonomy (how much the team does on its own)

**Status:** Built (Phase 3): the founder's dial for releases, what still asks, files the team must never change, and going live; per company and per project; tried live on real builds on Oct 6–7, 2026. The page wasn't opened in a browser yet (G-48).  
**Code:** `backend/app/features/autonomy/` · `backend/app/features/workflows/nodes/autonomy.py` · `backend/app/workers/run_autonomies.py` · `frontend/src/features/autonomy/` · page `/admin/autonomy` · migration `0015_autonomy_settings`  
**Last updated:** 2026-10-07

## What it is

A page where the founder decides, in plain terms, what the team does alone, what it asks first, and what it never does.

**How much on its own** (three choices; everyone starts on the first):
1. **Ask me before every release.** Nothing goes out without a yes.
2. **Release small, clean changes on its own.** "Small" is a number of files (default 3), with checks passed and no open review comments. Anything bigger waits.
3. **Release on its own when every check passes.**

**Always stop and ask me when…** (on by default; each can be switched off):
- it changes secrets, dependencies, the database or deployment settings
- the CTO accepted work with review comments still open
- the security engineer has warnings
- the preview doesn't build
- it changes more than N files (default 15)
- it uses more than N model tokens (default 1,000,000)

**Never let the team change these files:** one path or pattern per line (`payments/*`, `*.sql`). A release that touches one is **stopped without asking**, with the reason recorded.

**Go live:** after a release, publish to the internet (when deploys are set up), or deliver the code only.

**Always yours,** whatever is chosen: the team never handles passwords, never takes customers' money, never deletes the founder's data on its own, and a release that fails its checks or has a blocking security problem never goes out.

The page also says in plain sentences what the current choices mean ("It still stops to ask you when…"), and has a scope bar: **Everything**, or one project. A project can have its own settings, or go back to the company's.

## How it works

1. **Settings → rules** (`policy.build_policy`): the team template's approval rules (`software.toml`) are adjusted by the founder's settings.
   - Each question is a rule that is switched on or off; the file and token limits change its condition.
   - "Small, clean changes" switches on the template's `small_clean_change` rule.
   - "On its own after checks" adds an approve rule (`checks_pass`).
   - Each never-change pattern adds a **reject** rule.
   - The strictest matching rule still wins (reject, then ask, then approve), so "release on its own" never overrides a question the founder left on.
2. **A company that never opens the page behaves exactly as before:** with no row, the template's rules are used untouched. (Tested: the default settings give the same verdicts as the template.)
3. **Which settings apply to a run** (`AutonomyService.for_run`): its project's own, else the company's, else the template. The project is found through the backlog item that started the run. A run from the New run chat has no project, so it uses the company's.
4. **The autonomy step** (`workflows/nodes/autonomy.py`, between `preview` and `approval`) works out the verdict and the go-live flag and saves them in the run's state. The gate and the finish step read them from there. Because it's saved, a settings change made **while a release waits** can't turn the founder's pending decision into an automatic one.
5. **At the gate:** ask → the usual pause; approve → released with the reason recorded ("Approved the release by your rules: …", shown as "Approved by your rules" on the sign-off card); reject → stopped, "Stopped by your rules: You told the team never to change …".
6. **Go live off:** the finish step skips the production deploy, though the preview and the delivery to GitHub still happen.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `AutonomySettings` (validated: patterns must be inside the project), `Level`, `Scope`, `AutonomyView` |
| `policy.py` | `build_policy` (settings → approval rules), `describe` (settings → plain sentences) |
| `service.py` | `AutonomyService`: view, save, reset, `for_run` |
| `repository.py` · `memory_repository.py` · `models.py` | The `autonomy_settings` table: the company's row has `project_id ''` |
| `router.py` · `dependencies.py` | `/settings/autonomy`; `ProjectsOfRuns` (run → project) |
| `workflows/nodes/autonomy.py` | The step before the gate |
| `workflows/interfaces.py` · `workers/run_autonomies.py` | `RunAutonomies` and its adapter (reads the company from `current_company`) |
| `frontend/…/autonomy/` | `AutonomyPage` (scope bar), `AutonomyForm`, `parseSettings`, actions |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/settings/autonomy?project_id=` | The settings (a project shows the company's when it has none), `own`, and the plain-sentence `summary` | Bearer |
| PUT | `/settings/autonomy?project_id=` | Save the company's, or a project's own | Bearer, own project |
| DELETE | `/settings/autonomy?project_id=` | A project goes back to the company's settings | Bearer, own project |

## Data model

`autonomy_settings`: `company_id` (FK, cascade) + `project_id` (`''` = the company's) as the key, `settings` (jsonb), `updated_at`.

## Events

None of its own. The gate's existing `approval.decided` (by `rules`) now carries the founder's own reasons.

## Dependencies

- **Uses:** `approvals` (the rule engine), `teams` (the template's policy), `projects` (ownership; run → project), `auth`
- **Used by:** the build graph, through `RunAutonomies`
- **Config:** none. The template's rules in `software.toml` are the base.

## Design decisions

- 2026-10-07 — **Plain settings that compile to the existing rules, not a rule editor:** founders think "small changes can go alone"; the engine already knows "strictest wins". Nothing in the rule engine changed.
- 2026-10-07 — **Safe by default, and unchanged for those who never open it.**
- 2026-10-07 — **The verdict is fixed before the gate:** a decision pending at the gate is the founder's; settings can't take it over later.
- 2026-10-07 — **The founder's questions beat "release on its own":** a risky change (secrets, security warnings, a failed preview) still asks unless they switched that question off. The first live build asked because the CTO had left comments open, exactly as designed.
- 2026-10-07 — **Never-change files stop the release:** the team can still write the file, but the release can't go out. Blocking the edit itself (before the work) is a later step (G-53).

## How to run and test

- `uv run pytest app/features/autonomy app/features/workflows/tests/test_autonomy_step.py`; `npx vitest run src/features/autonomy`
- **Live (Oct 6–7, 2026), real builds of small web pages on the test account:**
  - The API returned the plain-sentence summaries, and a bad pattern (`/etc/passwd`) was refused with a clear message.
  - "Release on its own" with the open-comments question left on: the build **asked**, because the CTO had left comments open.
  - With that question switched off: **"Approved the release by your rules: Every check passed and nothing needs a look: released on its own."**
  - With `index.html` set as never-change: **"Stopped by your rules: You told the team never to change index.html."**, and the run ended rejected.

## Known limitations and gotchas

- **Settings are read once, at the autonomy step.** A change made while a run is still building applies to it; one made while it waits does not.
- **Go live only matters where deploys are set up** (a Vercel token).
- **Per project means a backlog project:** runs started from the New run chat use the company's settings.
- **The approval rules in `software.toml` are the base:** a founder can't add a custom rule type yet, only the ones above and the never-change list.
- **The team can still change a never-change file during the work:** it is only stopped at release (G-53).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A release asked although "on its own" is set | A question that is switched on matched (the gate says which) | Read the reason on the approval, or switch that question off |
| A project ignores the company's change | It has its own settings | Open the project and choose "Use my settings for everything" |
| "use a path or pattern inside the project" | A never-change pattern started with `/` or had `..` | Write it relative to the project, e.g. `payments/*` |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-07 | Created: the autonomy dial (three levels), questions, never-change files, go live, per company and per project |
