# Deploys (DevOps, Neel)

**Status:** Built (Phase 2): a preview before the release gate, production after approval, on Vercel. Preview tested live (Oct 4, 2026); production not yet tested live  
**Code:** `backend/app/features/deploys/` · workflow steps `nodes/preview.py` and `nodes/finish.py` · migration `backend/alembic/versions/0007_run_deployment.py`  
**Last updated:** 2026-10-04

## What it is

A founder shouldn't approve code they've only read about. **Neel**, the DevOps engineer, puts the work online twice:

- **Preview:** after QA, the browser test and security pass, and before the founder's release gate. The approval panel shows **Try the preview →**.
- **Production:** only after the founder approves. The run shows **Live at …**.

Apps that can't run online (libraries, scripts) are skipped. A preview that fails to build doesn't stop the run; the founder is asked, with the reason.

## How it works

1. **What kind of app** (`detect.py`, by its files):

| Kind | Detected by | On Vercel |
| --- | --- | --- |
| Next.js | `package.json` depends on `next` | Built by Vercel (`framework: nextjs`) |
| FastAPI | a `FastAPI()` named `app` in `app.py`, `index.py`, `server.py`, `main.py` or `asgi.py` (also under `src/`, `app/`) | One Python function (Vercel's zero-config FastAPI). Without `requirements.txt`/`pyproject.toml`, we add `requirements.txt` with `fastapi` |
| Static | `index.html` or `public/index.html` | Served from Vercel's CDN |
| None | anything else | Not deployed |

2. **What's sent** (`service.py`): the workspace's files except tests (`tests/`, `test_*.py`, `*_test.py`), `.git`, `node_modules`, caches, `.env*` and `*.pyc`; at most 300 files and about 6 MB, base64 inside the request (Vercel's inline files).
3. **The project name** is the same for every run of a project, so it keeps one address: the new repository's name, the founder's repository name, or `medhkarm-<run id>` for a one-off run (`deploy_name`), made Vercel-safe (`project_name`).
4. **Vercel** (`vercel.py`): `POST /v13/deployments` (`skipAutoDetectionConfirmation`, `forceNew`; `slug` = `VERCEL_TEAM` when set), then polls `GET /v13/deployments/{id}` every 3 s until `READY`, `ERROR` or `CANCELED` (7-minute limit). Production uses the project's own `<name>.vercel.app` alias.
5. **In the run:**
   - The preview goes into `state.preview`, and the gate gets `preview_url` (or `preview_error`).
   - The approval fact `preview_failed` feeds the rule "The preview didn't build, so it can't go live as it is."
   - Production goes into `state.deployment`, and the run row's `deployment` holds the live URL.
   - Events: `deploy.finished` from `devops` ("Preview ready: …", "The preview didn't build: …", "Live at …", "Couldn't put it live: …").
6. **Never an exception:** a host error comes back as a deployment with `state: ERROR`, so released work is never lost because a deploy failed.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `AppKind`, `DeployFile`, `Deployment` |
| `interfaces.py` | `DeployTarget` Protocol |
| `detect.py` | `detect_app()` |
| `vercel.py` | `VercelDeployTarget` |
| `service.py` | `DeployService.deploy()`, `project_name()` |
| `workflows/nodes/preview.py` | The preview step, `deploy_name()` |
| `workflows/nodes/finish.py` | Production after approval |
| `workers/wiring.py` | `DeployService` when the team has an active `devops` role and `VERCEL_TOKEN` is set |

## API

None of its own: `GET /runs/{id}` → `gate.preview_url` / `gate.preview_error`, and `deployment` once released.

## Data model

`runs.deployment` (jsonb, migration 0007): the production `Deployment`.

## Events

`deploy.finished` (new type) from the actor `devops`.

## Dependencies

- **Config:** `VERCEL_TOKEN` (vercel.com → Account Settings → Tokens), optional `VERCEL_TEAM` (team slug). Without a token nothing is deployed.
- **Used by:** `workflows`; the team template's `devops` role (Neel) switches it on.

## Design decisions

- 2026-10-04 — **Preview before the gate, production after.** The founder approves what they've tried, and nothing goes public without them.
- 2026-10-04 — **Inline files, no git integration.** Works for repos and new projects alike, without connecting Vercel to GitHub; enough for small apps (a file-upload path is the next step for big ones).
- 2026-10-04 — **A failed preview never blocks the run**; the founder decides with the reason in front of them.
- 2026-10-04 — Vercel first: free Hobby plan, first-class for Next.js and static sites, zero-config FastAPI. Other hosts would be new `DeployTarget` classes.

## How to run and test

- Tests: `uv run pytest app/features/deploys app/features/workflows/tests/test_preview_step.py` (detection, files, Vercel with a fake API, preview → gate → production, nothing live without approval).
- **Live test (Oct 4, 2026):** a word counter (FastAPI + page). QA's tests and Tara's browser test passed and security was clean. Neel's preview reached `READY` on Vercel as `medhkarm-4d3ea47bde94-…vercel.app`; the run waited at the gate. The preview answers 302 (sign in to Vercel) and 401 for the API, because Hobby previews are protected; the founder, signed in, can open it.

## Known limitations and gotchas

- Hobby previews are behind Vercel login, so Neel can't check them himself (see gaps: protection bypass).
- Production hasn't been exercised live yet.
- Inline files: about 6 MB and 300 files at most; binary assets are sent as base64 within that.
- Environment variables (API keys) for the app aren't set on Vercel yet.
- Python apps other than FastAPI (Flask, Django) aren't detected yet.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No preview at the gate | Not an app (library), no `VERCEL_TOKEN`, or no active `devops` role | Check the run's `preview.kind` and `.env` |
| "Vercel refused the deployment (403)" | Token scope or team | Set `VERCEL_TEAM` to the team slug |
| Preview asks to sign in | Vercel Deployment Protection on previews | Sign in to Vercel, or turn protection off for the project |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-04 | Created: app detection, Vercel previews before the gate, production after approval, `runs.deployment` |
