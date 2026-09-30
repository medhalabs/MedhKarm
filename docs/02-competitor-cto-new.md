# Competitor: cto.new

Explored Sep 30, 2026 from a logged-in free account. The live workspace (Headquarters, task board, approvals in action) was not tested; no business was launched.

## What it is

A general platform for running any business with AI agent teams (marketing agencies, lead generation, content, services). Building software is one template among many.

- **Start:** one text box ("What business do you want to launch?") plus a model picker.
- **Team setup:** a Team Lead the founder chats with, who plans, hires and fires specialist agents, assigns tasks and reviews results. The team shares one context.
- **Visibility:** a Headquarters dashboard with approvals on top and a task board with outputs attached to tasks.
- **Approvals:** rules the founder sets ("refunds over $50 need sign-off", "approve the first email batch, auto-approve the rest").
- **Models:** about 15 in the picker (Claude Fable 5.1 and Opus 5, GPT 5.6, Gemini 3.8 Flash, DeepSeek, GLM, Kimi). "Auto model" is the default; each agent can use a different model; the best models are locked to higher plans. No bring-your-own-key.
- **Integrations:** MCP with one-click OAuth: GitHub, Vercel, Supabase, Neon, Linear, Notion, Sentry, PostHog, Render, Cloudflare, Brave Search, plus custom MCP servers.
- **Marketplace:** 1,580 team templates anyone can list and sell. The "Engineering Team" template (Technical Lead, backend, frontend, QA) shows 5,281 sold; setup is "connect a GitHub repo and describe what to build".

## Pricing (Sep 30, 2026)

| Plan | Price | Notes |
| --- | --- | --- |
| Free | $0 | Ad-supported, rolling 24-hour and 7-day usage limits |
| Pro | $20/mo | 5× limits, 7 models, email, webhooks, scheduled runs, payments, 10 published sites |
| Plus | $60/mo | 15× limits, 11 models, custom domain, no ads, 20 sites |
| Max | $200/mo | 50× limits, 12 models, 40 sites |
| Enterprise | Contact | Unlimited usage, custom models, no training on data |

## What it means for us

1. **Team structure and an office UI won't set us apart.** Their Engineering Team template is roughly our PM → CTO → Dev → QA lineup, free and widely used.
2. **Their weak spot is depth.** No fixed stack, no starter template, no step that runs the app, no staged gates around shipping. Our pitch: "Their agent teams do anything; ours ships working, tested software you own."
3. **BYOM is a weaker differentiator.** They already offer per-agent model choice. Keep BYOM as a higher-tier feature; copy their "Auto model" default and cost-labelled picker.
4. **Their free tier sets the price floor.** Charge for outcomes (per shipped app, or a Managed plan with a human expert when agents get stuck).
5. **Copy:** approval rules on top of fixed gates, tools via official MCP servers, a shared project context, rolling usage limits.
6. **Their marketplace is also a channel.** We could list a "Ship a Next.js app" template there.

## Open follow-up

Run their free Engineering Team template on the salon booking example (a fresh, empty GitHub repo) and judge the workspace, approvals, code quality, tests and deploy.
