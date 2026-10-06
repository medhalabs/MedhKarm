# Blueprints (the plan before the build, written by Lekha)

**Status:** Built (Phase 3): plan-first flow with a documentation bot, comments, approval, and documents delivered in the project; tried live through the API on Oct 6, 2026. The pages weren't opened in a browser yet (G-48).  
**Code:** `backend/app/features/blueprints/` · `backend/app/workers/handlers/blueprint.py` · `backend/app/workers/approved_plans.py` · `backend/app/features/workflows/nodes/blueprint.py` · `frontend/src/features/blueprints/` · page `/admin/blueprints/{id}` · migration `0013_blueprints`  
**Last updated:** 2026-10-06

## What it is

The founder talks to Kabir (the CTO), who asks what he needs and suggests the technology with rough costs in ₹. When they agree, Kabir offers the next step: **Lekha, the documentation lead, writes the plan.** Nothing is built yet.

- **Nine documents,** in plain words, specific to the project. Lekha writes seven; **Anaya, the UI/UX designer, writes the two about screens:**
  1. product brief
  2. roadmap (milestone 1 is what gets built first; later milestones come later, as changes)
  3. **screens and journeys** (Anaya): who does what, step by step, and every screen the first version needs
  4. **screen mockups** (Anaya): the key screens drawn as phone-sized wireframes with the project's real names and prices
  5. architecture (with a diagram and why each choice)
  6. data and API
  7. file structure
  8. test plan
  9. costs (in ₹) and risks
- **The founder reads them** in the app, asks for changes in a comment, and **approves**. Approving starts the build.
- **Skip is always possible:** "Skip the plan, build now" starts a run straight away, as before.
- **The documents are delivered with the project:** the build puts them in the repository's `docs/` folder (with an index), and the CTO and the developers follow them.

## How it works

```mermaid
sequenceDiagram
    participant F as Founder
    participant A as API
    participant W as Worker (Lekha)
    participant R as Build run
    F->>A: POST /blueprints {brief}
    A->>W: job blueprint.write
    W->>W: one model call per document, each saved as it's done
    Note over F,A: the page refreshes: "Writing the architecture (3 of 7)"
    W->>A: status ready (in the inbox)
    F->>A: POST /comments "add a tip option"
    A->>W: job blueprint.revise
    W->>W: which documents does it touch? rewrite only those
    F->>A: POST /approve
    A->>R: start the run with the same brief
    R->>R: blueprint step: write docs/ files; plan and developers follow the plan
```

1. **Asking** (`BlueprintService.create`) saves the brief (the same fields as starting a run) with status `writing` and queues `blueprint.write`.
2. **Writing** (`BlueprintAuthor.write`, in the worker):
   - It writes the documents in order. Each document is saved when finished, so the page shows them as they appear, and a retry keeps what is already written.
   - Each call gets the brief, **the stack the team will really build on** (`StackText`: the founder's choices, then the request's words, then our defaults), and the earlier documents (cut to 3,500 characters each) so they agree.
   - Costs use stated typical prices (`COST_FACTS` in `catalog.py`): "about", check current pricing, payment fees as a percentage and never in the monthly total.
   - A model failure retries the job. When retries run out, the status is `failed` with the reason, and the founder can **Ask Lekha again**.
3. **Commenting** is allowed while the plan is `ready`. It sets `revising` and queues `blueprint.revise`. Lekha first decides which documents the comment touches (a small tool call; unclear answers rewrite all), then rewrites only those, each with the comment and its old text. Her reply is added to the comments ("I updated the architecture, costs and risks") and `revision` goes up.
4. **Approving** (`READY → APPROVED`, atomically, so a double click starts one build) starts the build with the stored brief and saves its `run_id`. If starting fails the plan goes back to `ready`.
5. **In the build** (`workflows/nodes/blueprint.py`, between `connect` and `plan`):
   - It looks up the plan by `run_id` through `ApprovedPlans` (an adapter in `app/workers`, so the workflow code doesn't know about blueprints).
   - It writes the documents into the workspace (`docs/…`, plus `docs/README.md`), so they're released with the code.
   - It gives the CTO the plan, up to 14,000 characters, most useful documents first. Developers get the first 6,000. The instruction is to **build milestone 1 only**.
6. **The inbox** shows "Plans to read and approve" for `ready` blueprints, and they count in the nav badge.

## Anaya's screens

- **Journeys first:** `03-screens.md` lists the two to four journeys and every screen of milestone 1, with what is on it and where it leads.
- **Then the mockups** (`04-mockups.html`): one HTML page with the key screens side by side in phone-sized frames. The founder sees them on the plan page, in a frame with every permission off (`sandbox=""`: no scripts, no forms, no navigation, no network), and can comment ("make the order button bigger") like on any document.
- **The HTML is made inert before anyone sees it** (`mockup.py`): scripts, frames, objects, form tags, event handlers, links and anything that loads from outside are removed; text with no markup becomes a page that says the mockups couldn't be drawn. Fields and buttons of a form stay, so a checkout screen still looks like one.
- **In the build:** the mockups go into the project's `docs/` with the rest, the CTO and developers are told to build the screens to match them, and the screens document is part of the plan they read. The HTML itself is too long to quote in a prompt.
- A **change** to a live project gets no mockups (three short documents only).
- **Live (Oct 7, 2026):** nine documents in under 3 minutes; the mockup showed a Menu screen (Masala Chai ₹40, Ginger Tea ₹35) plus Loading and Error screens, in the sandboxed frame on the plan page. It had no script, link or handler.

## Changes to a live project

A founder who wants something new on a released project talks to Kabir again, **about that project** (run page → "Request a change"). A change to an existing repository gets a lighter plan:
- **Three documents, not seven,** filed under `docs/changes/<date>-<title>/` so the project's own plan and docs are never replaced: change brief, plan and impact, and checks and risks (what could break in the live app; extra cost in ₹).
- **Lekha hasn't seen the code,** so she describes parts by what they do ("the checkout page") and is told never to invent file names. (Live, her first draft invented `src/pages/Checkout.tsx`.)
- **A small change skips the plan:** Kabir marks the brief `small` or `big`, and the brief card offers "Build it now" or "Prepare the plan" accordingly.
- **Comments and approval work the same way.** The build uses the existing repository, and the documents are added to the pull request. The project's own `docs/README.md` is never overwritten.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `BlueprintStatus`, `Doc`, `Comment`, `Blueprint`, `BlueprintSummary`, `NewBlueprint`, `NewComment`, `ApprovedPlan` |
| `catalog.py` | `DOCS` (each document's id, title, path, author, format and what it must contain), `CHANGE_DOCS`, `COST_FACTS` |
| `mockup.py` | `sanitize_mockup`: Anaya's HTML made inert |
| `service.py` | `BlueprintService`: create, owned, list, comment, approve, retry, `for_run` |
| `writer.py` | `BlueprintWriter`: one document per model call, `affected()` for comments; `describe()` |
| `author.py` | `BlueprintAuthor`: write, revise, give_up (the worker's side) |
| `interfaces.py` · `repository.py` · `memory_repository.py` · `models.py` | The `blueprints` table; `RunStarter` |
| `router.py` · `dependencies.py` | `/blueprints` |
| `workers/handlers/blueprint.py` | The jobs `blueprint.write`, `blueprint.revise` |
| `workers/approved_plans.py` | `ApprovedPlans` (adapter for the workflow), `StackText` |
| `workflows/nodes/blueprint.py` | The build step: write the docs, brief the team |
| `teams/templates/software.toml` | The `docs` role: Lekha and her instructions |
| `frontend/…/blueprints/` | `BlueprintPage`, `BlueprintView` (documents, comments, approve), actions, `client.ts` (`askForPlanAction`) |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | `/blueprints` | `{brief}` (the fields of `POST /runs`) → 201, queues Lekha | Bearer |
| GET | `/blueprints` | The company's plans, newest first (no documents) | Bearer |
| GET | `/blueprints/{id}` | The plan with its documents and comments | Bearer, own |
| POST | `/blueprints/{id}/comments` | `{text}` → Lekha rewrites what it touches (409 unless `ready`) | Bearer, own |
| POST | `/blueprints/{id}/approve` | Starts the build; the answer has `run_id` (409 unless `ready`) | Bearer, own |
| POST | `/blueprints/{id}/retry` | Ask again after a failure (409 unless `failed`) | Bearer, own |

## Data model

`blueprints`: `id`, `company_id` (FK, cascade), `title`, `brief` (jsonb, a `StartRun`), `status`, `docs` (jsonb: id, title, path, content), `comments` (jsonb: author, text, at), `progress`, `error`, `run_id` (indexed), `revision`, timestamps.

## Events

None on the run's log yet: the plan is written before a run exists. The run itself starts at approval (G-49: show Lekha's work in the office and activity).

## Dependencies

- **Uses:** `runs` (starting the build, through `RunStarter`), `jobs`, `models` (Lekha's model: the `docs` role, so founders can choose it in Settings → Models), `starters` (the stack text), `auth`
- **Used by:** `inbox` (waiting plans), `workflows` (through `ApprovedPlans`), the worker
- **Config:** none new. Lekha's model and instructions are the `docs` role in the team template.

## Design decisions

- 2026-10-06 — **A plan the founder approves before any code** (Pavan's flow: talk, plan, approve, build, demo, approve, change). It costs a few minutes and removes the biggest risk: building the wrong thing.
- 2026-10-06 — **One model call per document, not one big tool call:** long structured output is where the free models fail. Each document is saved when it's done, so progress is visible and retries are cheap.
- 2026-10-06 — **The plan follows the real stack.** The first live draft proposed React, Express and Docker while the team builds on Next.js, Supabase and Vercel, so `StackText` now tells Lekha what the team will build on.
- 2026-10-06 — **Documents live in the founder's repository** (`docs/`), not only in our database: they own the paperwork and keep it if they leave.
- 2026-10-06 — **Build milestone 1 only.** A roadmap with five milestones must not become one giant run. Later milestones are change requests (roadmap item 3).
- 2026-10-06 — **Costs are stated as "about" with typical prices written in the prompt.** They need a check each quarter; payment fees are never a monthly total.

## How to run and test

- `uv run pytest app/features/blueprints app/features/workflows/tests/test_blueprint_step.py` (plus `-m integration` for the table in the other features)
- **Live (Oct 6, 2026), through the API:**
  - A coffee-shop request: seven documents in about 2½ minutes on `gpt-oss:20b`, progress visible as each was saved.
  - The first draft ignored our stack and invented a monthly payments cost; both fixed (above).

## Known limitations and gotchas

- **Sizing:** each document is one model call of a free 20B model: they read well but are sometimes generic. A stronger model for the `docs` role (Settings → Models) improves them.
- **Reading is in the browser only;** no download or export yet (G-49).
- **The comment box is one thread:** comments are applied in order, and the founder can't comment while Lekha is rewriting.
- **A run started from a blueprint is linked by `run_id` after the run is created.** The build reads it a few seconds later (after clone and scaffold), so it's there in practice; if it were missing the build would run without the plan.
- **Existing repositories** get the same plan, but Lekha doesn't read their code yet (G-12 for Mira is the same gap).
- The run page doesn't link back to its plan yet (G-49).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Stuck on "Lekha is getting started" | The worker isn't running | Start it; the job continues |
| "Lekha couldn't finish: …" | The model failed after retries | **Ask Lekha again**; she keeps what's written |
| Documents are generic | A small model | Pick a stronger one for Lekha in Settings → Models |
| The build ignored the plan | `plans` not wired, or the run isn't linked | Check `blueprints.run_id`; check the worker log for the blueprint step |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-07 | Anaya: two more documents (screens and journeys, screen mockups) written by the designer, mockups shown in a sandboxed frame and made inert first; documents renumbered (architecture is now `05`) |
| 2026-10-06 | Changes to a live project: three-document change plans under `docs/changes/`, no invented file names, no overwrite of the project's docs index |
| 2026-10-06 | Created: Lekha (the `docs` role), seven documents, comments, approval that starts the build, docs delivered in `docs/`, the inbox shows plans, the CTO suggests technology with ₹ costs |
