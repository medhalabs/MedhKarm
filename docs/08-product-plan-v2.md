# Product plan v2: AI workforce

Decided Oct 1, 2026 by Pavan. Replaces the scope of [00-original-plan.md](00-original-plan.md), which stays as history. Based on the [interview findings](07-interview-findings.md) and the [competitor review](02-competitors.md).

## In one paragraph

MedhKarm gives solo founders, creators and small businesses in India a **ready-made AI team for a specific job**: a software team that builds, tests and ships; a content team that edits and publishes; an operations team that takes over routine work. Every team runs on one engine. A lead agent plans and assigns the work, specialist agents do it in an isolated sandbox, the work is checked before you see it, you approve what matters, and you get a standup every morning. You stay the CEO.

## Who it's for, and the teams we build

| # | Customer | What they want | Team | Launch |
| --- | --- | --- | --- | --- |
| 1 | **Software startups and solo builders** | An AI team that builds, tests and ships on their project | **Software team:** PM, tech lead, developers, QA, DevOps | **First** (beta Jan 2027) |
| 2 | **Content creators** | Digital editors | **Content team:** editor lead, video editor, thumbnail designer, caption writer | **Second** (with #3) |
| 3 | **Creators making AI videos** | Turn a story into a narrated AI video and post it on social media | Same content team, plus script writer, narrator, video generator, publisher | **Second** (with #2) |
| 4 | **Businesses with existing services** | Replace routine work done by staff (support, data entry, scheduling, bookkeeping) | **Operations team:** roles defined per job | **Third** |

Teams 2 and 3 share most tools, so they ship together.

## How it works: one engine, many team templates

Every team is a **template** with four parts:

| Part | Software team | Content team | Operations team |
| --- | --- | --- | --- |
| **Roles** | PM, tech lead, developers, QA, DevOps | Editor lead, editors, designer, writer, narrator, publisher | Defined per job |
| **Tools** | Code sandbox, GitHub, Vercel | Video and image editing (ffmpeg), media AI, text-to-speech, YouTube/Instagram | Browser/desktop control, email, WhatsApp, the business's own apps |
| **Workflow** | Spec → plan → build → test → release | Brief → script → produce → review → publish | Job-specific, with approval rules |
| **How work is checked** | **Automatically:** tests must pass | **By the creator:** review before anything is published | **By rules:** approval thresholds ("refunds over ₹2,000 need my OK") plus an audit log |

What every team shares: the lead agent, the event log, the **animated live office** (agents as characters at desks, moving and talking as they really work; in the beta from Phase 3), the CEO inbox for approvals, the **daily standup**, model choice and cost tracking.

## Launch order

1. **Software team.** Mostly built already, success is measurable (tests pass), and interviews found real demand from solo builders.
2. **Content and video team.** Strongest India angle: **narration and captions in Indian languages** (Hindi, Kannada, Tamil and more) for a huge creator market. Interview 5+ creators before building it.
3. **Operations team.** Biggest market, but hardest and riskiest. Starts once approval rules, audit logs and the computer-use sandbox are proven.

Each team launches only after it passes its own quality gate (see the [roadmap](03-roadmap.md)).

## Software team: what changed from v1

- **Works on existing projects:** connect a GitHub repo; agents map the codebase before changing it. JavaScript/TypeScript and Python first. The starter template stays for new projects.
- **Runs as a project, not a chat:** a backlog the PM splits into tasks, agents working through it day after day, QA on every change.
- **Daily standup** every morning: what was done, what's planned today, what's blocked, what needs your approval.

## Positioning

**"An AI workforce for India's solo founders, creators and small businesses."**

| Against | Our difference |
| --- | --- |
| Claude Code, Cursor | They answer prompts; we run the project: backlog, task split, QA, standups, release gates |
| Dots (OpenAI), Grok Bot (xAI) | They're general agents you have to direct, priced in their top plans and tied to one model family. We offer ready-made teams for specific jobs, Indian pricing and languages, your choice of models, and work that's checked |
| cto.new | Broad and shallow; no checks that run the work, no fixed workflows |

Details: [02-competitors.md](02-competitors.md).

## Pricing direction (to test in interviews)

- **India first:** rupee pricing, Razorpay.
- **Base subscription** for the platform: teams, office, standups, approvals.
- **Bring your own:** your own API keys or local models (via a small connector) at a lower price.
- **Managed:** our models, with pay-as-you-go credits on top.
- **Human expert help** when agents get stuck: paid per fix (and run by us manually during beta).

Exact prices come after the eval suite measures real cost per task.

## Architecture changes this needs

Built on the current engine (LangGraph, LiteLLM, swappable developer engines, sandboxes):

1. **Team templates as config:** roles, tools, workflow and checking method per team.
2. **Swappable checking step:** today "verify" always runs tests. It becomes an interface with three kinds: tests, human review, approval rules.
3. **Sandboxes with a screen** for teams 2–4: browser or desktop control (the OpenHands agent server already ships browser tools).
4. **Connected accounts with permission:** YouTube, Instagram, WhatsApp, email. Anything public or sent to customers goes through an approval gate by default.
5. **Media handling** for the content team: large files, GPU-heavy or paid generation, storage.

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Big players (OpenAI Dots, xAI Grok Bot) | Well funded; Grok Bot is bundled with Cursor, which our first users already pay for | Focus on specific teams, Indian pricing and languages, model choice, checked work |
| Spreading too thin across four use cases | Each team is real work; doing all at once means none is good | One team at a time, each behind its own gate |
| AI video generation cost | Paid video models can cost more per video than creators will pay | Measure cost per video before pricing; offer cheaper styles (images + narration) |
| Operations team mistakes cost real money | Wrong refunds, wrong messages to customers | Approval rules, audit logs, start with low-risk jobs |
| Platform rules on AI content and automation | Social platforms label or limit AI content and automated posting | Follow each platform's API terms; label AI content; creator approves every post |
| No commitments yet (Gate 0) | Interest isn't demand | Ask every interviewee for a beta slot with a real project |

## Open questions

- How many people were in interview round 1, and from which segments?
- Exact prices per plan (after eval-suite cost data).
- Which Indian languages first for the content team?
- Who builds it: solo, or with a second full-time builder?
