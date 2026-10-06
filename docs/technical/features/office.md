# Office (the animated office, replay and task board)

**Status:** Done (Phase 3): a 2D office per run, live and replayed, with a task board; tried live Oct 5, 2026  
**Code:** `frontend/src/features/office/` · page `/admin/runs/{id}/office` (link "Watch the team in the office →" on the run page)  
**Last updated:** 2026-10-05

## What it is

The founder watches their team work.
- **The floor:** every agent has a desk and a character (Mira, Kabir, Isha, Arjun, Ravi, Tara, Vikram, Neel). There's a meeting room, and the founder's office with a door.
- **The characters move with the work:**
  - The team gathers in the meeting room when Kabir plans.
  - Kabir walks to a developer's desk to assign or review a task.
  - Tara or Vikram walks over when sending a fix back.
  - Kabir waits at the founder's door when a release needs approval.
  - Everyone goes back to their desk when the run ends.
- **Speech bubbles** say what each agent is doing ("Ran the tests", "Approved …").
- **Every movement comes from a real event** in the run's activity log, never decoration.

**Replay** paces the log evenly, because agents finish tasks in seconds. Play, pause, change speed (1×, 2×, 4×), or scrub through it like a time-lapse. The **task board** shows each of Kabir's tasks moving To do → Working → In review → Done, with send-backs counted.

## How it works

1. `officeState(team, events)` (`officeState.ts`) is a pure function: it folds the events, in order, into each agent's place (`desk` of someone, `meeting` or `door`), what they're doing (idle, thinking, working, testing, reviewing, talking, waiting) and a bubble.

   | Event | In the office |
   | --- | --- |
   | `run.started`, `codebase.mapped` | Kabir at his desk, thinking |
   | `project.scaffolded`, `deploy.finished`, `changes.delivered` | Neel's bubble |
   | `plan.created` | Kabir and every task owner go to the meeting room |
   | `task.assigned` | Whoever assigned it (Kabir, Tara, Vikram) walks to the assignee's desk |
   | `work.started` | Everyone leaves the meeting room; the developer works at their desk |
   | `model.used` / `tool.used` | Thinking / the tool's summary (testing when it ran tests) |
   | `work.finished` | The developer's summary |
   | `review.finished` | Kabir at the developer's desk, reviewing |
   | `check.finished` / `security.finished` | Tara / Vikram at their desks, testing |
   | `approval.requested` | Kabir at the founder's door; the office glows "A release is waiting for you" |
   | `approval.decided` | Kabir goes back to his desk |
   | `message.posted` | The replying agent's bubble |
   | `run.finished` | Everyone back at their desk; the office shows the outcome |

   Who an event is about comes from its `data.member`, else the first person in the actor's role.
2. `taskBoard(events)` (`taskBoard.ts`):
   - `plan.created` gives the tasks.
   - A `task.assigned` with a new `task_id` adds a fix task (QA, security, browser test).
   - `work.started` → Working, `work.finished` → In review.
   - `review.finished` → Done (approve) or back to To do with one more send-back (revise).
3. **The roster** is every name in the software team template (`GET /teams/templates/software`), one desk each. Leadership sits on top, developers in the middle, specialists below.
4. **Live:** `OfficeView` starts from the events loaded on the server and follows the stream (`/api/runs/{id}/events/stream`, with the session token), like the activity feed.
5. **Replay:** steps through the events, leaving out `model.used`, which is too frequent: one step every 1.4 s at 1×.
6. **Drawing** (`OfficeFloor`, `Character`): inline SVG. Characters glide (CSS transform transitions, 1 s), and bubbles fade in. Motion is turned off when the device asks for reduced motion. Colours are by role, and it works in light and dark.

## Code map

| File | Responsibility |
| --- | --- |
| `types.ts` | `Member`, `Place`, `Doing`, `AgentState`, `OfficeState`, `BoardTask` |
| `officeState.ts` | `officeState`, `applyEvent`, `initialOffice` |
| `taskBoard.ts` | `taskBoard` |
| `layout.ts` | Floor plan: desks, meeting seats, the door; where each character stands (visitors side by side) |
| `colors.ts` | Role colours |
| `components/OfficeFloor.tsx` · `Character.tsx` · `TaskBoard.tsx` | Drawing |
| `components/OfficeView.tsx` | Live / replay, the controls, the caption |
| `components/OfficePage.tsx` · `api/getTeam.ts` | Server side: roster and events |
| `features/events/client.ts` | The events feature's browser-safe entry (`eventStreamUrl`, types) |

## API

None of its own: `GET /teams/templates/software` and the run's events (`/runs/{id}/events`, `/events/stream`).

## Data model

None.

## Events

Reads every run event type. The frontend's `EVENT_TYPES` now includes `project.scaffolded` and `message.posted`.

## Dependencies

- **Uses:** `events` (server: `listEvents`; browser: `@/features/events/client`), `teams` API
- **Convention added:** a feature may have a second public entry, `client.ts`, for browser-safe exports. `index.ts` can export server-only code that reads the session cookie, which can't be bundled for the browser. ESLint allows `@/features/<name>/client` ([05-architecture-and-conventions.md](../../05-architecture-and-conventions.md)).

## Design decisions

- 2026-10-05 — **A pure function from events to office state**, shared by live and replay, and tested without a browser. The drawing only renders that state.
- 2026-10-05 — **Inline SVG with CSS transitions**, not a game engine or canvas: crisp at any size, accessible (each character has a `<title>`), themeable, no extra library.
- 2026-10-05 — **Replay is paced by events, not by clock time:** real gaps are anything from milliseconds to minutes.

## How to run and test

- `npx vitest run src/features/office`: planning in the meeting room, walking to assign and review, QA walking to a developer, the door at the gate, everyone home at the end, the task board's columns and send-backs.
- **Live (Oct 5, 2026):** a test run (greet.py).
  - Live view: Kabir at the founder's door, "A release is waiting for you"; Isha, Ravi, Tara and Vikram with their last results.
  - Replay: Kabir walking to Ravi's desk to assign "Create test_greet.py". 30 steps in about 12 s at 2×.
  - The board ended with both tasks Done (one sent back once).

## Known limitations and gotchas

- One run at a time: there's no company-wide office showing every run at once yet.
- The meeting room is used for planning only. Agents don't hold discussions there yet.
- The PM's backlog planning (project events) isn't shown in the office.
- Simple figures. Small on phones, though the SVG scales.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Someone works at the wrong desk | A member name the template doesn't have | Add the name to the role's `display_names` |
| The office doesn't move live | The stream route isn't reachable, or the run finished | Reload; finished runs open in replay |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-06 | `demo.recorded` shows Tara's bubble "Recorded a demo of the app" |
| 2026-10-06 | Lekha has a desk (top row) and her own colour; `docs.updated` shows her bubble |
| 2026-10-05 | Created: the office per run (live and replay), task board, `@/features/events/client` |
