# Competitors

Last updated Oct 1, 2026.

## Summary

| Competitor | What it is | Price point | Our difference |
| --- | --- | --- | --- |
| [cto.new](#ctonew) | General platform for AI agent teams running any business; marketplace of team templates | Free (ads) to $200/mo | Their teams do anything, shallowly; ours are built for one job each, with workflows and checks |
| [Dots (OpenAI)](#dots-openai) | Always-on ChatGPT agents with their own cloud computer; ChatGPT Space for agents + human teams | ChatGPT Pro and Business Premium | General agent you direct; one model family; top-tier price |
| [Grok Bot (xAI)](#grok-bot-xai) | Always-on agent with its own cloud computer; "teach a task" by screen recording; Team Bots | SuperGrok, and bundled with Cursor plans (access gated to top tiers) | Same as Dots; also bundled with Cursor, which our first users already pay for |
| [Claude Code, Cursor](#claude-code-and-cursor) | AI coding tools our first interviewees use daily | Developer subscriptions | They answer prompts; we run the project (backlog, QA, standups, release gates) |

**Where we win:** ready-made teams for specific jobs; Indian pricing and languages; your choice of models, including local; work that's checked before you see it. See [08-product-plan-v2.md](08-product-plan-v2.md).

## cto.new

Explored Sep 30, 2026 from a logged-in free account. The live workspace (Headquarters, task board, approvals in action) was not tested; no business was launched.

### What it is

A general platform for running any business with AI agent teams (marketing agencies, lead generation, content, services). Building software is one template among many.

- **Start:** one text box ("What business do you want to launch?") plus a model picker.
- **Team setup:** a Team Lead the founder chats with, who plans, hires and fires specialist agents, assigns tasks and reviews results. The team shares one context.
- **Visibility:** a Headquarters dashboard with approvals on top and a task board with outputs attached to tasks.
- **Approvals:** rules the founder sets ("refunds over $50 need sign-off", "approve the first email batch, auto-approve the rest").
- **Models:** about 15 in the picker (Claude Fable 5.1 and Opus 5, GPT 5.6, Gemini 3.8 Flash, DeepSeek, GLM, Kimi). "Auto model" is the default; each agent can use a different model; the best models are locked to higher plans. No bring-your-own-key.
- **Integrations:** MCP with one-click OAuth: GitHub, Vercel, Supabase, Neon, Linear, Notion, Sentry, PostHog, Render, Cloudflare, Brave Search, plus custom MCP servers.
- **Marketplace:** 1,580 team templates anyone can list and sell. The "Engineering Team" template (Technical Lead, backend, frontend, QA) shows 5,281 sold; setup is "connect a GitHub repo and describe what to build".

### Pricing (Sep 30, 2026)

| Plan | Price | Notes |
| --- | --- | --- |
| Free | $0 | Ad-supported, rolling 24-hour and 7-day usage limits |
| Pro | $20/mo | 5× limits, 7 models, email, webhooks, scheduled runs, payments, 10 published sites |
| Plus | $60/mo | 15× limits, 11 models, custom domain, no ads, 20 sites |
| Max | $200/mo | 50× limits, 12 models, 40 sites |
| Enterprise | Contact | Unlimited usage, custom models, no training on data |

### What it means for us

1. **Team structure and an office UI won't set us apart.** Their Engineering Team template is roughly our PM → CTO → Dev → QA lineup, free and widely used.
2. **Their weak spot is depth.** No fixed stack, no starter template, no step that runs the app, no staged gates around shipping. Our pitch: "Their agent teams do anything; ours ships working, tested software you own."
3. **BYOM is a weaker differentiator.** They already offer per-agent model choice. Keep BYOM as a higher-tier feature; copy their "Auto model" default and cost-labelled picker.
4. **Their free tier sets the price floor.** Charge for outcomes (per shipped app, or a Managed plan with a human expert when agents get stuck).
5. **Copy:** approval rules on top of fixed gates, tools via official MCP servers, a shared project context, rolling usage limits.
6. **Their marketplace is also a channel.** We could list a "Ship a Next.js app" template there.

### Open follow-up

Run their free Engineering Team template on the salon booking example (a fresh, empty GitHub repo) and judge the workspace, approvals, code quality, tests and deploy.


## Dots (OpenAI)

From news coverage; not used hands-on. Launched at OpenAI DevDay, Sep 29, 2026.

- Always-on ChatGPT agents, each with its **own cloud computer and browser**, pursuing user-set goals in the background and learning from feedback.
- Connect to 4,000+ services in OpenAI's ecosystem; Slack, messaging apps and voice access announced as coming.
- Launched alongside **ChatGPT Space**, where agents and human teams collaborate.
- Rolling out to ChatGPT Pro and Business Premium; Enterprise, Edu and Healthcare in beta.

**What it means for us:** confirms the always-on, approval-based agent direction; "watch your agents work" is no longer a differentiator; ChatGPT Space overlaps with our office idea.

Sources: [VentureBeat](https://venturebeat.com/technology/openai-launches-dots-always-on-ai-agent-coworkers-and-chatgpt-space-where-they-can-collaborate-with-human-teams), [BetaNews](https://betanews.com/article/openai-dots-agents-chatgpt/), [TechCrunch](https://techcrunch.com/2026/09/29/openai-launches-dots-its-bubbly-agentic-avatar/)

## Grok Bot (xAI)

From news coverage; not used hands-on. Beta since Aug 11, 2026.

- An agent with its **own cloud computer** that signs into your apps, runs multi-step tasks around the clock, and comes back only for approval.
- **Teach a task:** screen-record a workflow once and it becomes a repeatable skill.
- **Team Bots** (Sep 2026): shared bots with common context and memory across Slack and connected apps.
- Included with SuperGrok and Cursor Pro, Pro+, Ultra and Teams plans; access currently gated to SuperGrok Heavy, Cursor Ultra and Cursor Teams Premium.

**What it means for us:** bundled with Cursor, so many solo builders may get it at no extra cost. Our answer is project delivery on their repo, which a general agent doesn't do.

Sources: [Interesting Engineering](https://interestingengineering.com/ai-robotics/xai-grok-bot-computer-agent), [Digital Applied](https://www.digitalapplied.com/blog/grok-bot-ai-teammates-launch-cloud-computer-2026), [Releasebot](https://releasebot.io/updates/xai)

## Claude Code and Cursor

Not competitors in the usual sense: they're what our first interviewees build with today ([07-interview-findings.md](07-interview-findings.md)).

- **Gap they leave:** they work prompt by prompt. They don't split work into tasks, track it, test it, or report on it. The person does all of that.
- **Our relationship to them:** complementary. A Claude Agent SDK developer engine (for users with Claude API keys) can run inside our software team.
