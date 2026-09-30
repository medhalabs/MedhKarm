# AI Virtual Office — Product Roadmap

Snapshot of Oct 1, 2026. Live version: [AI Virtual Office — Product Roadmap](https://claude.ai/artifact/K4F23pkpxAPZ6xpxFMYTi4).

Two builders reach a private beta by Feb 12, 2027 and a public launch on Mar 1, 2027, then match cto.new's breadth by end of May 2027. The order is fixed: prove agents ship working apps reliably, then build the office around them, then widen.

## At a glance

| Phase | Dates | Gate |
| --- | --- | --- |
| 0 · Validate and set up | Oct 5 – Oct 16, 2026 | Niche chosen, 5+ interviewees would pay, 20 eval specs written |
| 1 · Agent engine | Oct 19 – Nov 13, 2026 | Pause, resume after restart, every step and cost logged |
| 2 · App-building template | Nov 16 – Dec 18, 2026 | 12 of 20 eval apps deploy without help; cost and time per app known |
| Holiday buffer | Dec 21, 2026 – Jan 1, 2027 | Hardening only, no new scope |
| 3 · Office and private beta | Jan 4 – Feb 12, 2027 | 70% of beta projects deploy, 30% pay, satisfaction 8/10+ |
| Public launch | Mar 1, 2027 | |
| 4 · Match cto.new | Mar 1 – May 28, 2027 | Parity with cto.new's paid plans; 70% success rate holds |
| 5 · Platform | Jun 2027 onward | Ordered by customer demand |

## Principles

1. **Reliability before visibility.** No office UI work until agents ship apps from the eval suite without help.
2. **General engine, one deep template.** The engine runs any agent team; the software company is the first template, built far deeper than cto.new's.
3. **Every phase ends at a gate.** A gate is a measured result, not a date. Miss it and the next phase waits.
4. **Checks run the app.** "Done" means the build, tests and a browser test pass in the sandbox.
5. **Buy, don't build, the plumbing.** Official MCP servers, Vercel, Supabase, Stripe, Resend; our code goes into the agents, the template and the office.

## Technology stack

See [04-tech-stack.md](04-tech-stack.md).

## Phase 0 — Validate and set up (Oct 5 – Oct 16, 2026)

Goal: know who we build for and what "working" means before writing product code.

- [ ] Interview 15–20 potential customers across non-technical founders, agencies and small businesses
- [ ] Pick the launch niche (recommendation: agencies building client apps and internal tools)
- [ ] Pick product name and domain
- [ ] Write 20 reference app specs for the eval suite (booking, CRM, dashboard, internal tool, simple SaaS)
- [ ] Prove the chosen stack end to end: a LangGraph run that starts OpenHands in a local Docker sandbox and saves a checkpoint to Postgres
- [ ] Create the platform repo, cloud accounts, model API keys and a starting budget for tokens
- [ ] Clickable mock-up of the office to show in interviews

**Gate 0:** niche chosen; at least 5 of the people interviewed say they would pay; 20 eval specs written and reviewed.

## Phase 1 — Agent engine (Oct 19 – Nov 13, 2026)

Goal: a general engine that runs a Team Lead and specialist agents, pauses for approval and records everything.

- [ ] LangGraph workflow with Postgres checkpoints: runs survive restarts; approval gates pause with `interrupt()` and resume
- [ ] Team Lead agent that plans, assigns tasks and reviews results
- [ ] Specialist agents defined by config: instructions, tools, model
- [ ] Tools through MCP, with per-agent access limits
- [ ] Shared project context every agent reads and updates
- [ ] Append-only event log: actions, messages, tool calls, costs, approvals
- [ ] Approval rules (for example "always ask before a production deploy") on top of fixed gates
- [ ] LiteLLM model layer with an "Auto" default and cost tracking per agent and per task
- [ ] Bare admin page to watch runs (not the office yet)

**Gate 1:** a Lead plus two agents finish a 10-step task, pause at an approval, survive a worker restart and resume; every step and its cost shows in the event log.

## Phase 2 — AI Software Company template (Nov 16 – Dec 18, 2026, plus holiday buffer to Jan 1)

Goal: agents turn a spec into a deployed, tested Next.js + Supabase app without help.

- [ ] Starter repo: auth, Supabase access rules, migrations, UI kit, Playwright setup
- [ ] Ready-made modules: bookings, payments (Stripe), email and SMS reminders, admin dashboard, file uploads
- [ ] Workflow: PM spec → clickable prototype → CTO plan and tasks → developer → QA → DevOps
- [ ] Choose the hosted sandbox (E2B, Fly Machines, Daytona or Modal) and add it behind the Sandbox interface: isolated per project, limited network access
- [ ] Developer engine: OpenHands behind a "task + repo in, diff + test results out" interface, running in the sandbox (about 1 extra week; the holiday buffer absorbs it)
- [ ] Model × role tests in the eval suite: which models can fill which seats
- [ ] QA writes tests from user stories; build, type-check, lint, unit and Playwright tests must pass
- [ ] Preview deploy to Vercel on every change; production only after the release gate
- [ ] Founder owns the GitHub repo; connect their Vercel and Supabase accounts
- [ ] Change requests on an existing app, with the test suite growing each time
- [ ] Automated scans: npm audit, Semgrep, Supabase access-rule check
- [ ] Eval runner: all 20 reference apps nightly, with pass rate, cost and time per app

**Gate 2:** at least 12 of 20 reference apps (60%) reach a passing deploy without help; median cost and time per app known; pricing drafted from those numbers.

## Phase 3 — Virtual office and private beta (Jan 4 – Feb 12, 2027; public launch Mar 1, 2027)

Goal: real founders build real apps and pay for it.

- [ ] Office floor: each agent's live status, current task and reasoning, built from the event log
- [ ] Meeting-room feed of agent conversations; task board; code, PRs, tests and deploys linked to tasks
- [ ] CEO inbox for approvals and questions; message any agent directly
- [ ] Milestone updates by email, plus a weekly report in plain language
- [ ] Onboarding: idea box, company name, default models
- [ ] Stripe billing with a trial and one paid plan
- [ ] Human expert escalation: we unblock stuck builds ourselves during beta
- [ ] Recruit and onboard 10–20 founders from the chosen niche

**Gate 3:** at least 70% of beta projects reach a deployed app; simple apps deploy in under 3 days; at least 30% convert to paid; satisfaction 8/10 or higher.

## Phase 4 — Match cto.new (Mar 1 – May 28, 2027)

Goal: cover what cto.new offers, reusing the engine.

- [ ] Model picker with cost labels; Bring Your Own Model (Claude, OpenAI, Gemini keys) on higher plans
- [ ] Local models (Ollama) through a small connector app
- [ ] Two more team templates: marketing agency and internal-tools team
- [ ] Scheduled runs and webhook triggers
- [ ] Agents send and receive email on the customer's domain
- [ ] Custom domains for shipped apps
- [ ] Team accounts; Agency plan with client workspaces and white-label reports
- [ ] Full pricing: Trial, Builder, Managed, Agency; top-up credits
- [ ] Designer and Security Reviewer agents join the software template

**Gate 4:** every feature in cto.new's paid plans has an equivalent; the software template's success rate holds at 70% or more.

## Phase 5 — Platform and beyond (from June 2027)

- Curated template marketplace first, open listings with revenue share later
- More stacks (for example Python or Rails backends) and mobile apps
- Published sites and hosting-and-maintenance add-on
- CFO and CMO agents once they have concrete jobs
- Human developers joining the office alongside agents
- Animated 2D office view

## Team and assumptions

Two full-time builders using AI coding tools, starting Oct 5, 2026. With one builder, Phases 1–3 take roughly 1.5–2 times as long.

| Role | Phase 0–2 focus | Phase 3+ focus |
| --- | --- | --- |
| Builder 1 (agents and backend) | Engine, workflow, sandbox, eval runner | Template quality, new templates, BYOM |
| Builder 2 (product and frontend) | Interviews, specs, starter repo, modules | Office UI, onboarding, billing, beta support |

- Token and cloud budget during development is not set yet; the eval suite shows real cost per app by Gate 2.
- The original 10–12 weeks becomes about 16 weeks to beta close, because the engine is general and the eval suite comes first.

## Risks

| Risk | Phase | Early sign | Fallback |
| --- | --- | --- | --- |
| Eval success rate stays below 60% | 2 | Under 8/20 by Dec 4 | Narrow to 2–3 app types; more ready-made modules; stronger model for developer tasks |
| Cost per app too high for pricing | 2 | Median cost above planned plan margin | Cheap models for easy steps; prompt caching; token caps per task |
| Agents stall on change requests to grown apps | 3 | Beta apps fail after 3+ change rounds | Project memory file, stricter task size, human expert takes over |
| Office UI eats the schedule | 3 | Office not usable by Jan 25 | Plain dashboard for beta; polish after launch |
| cto.new or others ship a strong app-building template | Any | Competitor launch | Lean on measured success rate, tests and account ownership |
| Beta founders are hard to recruit | 3 | Fewer than 10 signed by Jan 15 | Use Phase 0 interviewees; offer free builds to agencies |

## Decisions needed before Phase 0

- [ ] Who builds it: solo, or with a second full-time builder?
- [ ] Launch market: India first, global, or both (affects Stripe vs Razorpay and pricing)
- [ ] Monthly token and cloud budget for development
- [ ] Confirm the start date of Oct 5, 2026
