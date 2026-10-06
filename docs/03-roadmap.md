# AI Virtual Office — Product Roadmap

Snapshot of Oct 1, 2026 (v2: AI workforce; dates re-planned Oct 1 for one builder, after Phase 1 finished early). Live version: [AI Virtual Office — Product Roadmap](https://claude.ai/artifact/K4F23pkpxAPZ6xpxFMYTi4). Scope: [08-product-plan-v2.md](08-product-plan-v2.md).

One engine runs every AI team; the teams launch one at a time. The **software team** opens a private beta for solo builders in India on Dec 7, 2026 and launches on **Feb 15, 2027**. The **content and video team** follows by mid-May 2027, and the **operations team** from June 2027.

**Why these dates (re-planned Oct 1, 2026).** Phase 1 was planned for Oct 19 – Nov 13 and was built on Oct 1: with AI coding tools, code is not the bottleneck. What doesn't speed up is everything that depends on people and money: interviews and beta commitments, weeks of real beta use, business registration for payments, and paid services (models, hosted sandboxes). So the build phases move up by 6 weeks, but the launch moves up by only 2: the beta still needs its weeks of real use.

## At a glance

| Phase | Dates | Gate |
| --- | --- | --- |
| Phase | Was | Now | Gate |
| --- | --- | --- | --- |
| 0 · Validate and set up | Oct 5 – Oct 16 | **Oct 5 – Oct 16, 2026** (unchanged) | Stack proven ✓; name ✓; 20 eval tasks written ✓ and reviewed; 5+ committed beta users by Nov 27 |
| 1 · Engine and team templates | Oct 19 – Nov 13 | **Done Oct 1, 2026** | Passed ✓ ([09-gate-1-report.md](09-gate-1-report.md)) |
| 2 · Software team | Nov 16 – Dec 18 | **Oct 5 – Nov 27, 2026** | 12 of 20 eval tasks pass without help, on new and existing repos; cost per task known |
| 3 · Office and private beta | Jan 4 – Feb 12, 2027 | **Nov 30, 2026 – Jan 29, 2027** (beta from Dec 7) | 70% of beta tasks succeed; 30% of beta users pay; satisfaction 8/10+ |
| Holiday buffer | Dec 21 – Jan 1 | Dec 21, 2026 – Jan 1, 2027 (inside Phase 3) | Hardening and beta support only |
| Software team launch | Mar 1, 2027 | **Feb 15, 2027** | |
| 4 · Content and video team | Mar 1 – May 28, 2027 | **Feb 15 – May 14, 2027** | Creators approve 70%+ of first drafts; cost per video fits pricing |
| 5 · Operations team | From Jun 2027 | From Jun 2027 (unchanged) | Defined after Phase 4 |

**Decision points** (dates by which something outside the code must be settled):

| By | Decision | Why then |
| --- | --- | --- |
| Oct 16, 2026 | Buy medhkarm.in (name decided: MedhKarm) | Beta invites and the landing page need it; an unbought domain can be taken |
| Nov 13, 2026 | A small paid-model budget for evals and the beta (or stay free and narrow the task types) | Gate 2 needs 12/20 evals; on the free model, advanced logic ran out of steps in Gate 1 |
| Nov 13, 2026 | Hosted sandbox for customer code (free tiers first) | Beta users' code can't run on this laptop's Docker |
| Dec 18, 2026 | Business registration and Razorpay account | Gate 3 measures paying users; payments need a registered business (KYC) |

## Principles

1. **Reliability before visibility.** No office UI work until the software team passes the eval suite.
2. **One engine, one team at a time.** Teams are templates on a shared engine; each launches only after passing its own gate.
3. **Every phase ends at a gate.** A gate is a measured result, not a date.
4. **Work is checked before you see it.** Tests for software, your review for content, approval rules for operations.
5. **Buy, don't build, the plumbing.** Official MCP servers, Vercel, Supabase, Razorpay, Resend; our code goes into the teams, the engine and the office.

## Roles: who works in a MedhKarm company

A solo founder's MedhKarm is a small IT company. Not every role in a big one is needed: platforms like Vercel and Supabase replace servers and internal IT, and the founder is the CEO. Every agent is a seat in a team template, added as config (plus the workflow step it needs). Names are office names and can change.

| Role in an IT company | In MedhKarm | Team | When |
| --- | --- | --- | --- |
| CEO | **You, the founder**: you set goals and approve what matters. Never an agent | All | ✓ |
| CTO | Kabir: plans each item, assigns developers, reviews every change | Software | ✓ |
| Product Manager | Mira: turns your goal into a backlog, with questions | Software | ✓ (Oct 2026) |
| Full-stack developer | Isha, Arjun, Ravi | Software | ✓ |
| QA engineer | Tara: re-runs the tests and refuses faked ones | Software | ✓; writes end-to-end browser tests in Phase 2 |
| DevOps engineer | Neel: preview deploys, releases after your approval | Software | Phase 2 |
| Frontend and backend developers | Developer seats with a specialty (UI and browser tests; APIs and database); the CTO assigns by specialty | Software | Phase 2 |
| Security engineer (cybersecurity analyst) | Vikram: scans every release (secrets, dependencies, Semgrep, Supabase access rules) and can block it | Software | Phase 2 |
| Database administrator | Part of the backend developer's and security engineer's work: schema design, migrations (which already need your approval), access rules | Software | Phase 2 |
| UI/UX designer | Anaya: user journeys and screens before anything is built; you approve them | Software | Phase 3 |
| Scrum master and project manager | Priya, the office manager: runs the standup and backlog, chases blockers, tracks timeline and budget per project | All | Phase 3 (standup and backlog work already, without a face) |
| Technical support engineer | During the beta, us (human expert escalation); later, a support agent in the operations team answers your customers | Operations | Phase 3 (us), Phase 5 |
| Mobile app developer | A developer specialty (React Native first) | Software | Later |
| Data analyst | Dashboards and reports on your app's data | Data (new team) | Later |
| Data scientist, ML engineer | Adding AI features to your app (search, recommendations, LLM features) | Data (new team) | Later |
| Cloud architect | Not a seat now: DevOps on managed platforms covers it for solo founders | Software | Later, for larger customers |
| Sales engineer | Not a seat: MedhKarm sells self-serve. A sales assistant may join the operations team for your business | Operations | Later |
| CIO, system administrator | Not needed: no office IT or servers to run; managed platforms do it | None | Not planned |

## Technology stack

See [04-tech-stack.md](04-tech-stack.md).

## Phase 0 — Validate and set up (Oct 5 – Oct 16, 2026, unchanged)

Goal: know who we build for and what "working" means before building the product.

- [x] Prove the stack end to end: LangGraph run with OpenHands in a local Docker sandbox, checkpointed in Postgres (done Oct 1, 2026)
- [x] Interview round 1 ([07-interview-findings.md](07-interview-findings.md)): solo builders in India
- [x] Launch market decided: India first
- [x] Interview round 2: dropped (Oct 3, 2026). Pavan knows what solo builders need from round 1 and his own work; beta commitments are asked for directly instead (see Gate 0)
- [x] Product name: **MedhKarm** (Oct 3, 2026)
- [ ] Buy the domain medhkarm.in (chosen, not yet bought)
- [x] Write 20 eval tasks: 17 on 4 existing projects, 3 new modules; all validated, baseline 18/19 (Oct 1, 2026). Waiting for your review
- [x] Office mock-up for interviews: the full expense-calculator journey, animated office, standup and release (done Oct 1, 2026: [mockups/office-demo.html](mockups/office-demo.html), [shareable link](https://claude.ai/artifact/8eBgvzgr8ycDaJd6HZnwSZ))

**Gate 0:** at least 5 solo builders commit to the beta with a real project; 20 eval tasks written and reviewed. With round 2 dropped, commitments are asked for directly, and the deadline moves to **Nov 27, 2026**, the week before the beta opens (Dec 7).

## Phase 1 — Engine and team templates (planned Oct 19 – Nov 13; done Oct 1, 2026)

Goal: a general engine where a team is defined by config, its work is checked, and every step is recorded.

- [x] Team templates as config: roles, tools, workflow, checking method. Done Oct 1, 2026: software team in `teams/templates/software.toml`
- [ ] Swappable checking step: tests, human review, approval rules (interface and tests checker done; human review and approval rules come with later teams)
- [x] Team Lead agent that plans, assigns and reviews. Done Oct 1, 2026: Kabir (CTO) splits work into tasks, assigns developers by name, reviews each task and sends it back with changes
- [x] Append-only event log: actions, messages, tool calls, costs, approvals; detailed enough to drive the animated office (who is doing what, task hand-offs, messages). Done Oct 1, 2026: API with live stream
- [x] Daily standup generated from the event log (done, planned, blocked, needs approval). Done Oct 1, 2026: built from the log with no model call, by API and command line, and sent every morning by the worker ([standups.md](technical/features/standups.md))
- [x] API endpoints and a job queue, so runs start and approvals happen over HTTP, not the command line. Done Oct 1, 2026: `POST /runs`, approval over HTTP, Postgres job queue; a worker killed mid-run is taken over by another and the build carries on; standup sent every morning ([jobs.md](technical/features/jobs.md), [runs.md](technical/features/runs.md))
- [x] Approval rules on top of fixed gates. Done Oct 1, 2026: rules in the team template decide ask / approve / reject at the release gate (strictest wins) and say why; the software team asks every time and flags secrets, dependencies, migrations, large or expensive changes ([approvals.md](technical/features/approvals.md))
- [x] Tools through MCP, with per-agent access limits. Done Oct 1, 2026: MCP server catalog; each role is granted servers, tools, read-only access and a call limit per task; agents only ever run tools they were offered; first server `python_docs` (GitHub and fetch listed, off) ([integrations.md](technical/features/integrations.md))
- [x] Bare admin page to watch runs. Done Oct 1, 2026: `/admin` to start runs and see their status, each run's live activity and the approval panel (approve or reject, with the rules' reasons), and the standup ([runs.md](technical/features/runs.md))

**Gate 1:** a team defined in config finishes a 10-step task, pauses at an approval, survives a worker restart, logs every step and its cost, and produces a standup. **Passed Oct 1, 2026** (7/7 checks, run killed mid-work and taken over; [09-gate-1-report.md](09-gate-1-report.md)). Advanced logic exceeds the free model's step limit: see the report.

## Phase 2 — Software team (Oct 5 – Nov 27, 2026; was Nov 16 – Dec 18)

Goal: the software team delivers working, tested changes on new and existing projects without help.

Building in the mornings, beta recruiting in the afternoons. Early sign for the gate: at least 8 of 20 evals passing by Nov 13.

- [x] Connect an existing GitHub repo; agents map the codebase before changing it (JavaScript/TypeScript and Python first). Done Oct 3, 2026: clone, map before planning, install/test detection, pull request on release ([repos.md](technical/features/repos.md)); new projects get a private repository on release (tested live Oct 2). Pull request on an existing repo confirmed live Oct 5
- [x] Backlog: the PM splits a goal into tasks; agents work through them across days. Done Oct 5, 2026: projects, Mira's backlog (edit, approve), items as runs, autopilot with a daily limit, approved work merged or waiting for your merge; tested live end to end (Tip splitter: new repo, then a pull request that auto-merged) ([projects.md](technical/features/projects.md))
- [x] Starter repo and ready-made modules for new projects (auth, payments, reminders, dashboards). Done Oct 5, 2026 (tested live: a cafe feedback wall reached the gate with a preview): the founder's stack choice wins (any frontend, API language, database, hosting or payment provider; empty = Next.js, Supabase, Vercel, Razorpay); a tested Next.js starter that runs with no keys, a Python API starter, modules for sign-in, payments (Razorpay or Stripe), reminders and an admin dashboard, Docker files for servers ([starters.md](technical/features/starters.md)). Left: live test in the Phase 2 end pass
- [x] QA writes and runs tests; build, type-check, lint and tests must pass. Done Oct 5, 2026 (live: caught lint and build errors, the fix round solved them): QA runs the tests plus the project's own build, type-check and lint (npm scripts, `tsc`, ruff, mypy, a Python syntax check); checks that already failed before the run don't block; one fix round back to a developer ([workflows.md](technical/features/workflows.md))
- [x] Preview deploys; production only after the release gate. Done Oct 5, 2026 with Neel (below)
- [x] Choose the hosted sandbox (E2B, Fly Machines, Daytona or Modal) for customer code. Done Oct 5, 2026: **Daytona** ([11-hosted-sandbox.md](11-hosted-sandbox.md)); provider built, switched on when the beta starts (local Docker until then)
- [x] Eval runner: all 20 tasks nightly, both developer engines, with pass rate, cost and time per task. Done Oct 4, 2026: every agent's tokens metered per task, ₹ cost at the run's model and at Claude Haiku/Sonnet/Opus prices, history and comparison, nightly with `EVAL_NIGHTLY=true` (OpenHands opt-in) ([evals.md](technical/features/evals.md)). Fresh baseline Oct 5: 18 of 20
- [ ] Model × role tests: which models fill which seats
- [x] Automated scans: npm audit, Semgrep, run by Vikram (security engineer), who can block a release. Done Oct 4, 2026: secrets, 15 offline Semgrep rules, pip-audit/npm audit on changed files after QA; blocking problems go back to a developer once, warnings go to your gate; tested live ([security.md](technical/features/security.md))
- [x] Neel (DevOps) joins the team with preview deploys. Done Oct 5, 2026: Vercel preview before your gate, production after approval, both tested live (word counter live at a public URL) ([deploys.md](technical/features/deploys.md))
- [x] Developer specialties: frontend (UI, browser tests) and backend (APIs, database, migrations); the CTO assigns by specialty. Done Oct 4, 2026: Isha and Ravi backend, Arjun frontend, each with their own instructions; tested live (notes app: API to Isha and Ravi, page to Arjun)
- [x] Tara (QA) writes end-to-end browser tests for web apps. Done Oct 4, 2026: Playwright in the sandbox; for web changes Tara writes one test, we run it, failures go to the frontend developer once; tested live (BMI calculator)

**Phase 2 end test pass (all at once, before Gate 2):** decided Oct 4, 2026: build everything first, then test together.
- ~~Full fresh 20-task eval baseline~~ done Oct 5 (18/20); switch on `EVAL_NIGHTLY=true` when you're ready to spend the quota nightly
- Model × role tests (needs the baseline)

**Gate 2:** at least 12 of 20 eval tasks pass without help; cost and time per task known; prices drafted from those numbers. **Passed Oct 5, 2026:** 18 of 20, median 7 min and 119k tokens per task, draft prices ₹799 / ₹1,999 a month ([12-gate-2-report.md](12-gate-2-report.md)).

## Phase 3 — Office and private beta (Nov 30, 2026 – Jan 29, 2027; launch Feb 15, 2027)

Goal: solo builders in India use the software team on real projects and pay for it.

The beta starts on Dec 7 with the admin page's card layout and the standup (what interviewees asked for first); the animated office joins mid-beta, driven by the same event log. Dec 21 – Jan 1 is buffer: beta support and hardening only.

- [x] Animated 2D office: each agent has a desk and a character; status bubbles ("Writing the expense form…"); characters move when the CTO assigns work or QA sends a bug back; a meeting room for agent discussions. Every movement is driven by real events from the log, never decoration Done Oct 5, 2026: per run, live and replayed, tried live ([office.md](technical/features/office.md))
- [x] Replay timeline: agents finish tasks in seconds, so activity is paced and can be scrubbed like a time-lapse; plus the task board. Done Oct 5, 2026 (1×/2×/4×, scrub; task board with send-backs)
**Added Oct 6, 2026 ([13-strategy-2027.md](13-strategy-2027.md)): the plan-first flow, after Pavan's coffee-shop example. Order: 1 to 3 first, then the rest.**
- [x] 1. **Blueprint stage and Lekha, the documentation bot** (built Oct 6, 2026, [blueprints.md](technical/features/blueprints.md); tried through the API, not yet in a browser): after the talk, Kabir asks "Shall I prepare the plan?"; Lekha with Kabir and Mira writes the product brief, roadmap, architecture, data model, file structure, test plan, costs and risks into the project's own `docs/` folder; the founder reads it in a Blueprint tab, comments and approves before any code. A "skip, just build" button stays
- [x] 2. (done Oct 6, 2026, in his prompt) Kabir **suggests the technology with reasons and monthly cost in ₹** when the founder isn't sure
- [x] 3. (built Oct 6, 2026: [signoffs.md](technical/features/signoffs.md), [blueprints.md](technical/features/blueprints.md); tried through the API and with fakes, not a full run on GitHub, G-50) **Change requests on a live project** ("add a tip option"): small ones go straight to build, big ones update the blueprint first; Lekha updates the docs and changelog after every release; a **sign-off card** per release (Kabir reviewed, Tara's tests, Vikram's scan, Neel's deploy, Lekha's docs)
- [ ] **Care routines** after launch: weekly test re-run, dependency scan, site-up check and docs update, reported in the standup, nothing changed without approval (an idea from Grok Bot's routines)
- [ ] **Autonomy settings** per project: what the team does alone, what it asks first, what it never does (built on the approval rules)
- [ ] **WhatsApp two-way:** approve, answer questions and request changes from WhatsApp (needs the Meta app)
- [ ] **Shareable time-lapse and demo link** of the office building the founder's app, plus a waitlist page: our version of the screenshots that made Clawd Bot spread
- [ ] Product demo for the customer (moved up: it is step 7 of the flow): live preview link plus a screen recording from QA's end-to-end browser test, before the release approval
- [x] CEO inbox for approvals and questions; message any agent. Done Oct 5, 2026 (tried live: Mira's questions in the inbox, an answer cleared one, Mira replied to a message in ~10 s): approvals with approve/reject, Mira's questions with answers that steer her plans, blocked work, messages to any agent with replies in role ([inbox.md](technical/features/inbox.md), [messages.md](technical/features/messages.md))
- [ ] Standup every morning by email or WhatsApp; weekly report. Built Oct 5, 2026: both channels (Resend/SMTP email, Meta WhatsApp), each founder's own standup at their hour, Monday report, settings page with a test send ([notifications.md](technical/features/notifications.md)). Left: your Resend key and WhatsApp app, then a real send
- [x] Bring your own: own API keys and local models (Ollama via a small connector), at a lower price. Done Oct 5, 2026: managed or own keys per founder, a model for the team and per agent, 7 providers including local Ollama through a tunnel URL, encrypted keys checked when added, every call routed by company; OpenHands now resolves settings per task and usage records identify own keys ([model_settings.md](technical/features/model_settings.md)). Left: a purpose-built connector (G-46)
- [ ] Razorpay billing in rupees: base subscription plus pay-as-you-go credits
- [ ] Human expert escalation: we unblock stuck tasks ourselves during beta
- [ ] Onboard 10–20 solo builders from Phase 0 interviews
- [ ] Anaya (UI/UX designer): user journeys and screens before building; the founder approves them
- [ ] Priya (office manager): the face of the standup and backlog; chases blockers, tracks timeline and budget per project

**Gate 3:** at least 70% of beta tasks succeed; at least 30% of beta users convert to paid; satisfaction 8/10 or higher.

## Phase 4 — Content and video team (Feb 15 – May 14, 2027; was Mar 1 – May 28)

Goal: creators get edited videos and AI story videos, in Indian languages, ready to publish.

- [ ] Interview 5+ creators before building (if not done in Phase 0)
- [ ] Sandbox with a screen and media tools: ffmpeg, image editing, browser
- [ ] Workflow: brief → script → produce → creator review → publish
- [ ] Narration and captions in Indian languages (first languages decided from interviews)
- [ ] AI video generation, with cost per video measured before pricing
- [ ] YouTube and Instagram publishing; the creator approves every post
- [ ] Large-file storage and handling

**Gate 4:** creators approve at least 70% of first drafts without a redo; cost per video fits the plan price.

## Phase 5 — Operations team (from June 2027)

Goal: businesses hand routine work to an AI team, safely.

- Computer-use sandbox: agents operate the business's own apps in a browser or desktop
- Email and WhatsApp channels
- Approval rules with money thresholds; full audit log
- Start with low-risk jobs (data entry, scheduling, first-line support)

## Later

- Curated team marketplace, then open listings
- More stacks and mobile apps for the software team (a mobile developer specialty)
- A data team: dashboards and reports (data analyst), AI features in your app (data scientist, ML engineer)
- Cloud architect for larger customers; a sales assistant in the operations team
- Human developers and editors joining the office alongside agents
- Richer office: detailed rooms, character customisation, possibly 3D

## Team and assumptions

One builder (Pavan), full-time, with AI coding tools (Claude Code), from Oct 5, 2026. Development budget ₹0 until the paid-model decision (Nov 13).

What Phase 1 showed: with AI tools, code for a well-defined piece takes days, not weeks. The dates above therefore budget time for what doesn't speed up:

| Work | Assumed pace |
| --- | --- |
| Engine and team code | Days per roadmap item |
| Integrations with outside services (GitHub, Vercel, hosted sandbox, Razorpay) | About a week each, including accounts, limits and failure cases |
| Interviews and beta recruiting | 2–3 conversations a day, alongside building |
| Beta use | At least 6 weeks of real projects before the Gate 3 numbers mean anything |
| Approvals outside our control (business registration, payment KYC) | 2–4 weeks; start early |

| Period | Focus |
| --- | --- |
| Oct 5 – Nov 27 | Software team (Phase 2) in the mornings; beta commitments and the domain in the afternoons |
| Nov 30 – Jan 29 | Beta onboarding and support first; office UI and billing around it |
| Feb 15 onward | Software team in production; content and video team |

## Risks

| Risk | Phase | Early sign | Fallback |
| --- | --- | --- | --- |
| Eval success rate below 60% | 2 | Under 8/20 by Nov 13 | Narrow to 2–3 task types; stronger model for developer tasks |
| Existing repos are too varied | 2 | Repo tasks fail far more than new-app tasks | Limit to JS/TS and Python; require tests in the repo; codebase map first |
| Cost per task too high | 2 | Median cost above plan margin | Cheap models for easy steps; caching; built-in engine for small tasks |
| No beta commitments | 0–3 | Fewer than 5 by Nov 27, or 10 by Dec 15 | Free beta for a real project; recruit from creator and freelancer communities |
| Dots, Grok Bot or Cursor add project management | Any | Competitor launch | Lean on specific teams, Indian pricing and languages, model choice, checked work |
| Content team too costly per video | 4 | Generation cost above what creators pay | Cheaper formats (images + narration); BYO video model keys |
| Animated office takes longer than planned | 3 | Not usable by Jan 8 | Start the beta on a card layout and switch to the animated office mid-beta; the event log drives both |
| Spreading too thin | 4–5 | Software team quality drops while building the next team | Next team waits until the current one holds its gate |
| One builder doing everything | 2–3 | Interviews or beta support crowd out building for a week or more | Protect build mornings; cut Phase 2 scope (starter modules, scans) before moving Gate 2 |
| Free model can't pass Gate 2 | 2 | Advanced eval tasks keep running out of steps (seen in Gate 1) | Paid model for developers only on hard tasks; CTO splits tasks smaller; more steps for hard tasks |

## Decisions

- [x] Launch market: India first (Oct 1, 2026)
- [x] Launch order: software team, then content and video, then operations (Oct 1, 2026)
- [x] Who builds it: Pavan alone, with AI coding tools (Oct 1, 2026)
- [x] Dates re-planned for one builder after Phase 1 finished early: launch Feb 15, 2027 (Oct 1, 2026)
- [x] Development budget: ₹0 for now, free Ollama models only; paid models after a certain stage of development (Oct 1, 2026)
- [x] Product name: MedhKarm (Oct 3, 2026)
- [x] Interview round 2 dropped; beta commitments asked for directly, by Nov 27 (Oct 3, 2026)
- [ ] Buy medhkarm.in (by Oct 16, 2026)
- [ ] Paid-model budget for evals and beta (by Nov 13, 2026)
- [x] Hosted sandbox for customer code (by Nov 13, 2026): Daytona, decided Oct 5
- [ ] Business registration and Razorpay (by Dec 18, 2026)
