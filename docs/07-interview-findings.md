# Interview findings (round 1)

Recorded Oct 1, 2026. Summarised by Pavan from early customer conversations, answering the seven questions in [06-customer-interview-guide.md](06-customer-interview-guide.md). Number of people and their segments: **not yet recorded**. Treat these as strong hypotheses until more interviews confirm them.

## Answers

| # | Question | What we heard |
| --- | --- | --- |
| 1 | Who feels the pain most? | **One-person companies:** solo founders, freelancers and one-person startups who take projects, build them and ship them |
| 2 | How do they build software today, and what does it cost? | Mostly **Claude Code, Cursor and other AI tools**. It costs them money, time and stress |
| 3 | What goes wrong? | AI coding tools work **prompt by prompt**. They don't treat the work as a project: no splitting it into tasks, no tracking. The person has to test everything and feed back themselves |
| 4 | Tried AI app builders (Lovable, Bolt, Replit, cto.new)? | About **10% yes, 90% no**. They see them as good products, but **none are Indian** |
| 5 | Do they care about owning code and accounts? | Hiring people, maintaining code and running a company is costly and a headache. They want a tool that **works on their project the way an IT company does**, with a **standup every morning** (what happened, what's planned today): "like me managing a real company" |
| 6 | Would they pay, and how? | **Subscription**, with flexibility: **pay as you go**, and **different prices for bringing your own** (local models, existing Claude or Cursor subscriptions) |
| 7 | Will they commit now? | **Not sure.** No commitments yet |

## What we concluded

1. **First users: solo builders in India** who already code with AI tools. Pitch: *"You're a one-person company. We give you the team."*
2. **The gap is project management, not code generation:** a backlog split into tasks, agents working through it day after day, QA, and a **daily standup**. The standup moves into the MVP.
3. **Work on their existing projects** (connect a GitHub repo), not only new apps from our template.
4. **Bring Your Own Model matters to this audience.** Move it earlier: own API keys and local models at a lower price; managed models with pay-as-you-go credits.
5. **India first.** Rupee pricing, Razorpay.

## Cautions

- **Gate 0 is not passed:** nobody has committed yet. Next conversations must end with a concrete ask: *"Connect one real repo for a 2-week beta in January; we'll run your backlog and send you a standup every morning."*
- **"Use my Claude or Cursor subscription"** can't be promised as asked. Cursor can't be driven by another product, and consumer Claude plans have their own terms for third-party tools. API keys are the safe route; check each provider's terms before offering more.
- **Not yet interviewed:** agencies and small businesses, and the new use cases (content creators, AI video, replacing workers). See [08-product-plan-v2.md](08-product-plan-v2.md).

## Next round

- Record for each interview: segment, role and the notes template from the guide.
- Add questions about Dots (OpenAI) and Grok Bot (xAI): "Have you tried them? What would you still need?"
- Show the office mock-up with the **standup and backlog** first.
- Interview 5+ content creators to test the second team before building it.
