# Strategy for 2027: what we learn from the leaders, and what we change

Written Oct 6, 2026, after Pavan's brief: *"A founder tells the CTO bot what they want. It asks what it needs, suggests the technology, then asks 'shall I prepare the roadmap?'. A documentation bot does all the paperwork. The team builds, shows a demo, the founder approves, and later changes work the same way. We must build tech like the market leaders, with zero investment, and be a big hit in 2027."*

## What I looked at

The [Dots announcement](https://openai.com/index/introducing-dots/) refused my fetch (HTTP 403), but Pavan pasted its full text, so that one is first-hand. The [Grok Bot page](https://x.ai/bot) refused too, but Pavan pasted its text, so that one is first-hand as well ([TechCrunch](https://techcrunch.com/2026/09/29/openai-launches-dots-its-bubbly-agentic-avatar/), [Forbes](https://www.forbes.com/sites/ronschmelzer/2026/10/05/what-are-openai-dots-and-do-you-need-them/), [Composio's Grok Bot guide](https://composio.dev/content/guide-to-frok-bot)). [clawd-bot.com](https://www.clawd-bot.com/) I read directly. For app builders I used [a 2026 founder comparison](https://altar.io/ai-app-builders-founders-comparison-2026/). Nothing here was used hands-on. Details per product: [02-competitors.md](02-competitors.md).

## What each one is good at

| Product | Why people use it | What it doesn't do |
| --- | --- | --- |
| **Dots** (OpenAI) | Always-on agents with their own cloud computer. You set what they may do alone, when they must ask, and what is never allowed. 4,000+ app connections | A general agent you direct. It doesn't deliver a tested, deployed product with the paperwork |
| **Grok Bot** (xAI) | "Teach a task": record your screen once and it becomes a repeatable skill. Works while you're away | Same: general, and gated to top-tier plans |
| **Clawd Bot / OpenClaw** | Free and open source. You control it from **WhatsApp, Telegram, Slack, iMessage**. It remembers you. 60,000 GitHub stars in 3 days, from screenshots people shared | Personal assistant: email, calendar, browsing. Not a software team |
| **Lovable, Bolt, Replit Agent** | Describe an app, get a working UI for about $25 a month (Replit: $8–25 per big task) | One shot. Little planning, no roadmap or architecture you keep, no QA or security review, no "tell me what changed" afterwards |
| **Devin** | Autonomous engineer, $20 a month and up | Aimed at developers with existing teams |

## The one idea they all share, and the gap

The leaders compete on **"an agent that does anything"**. Nobody competes on **"a company that builds my product the proper way and keeps running it"**. A coffee-shop owner doesn't want an agent; they want an *ordering app that works next week, that they understand, own and can change by messaging*. That is our ground.

We can't out-spend them on models or infrastructure, and we shouldn't try. We win on four things they can't copy quickly:

1. **A process they can trust:** conversation → blueprint → build → demo → approval → changes. Every step has an owner and a sign-off.
2. **Paperwork they own:** roadmap, architecture, data model, file layout and test plan, written into their own repository. If they leave us, they keep everything. (Builders give code; we give a project.)
3. **India first:** ₹ pricing (₹799 to bring your own keys, ₹1,999 managed), WhatsApp as a main channel, Razorpay and UPI built in, Hindi and Kannada later.
4. **Zero lock-in, zero black box:** their own models, keys and local models; every action visible in the animated office and a replay.

## What we adopt from them

| From | We adopt | Where |
| --- | --- | --- |
| Dots | **Autonomy settings, as three lists per project:** *allow* (the team just does it), *ask first*, *never*. Their *Custom Rules* work this way. Our approval rules and gate become the founder's dial, with a few things always left to the founder (passwords, payments, deleting data) | Roadmap item |
| Dots | **Proof with every change:** their developer example delivers PRs "with attached videos showing the changes". That is our demo recording plus the sign-off card, so both stay high on the list | Roadmap items |
| Dots | **Open the agent's workspace:** they let you inspect the dot's computer. We offer the preview link, the replay and the activity feed; a read-only "look inside the sandbox" view is worth adding | Later |
| Dots | **Proactive background work, read-only:** their dot researches while idle but can't send or change anything. Priya could do the same: spot stalled work, suggest the next backlog item, never act without approval | Phase 3, with Priya |
| Clawd Bot | **WhatsApp as a two-way control channel:** reply "approve", answer Mira's question, or say "add a tip option" from WhatsApp. Our standup is already one-way on WhatsApp | Roadmap item |
| Clawd Bot | **Virality by shareable proof:** their growth came from screenshots. Ours: a one-click **shareable time-lapse** of the office building the founder's app, plus the live demo link | Roadmap item |
| Clawd Bot | **Persistent memory of the business** (menu, brand, tone, past decisions) so the second request is easier than the first | Part of the blueprint docs |
| Grok Bot | **Care routines after launch:** its "routines on a schedule" for our case. When the app is live, the team keeps watching it: every week Tara re-runs the tests, Vikram scans dependencies, Neel checks the site is up, Lekha updates the docs, and the founder gets a line in the standup. Nothing changes without an approval. A reason to keep paying after the build | Roadmap item |
| Grok Bot | **Approval cards that show the real thing:** an email draft with *Send* / *Discard*. Ours: the release card shows the demo, the changes and the sign-offs, and works from WhatsApp too | With the sign-off card |
| Grok Bot | **A first message that interviews you:** "What do you want me around for?" Our CTO chat already does this | Built |
| Grok Bot | **Teach by example, later:** "record how my staff handle an order" feeds the Operations team in Phase 5 | Later |
| Lovable | **A first result in minutes:** the demo preview must appear quickly. Our median build is 7 minutes | Already there |

## Pavan's flow, mapped onto the product

The coffee-shop example, step by step, with what exists and what is new.

| # | What the founder sees | Status |
| --- | --- | --- |
| 1 | Tells **Kabir (CTO)** "a web app for my coffee shop to take orders" | Built |
| 2 | Kabir asks only what's needed (new or existing, sign-in, payments) **and suggests the technology with reasons and monthly cost in ₹** ("Next.js with Supabase, free to start; Razorpay for UPI") | Asking is built. **Suggestions with costs are new** |
| 3 | Kabir asks **"Shall I prepare the plan?"** and waits | **New:** an explicit gate |
| 4 | **Lekha, the documentation bot,** with Kabir, Mira and Anaya, writes the **blueprint**: product brief, roadmap with milestones, architecture and why, data model, screens, file structure, test plan, running costs and risks | **New** (see below) |
| 5 | The founder reads the blueprint in the app, comments, and **approves** it | **New:** a second approval gate, before any code |
| 6 | The team builds: Isha, Arjun and Ravi develop, Kabir reviews, Tara tests, Vikram scans | Built |
| 7 | **Demo:** a live preview link and a recording of QA using the app | Link built; recording is next |
| 8 | The founder approves; Neel deploys | Built |
| 9 | "I need a new thing / change this" starts the **same loop on the live project**: small changes go straight to build, big ones update the blueprint first | **New:** change requests |
| 10 | A **sign-off card** on every release: Kabir reviewed, Tara's tests passed, Vikram's scan clean, Neel's deploy live, Lekha updated the docs | **New:** all the data exists in the log |

### The documentation bot: Lekha

Lekha ("writer" in Hindi) does the paperwork so the founder never has to ask for it.

- **Before the build, the blueprint**, written into the project's `docs/` folder:
  - `01-product-brief.md`: goal, users, must-have features, what is out of scope
  - `02-roadmap.md`: milestones, each a set of runs, with the demo at each end
  - `03-architecture.md`: stack, how the parts fit, and why each choice (with a diagram)
  - `04-data-and-api.md`: tables and endpoints
  - `05-screens.md`: from Anaya, once she exists
  - `06-structure.md`: the file tree and where things go
  - `07-test-plan.md`: what Tara will check
  - `08-costs-and-risks.md`: hosting and tool costs in ₹, and what could go wrong
- **After every release, the changelog:** Lekha updates the docs to match what was built and logs what changed, in plain language for the founder.
- **The founder owns it:** the files live in their repository, and the app shows them in a **Blueprint** tab with comments and approval.
- **Dogfooding:** this is how we already work (a doc per feature, changelogs, a gaps list). Lekha makes it the product.

## Roadmap changes (also in [03-roadmap.md](03-roadmap.md))

Phase 3 now runs in this order. Beta stays Dec 7.

1. **Blueprint stage and Lekha:** the plan-first gate, the docs, the Blueprint tab and approval. (Oct)
2. **Kabir's suggestions with costs in ₹,** and the "shall I prepare the plan?" gate. (Oct)
3. **Change requests on a live project** and the **release sign-off card.** (Oct–Nov)
4. **Demo recording** from QA's browser test (already on the list; moves up because the demo is step 7). (Nov)
5. **Autonomy settings** per project. (Nov)
6. **WhatsApp two-way:** approve, answer and request changes from WhatsApp. Needs the Meta app and template. (Nov)
7. **Shareable time-lapse and demo link,** plus a waitlist page. (Nov)
8. **Razorpay billing.** (Nov–Dec)
9. **Anaya and Priya** (screens before building; the standup's face). (Dec, or inside the beta)
10. **Beta Dec 7:** 10–20 solo builders from the interviews, then launch Feb 15.

Moved to later: Grok-style "teach a task", a company-wide office, mobile apps.

## How to be a hit with zero investment

- **Build in public.** Every beta project is a demo: the office time-lapse is our screenshot. Post one a week (X, LinkedIn, Indian founder communities, ProductHunt in the launch month).
- **Free first project,** paid after. The cost is model quota, which we know: median 119k tokens a task.
- **Distribution through WhatsApp:** founders forward a demo link; the link ends in "Built by a MedhKarm team. Start yours."
- **Open-source a piece** (the office and replay viewer) as OpenClaw did, for stars and trust, while the engine stays closed. To decide before launch.
- **Stay cheap:** free tiers (Vercel, Supabase, Resend), bring-your-own keys at ₹799, our bill near zero on that plan.
- **Measure what matters** (Gate 3): 70% of beta tasks succeed, 30% convert to paid, satisfaction 8/10.

## Risks to watch

- **The giants add "build me an app" to their always-on agents.** Our protection is the process, the owned paperwork and India, not model quality. Re-check every quarter.
- **Dots roadmap: "teams of dots" and specialist dots.** They plan teams, but for company back-office work first. Watch whether they add a software-delivery team; our head start is a tested process and the paperwork.
- **Bundles:** Grok Bot costs $20 a month on Cursor Pro, per its own page, so our first users may already have a general agent in their subscription. Our managed plan costs about the same, so the case for it has to be the finished product and the paperwork, not price. Bring-your-own at ₹799 (about $9) is the cheaper way in. We must show a finished, tested product on their repo, which a general agent doesn't promise.
- **Blueprint gate adds friction.** Keep it quick: one question round, a plan in a few minutes, a "skip, just build" button for founders who don't want it.
- **Promise vs. reality:** "hot cake" needs the demo to work every time. Gate 2 was 18 of 20 tasks; the beta target of 70% is the real test.
