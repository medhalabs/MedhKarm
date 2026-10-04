# Known gaps

Everything we know is missing, half-done or untested, in one place, so nothing found along the way gets lost. Each feature doc's "Known limitations" has the detail; this list is what we've decided to fill, and when.

**How to keep it:** a gap found while building or testing gets a line here the same day (and in its feature doc). When it's filled, move it to **Filled** with the date and where. Ids never change.

Last updated: Oct 5, 2026.

## Before Gate 2 (by Nov 27, 2026)

| Id | Gap | Why it matters | Found | Fix idea |
| --- | --- | --- | --- | --- |
| G-01 | **The free model fails advanced tasks.** Cron parser (Gate 1) and the first Pomodoro item both failed: developers ran out of steps, got stuck on test-import errors and reached for shims | Gate 2 needs 12 of 20 evals; beta users bring real work | Oct 1, Oct 4 | Paid-model decision by Nov 13; CTO splits smaller; more steps for hard tasks; tests first |
| G-02 | Eval results are stale: measured before the CTO, security step, specialties and browser tests. The runner now measures cost and time per task (Oct 4); a full fresh baseline hasn't been run | Gate 2 is measured on them | Oct 1 | One full run now; then `EVAL_NIGHTLY=true` |
| G-03 | Code-graph (Graphify) A/B comparison unfinished (graph on: 10 of 13 so far, about 29% more tokens) | Decide whether to keep it | Oct 2 | Finish with the eval runner; lean: keep off |
| G-05 | A backlog item has never been released end to end live (repo created, next item builds on it, auto-merge) | The backlog's core promise | Oct 4 | One live run with your OK to create the repo |
| G-06 | A pull request on an existing repository has never been tested live against GitHub (skipped Oct 3) | Founders with existing projects | Oct 3 | Test with the first beta user's repo, or a test repo |
| G-34 | The starter hasn't run live end to end: the free model building on it, Tara's browser test on a Next.js app, a Vercel preview of it | It's how every new project will start | Oct 5 | Phase 2 end test pass |
| G-07 | Integration tests write into the development database; test runs (`probe`, `test-…`) can't be deleted from the append-only log and show as "Blocked" in standups | Misleading standups | Oct 1 | Separate test database (task suggested Oct 1) |

## Before the beta (by Dec 7, 2026)

| Id | Gap | Why it matters | Found | Fix idea |
| --- | --- | --- | --- | --- |
| G-08 | **No sign-in, no companies.** API and admin page are open to anyone who can reach them; `company_id` is empty everywhere, no row-level security | Required before anyone else uses it | Oct 1 | Supabase auth, a companies feature, `company_id` required with RLS |
| G-09 | Runs can't be cancelled | A runaway run burns tokens | Oct 1 | Cancel endpoint + job release + sandbox removal |
| G-10 | Standup goes to the worker's log only, and covers every run (not per company) | "A standup every morning" was the interview ask | Oct 1 | Email or WhatsApp delivery; filter by company |
| G-11 | Local Docker sandbox only | Beta users' code can't run on this laptop | Sep 30 | Hosted sandbox decision by Nov 13 |
| G-12 | Mira doesn't read an existing repository's code when planning, and there's no back-and-forth: she lists questions, you edit and ask again | Plans for existing projects are generic | Oct 4 | Give her the codebase map; answer her questions in the page |
| G-13 | Frontend API types are written by hand, not generated from the OpenAPI spec (`shared/api/generated/` is empty) | Types can drift from the backend | Oct 1 | Add the generator to the frontend build |
| G-35 | Local mode on Vercel keeps data in each server instance's memory: on a preview, accounts and records can vanish between requests | Founders try previews; sign-up that forgets you looks broken | Oct 5 | A free database per project for previews (Supabase/Neon), or Vercel's storage, set as `DATABASE_URL` by Neel |
| G-14 | No readiness check (database, Redis) on `/health` | Deploys can't tell a broken backend | Oct 1 | `/health/ready` |

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
| G-31 | Placeholder tests slip through: a developer added `tests/test_dummy.py` with `assert True`; the CTO's review should refuse "tests that check nothing", but didn't, and the guards only catch fake test tools | Oct 4 | A guard for tests with no real assertion (`assert True`, empty bodies); CTO review prompt with an example |
| G-32 | Eval cost estimates: the OpenHands engine's calls aren't metered (it reports totals only); paid-model figures ignore prompt caching (most tokens are repeated input), so they overstate cost; the ₹ rate in `prices.toml` is set by hand | Oct 4 | Meter OpenHands through its LLM settings; estimate cached input from the conversation shape; update the rate |
| G-33 | QA checks: `ruff`/`mypy` run only when the project installs them (not in the sandbox image); checks already failing before a run are logged but not shown at the gate; the QA fix task goes to the first developer whatever failed; not tried live on a Node/Next.js project | Oct 4 | Add ruff to the image; show old failures at the gate; route by the failing files' specialty; test in the Phase 2 end pass |
| G-36 | Starters: modules exist only for the Next.js API; a split project (Python API + Next.js in `api/` and `web/`) gets none, and QA's checks and Neel's preview only look at the project root; no starter for Java, Go, Django, Vue… (the team sets those up) | Oct 5 | Python modules; checks and previews per folder; more starters as founders ask |
| G-37 | Neel deploys to Vercel only: Docker, DigitalOcean and AWS projects get Dockerfile and compose files but no automatic deploy | Oct 5 | New `DeployTarget` classes (DigitalOcean App Platform, AWS) |
| G-38 | Module services untested against the real thing: Supabase Auth, Razorpay/Stripe test-mode payments, Resend email (unit tests only); no SMS/WhatsApp reminders; Vercel's free plan runs the reminders cron once a day | Oct 5 | Try each with test keys; an SMS/WhatsApp `Notifier` (MSG91, Gupshup) |
| G-39 | The stack and modules are picked from the request's words, not understood ("spring" in a sentence; a feature that needs sign-in without saying so) | Oct 5 | Let the CTO confirm or adjust the stack and modules in the plan |

## Filled

| Id | Gap | Filled | Where |
| --- | --- | --- | --- |
| — | Developers faked tests with a stand-in `pytest.py` (no pytest in the sandbox) | Oct 1, 2026 | Sandbox image with pytest; review and QA refuse stand-ins ([workflows.md](technical/features/workflows.md)) |
| — | Retries leaked a Docker container per failed developer step | Oct 1, 2026 | `prepare` step creates the sandbox first ([jobs.md](technical/features/jobs.md)) |
| — | The engine ran built-in tools a role wasn't given | Oct 1, 2026 | Only offered tools run ([integrations.md](technical/features/integrations.md)) |
| — | No security checks on releases | Oct 4, 2026 | Vikram ([security.md](technical/features/security.md)) |
| G-04 | QA failures ended the run: no fix round from QA back to a developer | Oct 4, 2026 | One "Make QA's checks pass" task, with build, type-check and lint checks ([workflows.md](technical/features/workflows.md)) |
