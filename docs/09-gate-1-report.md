# Gate 1 report: engine and team templates

**Result: PASSED** on Oct 1, 2026, 7 of 7 checks, on run `94333fecaef5` (LRU cache).
Checked by `uv run python -m app.workers.gate_check <run_id>`, which reads everything back from the database: events, the run, its jobs, the LangGraph checkpoint and the standup.

**Gate 1** (roadmap, Phase 1): a team defined in config finishes a 10-step task, pauses at an approval, survives a worker restart, logs every step and its cost, and produces a standup.

## How it was run

Everything went the way a founder would use it: requests over HTTP, a background worker, approval over HTTP. Model: `gpt-oss:20b` on Ollama Cloud (free tier).

1. **19:30:48 IST:** three requests of different difficulty started together with `POST /runs`. The worker runs two jobs at a time.
2. **19:33:11:** with the advanced and medium runs both mid-work (5 tool uses each), the worker was killed with `kill -9`: no warning, no clean-up, like a crashed machine.
3. **A fresh worker** took the medium run over 41 s later, once the dead worker's 60 s lease ran out. The advanced run was taken over when a slot freed up, and the queued easy run started normally.
4. **While the medium run was paused** at the release gate, the worker was stopped (Ctrl+C) and a third one started. The founder's approval was then sent over HTTP, and the new worker released the run.

## The checks (run `94333fecaef5`)

| Check | Result | Evidence |
| --- | --- | --- |
| A team defined in config | Pass | Template `software`; agents seen: Kabir (CTO), Isha and Arjun (developers), Tara (QA), all named in `software.toml` |
| Finishes a task of 10+ steps | Pass | 40 developer steps, 36 tool uses, 2 tasks; run released |
| Pauses at an approval | Pass | Paused at the release gate 27 min, until the founder approved |
| Survives a worker restart | Pass | Killed mid-work; picked up once by another worker ("Picked up again after an interruption"); started once, planned once (the CTO didn't plan again); same sandbox, no extra container |
| Logs every step | Pass | 95 events: the plan, every task attempt, review, QA check, approval and finish |
| Logs every step's cost | Pass | 43 model calls, each with its tokens: 289,563 in the log. The run's own totals say 279,067; the 10,496 extra is the work the crash interrupted: paid for, logged and redone |
| Produces a standup | Pass | Standup for Oct 2: "Create lru.py with an LRUCache class": released, 2/2 tasks; Done lists both tasks and the release |

## Easy to advanced

| Level | Request | Outcome | Time | Tokens |
| --- | --- | --- | --- | --- |
| Easy | Roman numerals both ways, 1–3999, invalid numerals rejected, round-trip tests | QA passed in 6 min; waiting for approval | 6 min | 2,89,688 |
| Medium | LRU cache: O(1) get/put, eviction, `__contains__` without reordering, stats | QA passed, survived the crash, released | 7 min of work (35 min incl. waiting for approval) | 2,89,563 |
| Advanced | Cron-expression parser: ranges, lists, steps, either-day rule, leap years | **Failed:** both developers hit the 25-step limit twice; `cron.py` was left with a syntax error, so QA's tests couldn't load. The run stopped as "checks did not pass" without asking the founder | 19 min | 11,61,859 |

The advanced run also survived the crash (picked up again, planned once), and is the only run where a developer looked something up with the `python_docs` MCP tool.

## What this tells us

1. **The engine is sound.** Crashes, restarts, pauses, approvals, logging, cost and the standup all held up on real work, without help.
2. **The safety net works.** The advanced run failed, and the founder was never asked to approve broken code.
3. **The free small model is the ceiling, not the engine.** Easy and medium requests pass. Advanced logic (cron's edge cases) runs out of steps at about 12 lakh tokens. Options for Phase 2:
   - more steps for the hardest tasks, or a CTO who splits them smaller (cron was split into only "implement" and "test");
   - a stronger model for developers on hard tasks (one line per role in the template) once paid models are in;
   - tests written before code, so each task has a clear target.
4. **Cost per request varies about 4×** between medium and advanced. Pricing needs usage-based limits, not a flat number of builds.

## Housekeeping

- Runs still waiting for a decision (admin page): easy Roman numerals `b2bea8cbbe19`, the dates demo `7f4d86116e4f`, the calc demo `7c011955d56f`. Each keeps its sandbox until decided.
- Earlier test events (`probe`, `test-…`) remain in the development activity log, which is append-only; a separate test database is suggested as its own task.
- The superseded expense-tracker gate attempt `8012ffdef914` was rejected: a shell-loop bug meant its worker was killed only after the run had already paused, which didn't test a mid-run crash.
