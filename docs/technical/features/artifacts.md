# Artifacts (files a run produces for the founder: the demo video)

**Status:** Built (Phase 3): QA's browser test is recorded and the video is kept and played in the app; see "How to run and test" for what was tried live.  
**Code:** `backend/app/features/artifacts/` · `backend/app/features/workflows/nodes/browser_qa.py` · `frontend/src/features/artifacts/` · route `/api/runs/{id}/artifacts/{artifactId}` · migration `0014_run_artifacts`  
**Last updated:** 2026-10-06

## What it is

When a run changes something a person sees in a browser, Tara (QA) writes a browser test. Now we run it **with video on**, and when it passes, the recording is kept: **a short demo of the app working, before the founder approves.** The founder sees it as a **Demo** card on the run page and in the inbox, next to the preview link, and "▶ Watch the demo" appears on Tara's line of the sign-off card.

It is the proof Pavan's flow asks for between "built" and "approved". It is not a marketing video: it's what the test saw, in order, at the speed it ran.

## How it works

1. **Recording.** In the browser step, our own run of QA's test adds `--video on --slowmo 300 --output /tmp/medhkarm-demo-<round>` (pytest-playwright records one `.webm` per test page; the 300 ms pause after each action lets a person follow it). The folder is outside the project, so the video is never committed.
2. **Keeping it** (only when the test passed): `_keep_demo` finds the biggest `.webm`, checks it's under 6 MB, reads it as base64 through the sandbox's `run()` (so it works the same on Docker, Daytona and OpenHands, with no new sandbox method), decodes it and saves it through the `ArtifactSink` (the artifacts service). It records a `demo.recorded` event.
3. **Never fails a run.** A missing, oversized or unreadable video, or a database error, is logged and the run carries on without a demo.
4. **Playing.** `GET /runs/{id}/artifacts/{artifactId}` serves the bytes **with byte-range support** (206 / 416): Safari and Chrome won't play or skip through a video without it. The browser reaches it through a Next.js route that adds the founder's session cookie, so the file is private to the run's company.
5. **Storage:** Postgres (`bytea`), 8 MB cap per file. A short test video is about 5–500 KB. When files get big, the repository can move to object storage without touching the callers.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Artifact` (id, run, kind, name, type, size), `Content` |
| `service.py` | `ArtifactService`: save (size cap), list, content; `byte_range()` |
| `repository.py` · `memory_repository.py` · `models.py` | The `run_artifacts` table; listing leaves the bytes out |
| `router.py` | `GET /runs/{id}/artifacts`, `GET /runs/{id}/artifacts/{artifactId}` |
| `workflows/interfaces.py` | `ArtifactSink`: what the workflow needs, nothing more |
| `workflows/nodes/browser_qa.py` | The video flags, `_keep_demo` |
| `frontend/…/artifacts/` | `DemoCard` (the player), `fileUrl`, `listArtifacts` |
| `frontend/src/app/api/runs/[runId]/artifacts/[artifactId]/route.ts` | The proxy that passes the session and byte ranges |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/runs/{run_id}/artifacts?kind=demo` | The run's files, newest first (no bytes) | Bearer, own run |
| GET | `/runs/{run_id}/artifacts/{artifact_id}` | The file; honours `Range` | Bearer, own run |

## Data model

`run_artifacts`: `id` (bigserial), `run_id` (indexed), `kind` (`demo`), `name`, `content_type`, `size`, `data` (bytea), `created_at`. Owned through the run (the same rule as the activity log).

## Events

`demo.recorded` (actor `qa`): "Recorded a demo video of the app working", with `artifact_id` and `bytes`. The office shows it as Tara's bubble.

## Dependencies

- **Uses:** `runs` (ownership), the sandbox's `run()` (nothing else), `signoffs` reads the event
- **Config:** none. The 6 MB (video) and 8 MB (file) limits are constants.

## Design decisions

- 2026-10-06 — **Record our own run of the test, not QA's:** QA writes the test and runs it as it likes; the demo must come from a run we control and know passed.
- 2026-10-06 — **Base64 through `run()`** instead of a binary read on every sandbox provider: three providers, no interface change, and the videos are small.
- 2026-10-06 — **Postgres for now:** one fewer service for the beta, with a hard size cap and the bytes left out of listings. The `ArtifactRepository` interface lets us move to object storage later.
- 2026-10-06 — **Range requests from day one:** without them Safari shows a video that can't play.
- 2026-10-06 — **A demo is a bonus:** failing to record or save never stops a release.

## How to run and test

- `uv run pytest app/features/artifacts app/features/workflows/tests/test_demo_recording.py` (plus `-m integration` for the table); `npx vitest run src/features/artifacts`
- **Live (Oct 6, 2026), two small web-page builds through the whole pipeline** (no GitHub, no deploys):
  - Both passed their browser test, recorded a demo, and reached the gate in about 3 minutes.
  - The file is a valid VP8 video, 800×450, 6 KB. The first (no slow-down) lasted 1.7 s, the second (300 ms pauses) 2.1 s: short because those pages have two or three actions. A real app's journey is longer.
  - The API served it whole (200) and in parts (206), and another company's request got 404.
  - Tara's sign-off line carried the video's id.
  - Not yet seen: the video playing in a browser tab (G-48).

## Known limitations and gotchas

- **Only web changes with a passing browser test get a demo.** Backend-only runs and Next.js apps whose test fails don't.
- **Only the biggest recording is kept** (one video per run and round); a test with several pages shows the longest.
- **Short for simple pages:** the length follows the test, not a script.
- **No audio, no captions, no cursor highlight:** it's Playwright's plain recording. A narrated, polished demo is a later step (the content team's tools).
- **The video can't be downloaded from the card yet** (right-click works in the browser).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No Demo card on a web run | The test failed, no browser test was needed, the video was over 6 MB, or the sandbox image has no video support | Check the activity log for `demo.recorded`; rebuild the sandbox image |
| The video loads but can't play in Safari | The proxy dropped the `Range` header | Check the Next.js route passes `Range` and `Content-Range` |
| 413 on saving | The file is over 8 MB | Shorten the test or raise `MAX_BYTES` |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-06 | The recording run adds `--slowmo 300` |
| 2026-10-06 | Created: browser tests run with video on, the passing test's video is kept and played in a Demo card |
