# Intake (start a run or a project by talking to the team)

**Status:** Done (Phase 3): conversations replace the "New run" form (with Kabir, the CTO) and the "New project" form (with Mira, the PM); both tried live Oct 5, 2026  
**Code:** `backend/app/features/intake/` · `frontend/src/shared/ui/ChatIntake.tsx` (the chat) · runs: `IntakeChat.tsx`, `BriefCard.tsx` · projects: `ProjectIntake.tsx`, `ProjectBriefCard.tsx`  
**Last updated:** 2026-10-05

## What it is

The founder starts work the way they'd brief a person. They say what they want, or paste a full spec, and Kabir, the CTO, replies with what he understood and up to three short questions:
- new project, or an existing GitHub repository?
- stack preferences, or the team's defaults (Next.js, Supabase, Vercel, Razorpay)?
- does it need sign-in, payments, reminders or an admin dashboard?
- anything genuinely unclear in the scope

When he has enough, he hands over a **brief**: a short summary, plus chips for the repo, the stack choices and the modules. The founder presses **Start run**, or **Change something** to keep talking. **"Skip the questions, start now"** starts at any point with what they wrote. The stack can be anything the founder names.

### Projects, with Mira

The same conversation on the Projects page, with Mira, the PM.
- **What she asks:**
  - what the product is and who uses it
  - the must-have features for the first release
  - new project or existing repo
  - stack (only if you care)
  - whether the team should work through the backlog on its own, and how many items a day
- **What she hands over** (`submit_project`): a project with a name, the whole goal (answers included), a summary, repo, stack, and autopilot with its daily limit. The **"Ready to plan"** card creates it (`POST /projects`), and she plans its backlog as before.
- **Endpoint:** `POST /intake/project`.

### The first reply always asks

Small models sometimes hand over a brief straight away. When that happens on the founder's first message, `too_soon()` holds the brief back and the reply becomes questions: the model's own if it wrote any, else the role's standard ones (`FIRST_QUESTIONS`). The exceptions: a pasted full spec (700+ characters), or the founder saying "just start" / "go ahead".

## How it works

1. **The conversation lives in the browser.** Each turn sends it whole to `POST /intake`, so nothing is stored on the server until the run starts.
2. `IntakeService.turn` calls the CTO role's own model with `INTAKE_PROMPT` and the `submit_brief` tool.
   - When he's still asking, it returns a reply with no brief.
   - When he calls `submit_brief`, it also returns the brief.
3. `parse_brief` reads the tool call leniently:
   - The `request` is the complete ask, with the answers folded in. When the model leaves it out, the founder's own words are used instead.
   - Stack fields only if the founder chose them, modules, starter (auto / yes / no) and notes become a `StackChoice`.
   - Line breaks written as "/n" are fixed.
4. **Start run** posts the brief to `POST /runs`: request, repo (or a new repo and stack), test command. From there it's an ordinary run. The starter step still applies its own rules ([starters.md](starters.md)), so modules named in the request are added even when the brief doesn't list them.

## Code map

| File | Responsibility |
| --- | --- |
| `intake/schemas.py` | `Turn`, `Conversation`, `Brief`, `Reply` |
| `intake/prompt.py` | `INTAKE_PROMPT`, `BRIEF_TOOL` |
| `intake/service.py` | `IntakeService.turn`, `parse_brief` |
| `intake/dependencies.py` | The CTO's model and name from the software template |
| `intake/router.py` | `POST /intake`, `POST /intake/project` |
| `frontend/…/runs/components/IntakeChat.tsx` | The chat: bubbles, examples, thinking dots, skip, start over |
| `frontend/…/runs/components/BriefCard.tsx` | The brief: summary, chips, Start run / Change something |
| `frontend/…/runs/api/actions.ts` | `intakeAction`, `startFromBriefAction` |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | `/intake` | `{turns: [{role: founder or agent, text}]}` → `{agent, text, brief or null}` | Bearer |
| POST | `/intake/project` | The same with Mira → `{agent, text, brief: ProjectBrief or null}` | Bearer |

## Data model

None: the run is created by `POST /runs`.

## Events

None until the run starts.

## Dependencies

- **Uses:** `models` (the CTO's model), `teams` (name and model), `starters` (`StackChoice`)
- **Config:** the CTO role's `model` in the team template (default model otherwise)

## Design decisions

- 2026-10-05 — **A conversation instead of a form** (Pavan): founders say what they want; the CTO asks only what matters, and nothing is a fixed list.
- 2026-10-05 — **The founder always confirms the brief** before any work starts, and can skip the questions.
- 2026-10-05 — **Stateless turns:** the browser holds the conversation, so the API stays stateless and nothing half-finished is stored.

## How to run and test

- `uv run pytest app/features/intake`
- **Live (Oct 5, 2026):**
  - "A booking page for my yoga studio…": Kabir asked new or existing, stack, and sign-in/reminders/admin.
  - "New project, Razorpay ₹499, you pick the rest, admin dashboard, no student sign-in" gave a brief with those choices, in about 10 s per turn on gpt-oss:20b.

## Known limitations and gotchas

- The conversation is lost on a page reload.
- The brief card shows the modules the CTO listed. The starter step may add more from the request's words.
- Each turn takes a few seconds (one model call).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| "Couldn't reach the backend" in the chat | API down, or the model call failed | Start the API; check `OLLAMA_API_KEY`; or use "Skip the questions" |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-05 | Projects by talking to Mira (`/intake/project`, `submit_project`); the shared `ChatIntake` component; the first reply always asks (`too_soon`, `FIRST_QUESTIONS`): live, Mira had jumped to a thin brief |
| 2026-10-05 | Created: start a run by talking to the CTO, with a confirmable brief |
