# Review of the original plan

Sep 30, 2026. Reviews [00-original-plan.md](00-original-plan.md).

The vision is clear and the MVP cuts are sensible. The main concern: most of the plan's structure goes into the part that's easy to build (agent roles and the office UI), and too little into the part that decides whether the product works (reliably building and changing real apps).

## 1. Make the roles a view of the work, not separate AIs

Six agents chatting with each other (the MetaGPT / ChatDev approach) loses to one strong coding agent with good tools. Agent-to-agent chatter burns tokens, loses context at every handoff and adds ways to fail.

- **Outer layer: a fixed workflow.** Spec → prototype → plan → tasks → build → verify → deploy. Approval gates are pauses and resumes.
- **Inner layer: one coding agent** that runs each task in the sandbox.
- **PM, CTO and QA are steps in the workflow**, each with its own instructions and output.
- **The office stays as designed** for the founder: the "live company" feel without real multi-agent chaos.

## 2. QA should run the app, not just have an AI read the code

"Done" means the build, type-check, lint, unit tests and Playwright tests against a preview deploy all pass. The QA agent writes those tests from the user stories and reads the results. Reliable checking is the moat.

## 3. Start every app from a template

One starter repo (Next.js + Supabase) with sign-in, access rules, migrations, Stripe, email/SMS, scheduled jobs, a UI kit and Playwright set up. Add ready-made modules: bookings, payments, reminders, admin dashboards, file uploads. Agents adapt tested parts instead of writing them from scratch.

## 4. Show founders screens, not documents

Non-technical founders can't judge a spec well or a technical plan at all. Build a clickable prototype (screens with fake data) first.

1. **Gate 1:** spec plus clickable prototype
2. **Gate 2:** scope, timeline and cost only (architecture stays internal)
3. **Gate 3:** release

## 5. Drop Bring Your Own Model from the MVP

- Non-technical founders don't have API keys and don't care which model runs.
- 4 providers × 6 roles is a large test matrix; weak models fail and the product gets blamed.
- Ollama needs a tunnel or connector app: its own product.
- The cheap BYOM plan still costs us sandboxes, previews and CI.

Keep a model layer internally, launch managed-only on 1–2 tuned models, add BYOM later for Pro/Agency.

## 6. Build an eval suite before the office UI

Write 15–20 reference app specs, run them end to end unattended, and track success rate, cost, time and fixes per app. Don't set pricing until cost per app is known.

## 7. Treat "keep improving" as the main product

Change requests on a growing codebase are where founders spend their time and where agents fall apart. From the start: a per-project memory file, a codebase map, and a test suite that grows with every feature.

## 8. Record everything as events from day one

One append-only event table (actions, messages, tool calls, costs, gate decisions). The office floor, feed, task board, reports, cost tracking and replay are all built from it.

## 9. Decide early who owns the accounts

Founder owns GitHub, and decide the same for Vercel, Supabase and the app's own Stripe/SMS keys. Never let the model see the app's secrets. Limit the GitHub App to one repo per project and restrict sandbox network access.

## 10. Cut scope to fit the timeline

**Cut or defer:** BYOM, Stripe billing (invoice by hand in beta), WhatsApp/Slack alerts, the second developer agent.

**Add cheaply:** automated security scans (`npm audit`, Semgrep, Supabase access-rule check); ourselves as the "human expert" in beta; milestone-based reports instead of daily standups.

## 11. Pick a sharper niche

"Transparency" alone is weak. Lean toward **agencies building internal tools and client apps**: partly technical, pay more, value white-label reports. Pitch: "Production-grade: tested, secure, and you own it."
