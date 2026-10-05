# Known gaps

Everything we know is missing, half-done or untested, in one place, so nothing found along the way gets lost. Each feature doc's "Known limitations" has the detail; this list is what we've decided to fill, and when.

**How to keep it:** a gap found while building or testing gets a line here the same day (and in its feature doc). When it's filled, move it to **Filled** with the date and where. Ids never change.

Last updated: Oct 5, 2026.

## Before Gate 2 (by Nov 27, 2026)

| Id | Gap | Why it matters | Found | Fix idea |
| --- | --- | --- | --- | --- |
| G-01 | **The free model fails the hardest tasks**: 18 of 20 evals pass, but a reminders feature timed out and a slugify module ran out of steps; Gate 1's cron parser failed too | Beta users bring harder work than the evals | Oct 1, Oct 5 | Model × role tests with a paid model; more steps or smaller tasks for hard ones |
| G-40 | A run waiting at the gate lost its sandbox container (cafe wall, Oct 5). Cause unknown: not the eval runner (it removes only its own), Docker's event history had expired | Approving a waiting run must always work | Oct 5 | Watch for it again; if it repeats, keep the work outside the sandbox (push a branch before the gate) so approval never depends on the container |

## Before the beta (by Dec 7, 2026)

| Id | Gap | Why it matters | Found | Fix idea |
| --- | --- | --- | --- | --- |
| G-11 | Local Docker sandbox only; Daytona chosen and its provider built, but not switched on or tried against Daytona | Beta users' code can't run on this laptop | Sep 30 | At the beta: Daytona account, `SANDBOX_PROVIDER=daytona`, one eval run on it |
| G-12 | Mira doesn't read an existing repository's code when planning (the back-and-forth is now in the inbox: answers and messages steer her plans) | Plans for existing projects are generic | Oct 4 | Give her the codebase map |
| G-13 | Frontend API types are written by hand, not generated from the OpenAPI spec (`shared/api/generated/` is empty) | Types can drift from the backend | Oct 1 | Add the generator to the frontend build |
| G-35 | Local mode on Vercel keeps data in each server instance's memory: on a preview, accounts and records can vanish between requests | Founders try previews; sign-up that forgets you looks broken | Oct 5 | A free database per project for previews (Supabase/Neon), or Vercel's storage, set as `DATABASE_URL` by Neel |
| G-14 | No readiness check (database, Redis) on `/health` | Deploys can't tell a broken backend | Oct 1 | `/health/ready` |
| G-41 | Sign-in scopes data in the application only: Postgres row-level security isn't enforced (the app connects as the table owner); no password reset, rate limits on log-in, server-side log-out or teammates | A bug in one query could show another company's data; locked-out founders need us | Oct 5 | A non-owner database role with RLS policies on `company_id`; reset emails with the email service; log-in attempt limits |
| G-46 | Local models reach the worker through a public tunnel URL the founder runs (cloudflared): it changes on restart and is public | BYO local models are a promise of the ₹799 plan | Oct 5 | A small MedhKarm connector on the founder's machine that dials out to us (websocket), so no public URL |
| G-47 | Token usage isn't marked as on our keys or the founder's | Billing (next item) charges only for ours | Oct 5 | Add `own_key` to `model.used` events and the meter |
| G-48 | The Models page wasn't opened in a browser (only the API was tried live; page types, lint and tests pass) | A broken form would block BYO | Oct 5 | Pavan opens /admin/models: save a choice, add and check a key |
| G-43 | Standup and weekly report built but never sent for real: no Resend key or WhatsApp app yet; plain-text email only; one timezone for all; WhatsApp is one-way | The interview ask | Oct 5 | Pavan adds the keys and template (notifications.md); HTML email; read WhatsApp replies via Meta webhooks |

## Later

| Id | Gap | Found | Fix idea |
| --- | --- | --- | --- |
| G-15 | JavaScript inside `.html` files isn't scanned by Semgrep | Oct 4 | Extract inline scripts before scanning, or scan with a model |
| G-16 | Semgrep rule `js-inner-html` also warns on `el.innerHTML = ''` (harmless) | Oct 4 | Add `pattern-not: $EL.innerHTML = ""` (needs an image rebuild) |
| G-17 | Secrets in git history or binary files aren't checked; no Supabase access-rule (RLS) checks | Oct 4 | History scan on onboarding; RLS checks with Supabase projects |
| G-18 | Small models rarely use offered MCP tools (gpt-oss:20b ignored `python_docs` even when told to) | Oct 1 | Stronger models; or prompt the tool at the moment it helps |
| G-19 | The OpenHands engine ignores role instructions, tools, MCP grants and specialties | Oct 1 | Wire them into OpenHands' own settings |
| G-20 | Only the release gate exists; approval rules are per template, not per company | Oct 1 | Spec and plan gates; per-company rules with companies |
| G-21 | Founder's repository: a pull request isn't updated if the founder asks for changes; merge conflicts with later items are left to the founder | Oct 2, Oct 4 | Update the PR on re-runs; rebase items on the latest main |
| G-22 | Repos: GitHub only; monorepos read only root manifests; other languages get no install/test detection | Oct 1 | As customers need them |
| G-23 | Budgets: a project's daily limit counts items, not tokens; no per-company limits or job priorities | Oct 1, Oct 4 | Token budgets with paid models |
| G-24 | The run row and its job are two transactions; finished jobs are never cleaned up | Oct 1 | One transaction; a clean-up job |
| G-25 | A resumed run uses the current `DEVELOPER_ENGINE`, not the one it started with | Oct 1 | Store the engine in the run's state |
| G-26 | `models.md` says there's no per-role model choice; roles do set their own model now | Oct 4 | Doc fix |
| G-27 | The sandbox image is 3.24 GB (Playwright and Chromium, Node 22 and the starter's npm cache; was 1.21 GB): slow first build, more disk | Oct 4 | Playwright's smaller headless-only Chromium; a separate image for web projects |
| G-28 | Browser tests are proven for Python web apps and plain pages; Node/React dev servers (npm, Next.js) aren't tried yet; QA's test used a fixed port (8000) instead of a free one | Oct 4 | Try on a JS app; tell QA to pick a free port in code |
| G-29 | Hobby previews are behind Vercel login (302/401), so Neel can't smoke-test them; the founder must be signed in to Vercel | Oct 4 | Vercel "Protection Bypass for Automation" secret: Neel opens the preview and checks the page and API |
| G-30 | Deploys: no app environment variables (API keys) on Vercel; Flask/Django not detected; inline upload capped at ~6 MB (production tested live Oct 5) | Oct 4 | Test production on approval; env vars per project; file-upload API for big apps |
| G-32 | Eval cost estimates: the OpenHands engine's calls aren't metered (it reports totals only); paid-model figures ignore prompt caching (most tokens are repeated input), so they overstate cost; the ₹ rate in `prices.toml` is set by hand | Oct 4 | Meter OpenHands through its LLM settings; estimate cached input from the conversation shape; update the rate |
| G-33 | QA checks: `ruff`/`mypy` run only when the project installs them (not in the sandbox image); checks already failing before a run are logged but not shown at the gate; the QA fix task goes to the first developer whatever failed; not tried live on a Node/Next.js project | Oct 4 | Add ruff to the image; show old failures at the gate; route by the failing files' specialty; test in the Phase 2 end pass |
| G-36 | Starters: modules exist only for the Next.js API; a split project (Python API + Next.js in `api/` and `web/`) gets none, and QA's checks and Neel's preview only look at the project root; no starter for Java, Go, Django, Vue… (the team sets those up) | Oct 5 | Python modules; checks and previews per folder; more starters as founders ask |
| G-37 | Neel deploys to Vercel only: Docker, DigitalOcean and AWS projects get Dockerfile and compose files but no automatic deploy | Oct 5 | New `DeployTarget` classes (DigitalOcean App Platform, AWS) |
| G-38 | Module services untested against the real thing: Supabase Auth, Razorpay/Stripe test-mode payments, Resend email (unit tests only); no SMS/WhatsApp reminders; Vercel's free plan runs the reminders cron once a day | Oct 5 | Try each with test keys; an SMS/WhatsApp `Notifier` (MSG91, Gupshup) |
| G-39 | The stack and modules are picked from the request's words: now only when phrased as a choice ("using X", "deploy to Y"), and modules from a long spec's opening only. Still words, not understanding (a feature that needs sign-in without saying so) | Oct 5 | Let the CTO confirm or adjust the stack and modules in the plan |
| G-42 | Messages: replies appear only on refresh (no live update); roles without instructions (security, devops) are answered by the first persona; the free model's replies can skip part of a question (live: Mira ignored "why did you ask about timestamps?") | Oct 5 | Live thread updates through the event stream; personas for every role; a stronger model for replies |
| G-45 | The OpenHands engine reads its model when the worker starts, so it ignores founders' own models and keys | Oct 5 | Build the OpenHands agent per run from `ModelSettingsService.config` |
| G-44 | Office: one run at a time (no company-wide office), the meeting room only for planning (no agent discussions yet), PM backlog events not shown, simple figures | Oct 5 | A company office across live runs; discussions as meeting events; richer characters |

## Filled

| Id | Gap | Filled | Where |
| --- | --- | --- | --- |
| — | Developers faked tests with a stand-in `pytest.py` (no pytest in the sandbox) | Oct 1, 2026 | Sandbox image with pytest; review and QA refuse stand-ins ([workflows.md](technical/features/workflows.md)) |
| — | Retries leaked a Docker container per failed developer step | Oct 1, 2026 | `prepare` step creates the sandbox first ([jobs.md](technical/features/jobs.md)) |
| — | The engine ran built-in tools a role wasn't given | Oct 1, 2026 | Only offered tools run ([integrations.md](technical/features/integrations.md)) |
| — | No security checks on releases | Oct 4, 2026 | Vikram ([security.md](technical/features/security.md)) |
| — | Listing the project read all of `node_modules` (22,229 files, about 324k tokens) and broke the first live run on the starter | Oct 5, 2026 | Listing and change detection skip dependency folders; listing capped at 400 ([sandbox.md](technical/features/sandbox.md)) |
| G-02 | Eval results were stale (measured before the CTO, security, specialties, browser tests) | Oct 5, 2026 | Fresh baseline with the whole team: 18 of 20 ([12-gate-2-report.md](12-gate-2-report.md)) |
| G-10 | The standup went to the worker's log only, covering every run | Oct 5, 2026 | Per-company standup and weekly report by email and WhatsApp ([notifications.md](technical/features/notifications.md)); a real send still to do (G-43) |
| G-08 | No sign-in, no companies: API and admin open to anyone | Oct 5, 2026 | Email + password accounts, companies, every route scoped by company ([auth.md](technical/features/auth.md)); RLS still to do (G-41) |
| G-09 | Runs couldn't be cancelled | Oct 5, 2026 | `POST /runs/{id}/cancel` and a Cancel button; running workers stop, sandboxes removed ([runs.md](technical/features/runs.md)) |
| G-34 | The starter had never run live end to end | Oct 5, 2026 | Second live run (cafe feedback wall, gpt-oss:20b) reached the gate: starter + modules, API to Isha, pages to Arjun, QA caught lint/build errors and the fix round solved them, Tara's browser test passed, Vikram clean, Neel's preview ready ([starters.md](technical/features/starters.md)) |
| G-05 | A backlog item had never been released end to end live | Oct 5, 2026 | Live: project "Tip splitter": item 1 created the private repo `tip-splitter-ec7529`, item 2 cloned it, built on it, opened PR #1 and it auto-merged after approval ([projects.md](technical/features/projects.md)) |
| G-06 | A pull request on an existing repository had never been tested live | Oct 5, 2026 | Same live test: item 2 ran on the existing repo (mapped its code) and delivered as a pull request. A founder-owned repo takes the same path and waits for their merge |
| G-03 | Code-graph (Graphify) A/B unfinished | Oct 5, 2026 | Decided from the data: graph off 18/20, on 10/13 with ~29% more tokens; `CODE_GRAPH` stays off |
| G-07 | Integration tests wrote into the development database | Oct 5, 2026 | `backend/conftest.py`: integration tests use `medhkarm_test`, created and migrated on first use ([local-setup.md](technical/local-setup.md)) |
| G-31 | Placeholder tests (`assert True`, tests with no assertion) slipped through | Oct 5, 2026 | `hollow_tests()` guard: the review sends them back (no model call) and QA fails them ([workflows.md](technical/features/workflows.md)) |
| G-04 | QA failures ended the run: no fix round from QA back to a developer | Oct 4, 2026 | One "Make QA's checks pass" task, with build, type-check and lint checks ([workflows.md](technical/features/workflows.md)) |
