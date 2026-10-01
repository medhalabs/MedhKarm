# AI Virtual Office — Product Roadmap

Snapshot of Oct 1, 2026 (v2: AI workforce; dates re-planned Oct 1 for one builder, after Phase 1 finished early). Live version: [AI Virtual Office — Product Roadmap](https://claude.ai/artifact/K4F23pkpxAPZ6xpxFMYTi4). Scope: [08-product-plan-v2.md](08-product-plan-v2.md).

One engine runs every AI team; the teams launch one at a time. The **software team** opens a private beta for solo builders in India on Dec 7, 2026 and launches on **Feb 15, 2027**. The **content and video team** follows by mid-May 2027, and the **operations team** from June 2027.

**Why these dates (re-planned Oct 1, 2026).** Phase 1 was planned for Oct 19 – Nov 13 and was built on Oct 1: with AI coding tools, code is not the bottleneck. What doesn't speed up is everything that depends on people and money: interviews and beta commitments, weeks of real beta use, business registration for payments, and paid services (models, hosted sandboxes). So the build phases move up by 6 weeks, but the launch moves up by only 2: the beta still needs its weeks of real use.

## At a glance

| Phase | Dates | Gate |
| --- | --- | --- |
| Phase | Was | Now | Gate |
| --- | --- | --- | --- |
| 0 · Validate and set up | Oct 5 – Oct 16 | **Oct 5 – Oct 16, 2026** (unchanged) | Stack proven ✓; 5+ committed beta users; 20 eval tasks written ✓ and reviewed |
| 1 · Engine and team templates | Oct 19 – Nov 13 | **Done Oct 1, 2026** | Passed ✓ ([09-gate-1-report.md](09-gate-1-report.md)) |
| 2 · Software team | Nov 16 – Dec 18 | **Oct 5 – Nov 27, 2026** (alongside Phase 0's interviews) | 12 of 20 eval tasks pass without help, on new and existing repos; cost per task known |
| 3 · Office and private beta | Jan 4 – Feb 12, 2027 | **Nov 30, 2026 – Jan 29, 2027** (beta from Dec 7) | 70% of beta tasks succeed; 30% of beta users pay; satisfaction 8/10+ |
| Holiday buffer | Dec 21 – Jan 1 | Dec 21, 2026 – Jan 1, 2027 (inside Phase 3) | Hardening and beta support only |
| Software team launch | Mar 1, 2027 | **Feb 15, 2027** | |
| 4 · Content and video team | Mar 1 – May 28, 2027 | **Feb 15 – May 14, 2027** | Creators approve 70%+ of first drafts; cost per video fits pricing |
| 5 · Operations team | From Jun 2027 | From Jun 2027 (unchanged) | Defined after Phase 4 |

**Decision points** (dates by which something outside the code must be settled):

| By | Decision | Why then |
| --- | --- | --- |
| Oct 16, 2026 | Product name and domain | Beta invites and the landing page need them |
| Nov 13, 2026 | A small paid-model budget for evals and the beta (or stay free and narrow the task types) | Gate 2 needs 12/20 evals; on the free model, advanced logic ran out of steps in Gate 1 |
| Nov 13, 2026 | Hosted sandbox for customer code (free tiers first) | Beta users' code can't run on this laptop's Docker |
| Dec 18, 2026 | Business registration and Razorpay account | Gate 3 measures paying users; payments need a registered business (KYC) |

## Principles

1. **Reliability before visibility.** No office UI work until the software team passes the eval suite.
2. **One engine, one team at a time.** Teams are templates on a shared engine; each launches only after passing its own gate.
3. **Every phase ends at a gate.** A gate is a measured result, not a date.
4. **Work is checked before you see it.** Tests for software, your review for content, approval rules for operations.
5. **Buy, don't build, the plumbing.** Official MCP servers, Vercel, Supabase, Razorpay, Resend; our code goes into the teams, the engine and the office.

## Technology stack

See [04-tech-stack.md](04-tech-stack.md).

## Phase 0 — Validate and set up (Oct 5 – Oct 16, 2026, unchanged)

Goal: know who we build for and what "working" means before building the product.

- [x] Prove the stack end to end: LangGraph run with OpenHands in a local Docker sandbox, checkpointed in Postgres (done Oct 1, 2026)
- [x] Interview round 1 ([07-interview-findings.md](07-interview-findings.md)): solo builders in India
- [x] Launch market decided: India first
- [ ] Interview round 2: 10+ solo builders and 5+ content creators, every one ending with a beta ask
- [ ] Pick product name and domain
- [x] Write 20 eval tasks: 17 on 4 existing projects, 3 new modules; all validated, baseline 18/19 (Oct 1, 2026). Waiting for your review
- [x] Office mock-up for interviews: the full expense-calculator journey, animated office, standup and release (done Oct 1, 2026: [mockups/office-demo.html](mockups/office-demo.html), [shareable link](https://claude.ai/artifact/8eBgvzgr8ycDaJd6HZnwSZ))

**Gate 0:** at least 5 solo builders commit to the beta with a real project; 20 eval tasks written and reviewed.

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

Runs alongside Phase 0's interviews: building in the mornings, interviews and beta recruiting in the afternoons. Early sign for the gate: at least 8 of 20 evals passing by Nov 13.

- [ ] Connect an existing GitHub repo; agents map the codebase before changing it (JavaScript/TypeScript and Python first)
- [ ] Backlog: the PM splits a goal into tasks; agents work through them across days
- [ ] Starter repo and ready-made modules for new projects (auth, payments, reminders, dashboards)
- [ ] QA writes and runs tests; build, type-check, lint and tests must pass
- [ ] Preview deploys; production only after the release gate
- [ ] Choose the hosted sandbox (E2B, Fly Machines, Daytona or Modal) for customer code
- [ ] Eval runner: all 20 tasks nightly, both developer engines, with pass rate, cost and time per task
- [ ] Model × role tests: which models fill which seats
- [ ] Automated scans: npm audit, Semgrep

**Gate 2:** at least 12 of 20 eval tasks pass without help; cost and time per task known; prices drafted from those numbers.

## Phase 3 — Office and private beta (Nov 30, 2026 – Jan 29, 2027; launch Feb 15, 2027)

Goal: solo builders in India use the software team on real projects and pay for it.

The beta starts on Dec 7 with the admin page's card layout and the standup (what interviewees asked for first); the animated office joins mid-beta, driven by the same event log. Dec 21 – Jan 1 is buffer: beta support and hardening only.

- [ ] Animated 2D office: each agent has a desk and a character; status bubbles ("Writing the expense form…"); characters move when the CTO assigns work or QA sends a bug back; a meeting room for agent discussions. Every movement is driven by real events from the log, never decoration
- [ ] Replay timeline: agents finish tasks in seconds, so activity is paced and can be scrubbed like a time-lapse; plus the task board
- [ ] Product demo for the customer: live preview link plus a screen recording from QA's end-to-end browser test, before the release approval
- [ ] CEO inbox for approvals and questions; message any agent
- [ ] Standup every morning by email or WhatsApp; weekly report
- [ ] Bring your own: own API keys and local models (Ollama via a small connector), at a lower price
- [ ] Razorpay billing in rupees: base subscription plus pay-as-you-go credits
- [ ] Human expert escalation: we unblock stuck tasks ourselves during beta
- [ ] Onboard 10–20 solo builders from Phase 0 interviews

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
- More stacks and mobile apps for the software team
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
| Oct 5 – Nov 27 | Software team (Phase 2) in the mornings; interviews, beta commitments, name and domain in the afternoons |
| Nov 30 – Jan 29 | Beta onboarding and support first; office UI and billing around it |
| Feb 15 onward | Software team in production; content and video team |

## Risks

| Risk | Phase | Early sign | Fallback |
| --- | --- | --- | --- |
| Eval success rate below 60% | 2 | Under 8/20 by Nov 13 | Narrow to 2–3 task types; stronger model for developer tasks |
| Existing repos are too varied | 2 | Repo tasks fail far more than new-app tasks | Limit to JS/TS and Python; require tests in the repo; codebase map first |
| Cost per task too high | 2 | Median cost above plan margin | Cheap models for easy steps; caching; built-in engine for small tasks |
| No beta commitments | 0–3 | Fewer than 5 by Oct 16, or 10 by Dec 15 | Free beta for a real project; recruit from creator and freelancer communities |
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
- [ ] Product name and domain (by Oct 16, 2026)
- [ ] Paid-model budget for evals and beta (by Nov 13, 2026)
- [ ] Hosted sandbox for customer code (by Nov 13, 2026)
- [ ] Business registration and Razorpay (by Dec 18, 2026)
