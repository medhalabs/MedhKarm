# Gate 2 report: the software team

**Date:** Oct 5, 2026 (planned for Nov 27). **Result: passed.** All three criteria are met; one Phase 2 item (model × role tests) waits for a paid-model key.

| Criterion | Result |
| --- | --- |
| At least 12 of 20 eval tasks pass without help | **18 of 20 (90%)**, built-in engine, gpt-oss:20b (free) |
| Cost and time per task known | **Median 7 min 16 s and 119k tokens per task**; cost per task below |
| Prices drafted from those numbers | **Draft below**, to test with beta users |

## The eval run (Oct 5, 2026)

The first run with the whole team: Kabir (CTO) plans and reviews; specialist developers; QA's tests, build, type-check and lint with one fix round; Tara's browser tests; Vikram's security scans. Results: `backend/evals/results/2026-10-04T160442Z-builtin.md`.

| | Passed |
| --- | --- |
| Bugs | 3 of 3 |
| Features | 11 of 12 |
| New modules | 2 of 3 |
| Refactor | 1 of 1 |
| JavaScript | 5 of 5 |
| Python | 13 of 15 |

- **Failed:**
  - `book-feature-reminders`: timed out at 20 minutes after 81 model calls.
  - `new-py-slugify`: used all 100 steps; its tests passed for the developer, but not our hidden ones.
- **Spread:** the cheapest task took 25k tokens (131 s), the most expensive 469k (20 min).
- **Totals:** 4.0 million tokens and about 2.8 hours of work for all 20 (about 1.5 hours of waiting, running 2 at a time).

### Live end-to-end checks (same day)

- **Starter:** a cafe feedback wall reached the release gate.
  - Neel set up the Next.js starter with sign-in and the admin dashboard; Kabir sent the API to Isha and the pages to Arjun.
  - QA caught a lint and a build error, and the fix round solved them.
  - Tara's browser test passed, Vikram found nothing, and Neel's preview was ready.
  - The first attempt failed. The developers ignored the starter's data layer, and the starter's rules now go into every brief.
- **Backlog:** Mira planned "Tip splitter". Item 1 created the private repo; item 2 cloned it, built on it and opened a pull request, which merged on approval.
- **Production deploy:** the word counter is live on Vercel and answers correctly.

## Cost per task

**What we pay per task:**
- **Model tokens:** this run cost ₹0 (free tier). The same tokens at Claude list prices, without prompt caching:

  | Model | Per task (mean) | Per passed task |
  | --- | --- | --- |
  | Claude Haiku 4.5 | ₹22 | ₹25 |
  | Claude Sonnet 5.5 | ₹44 | ₹49 |
  | Claude Opus 5.5 | ₹89 | ₹99 |

  About 93% of the tokens are repeated input (the conversation so far), which prompt caching bills at a tenth of the price. That should bring Sonnet-class cost to about **₹12–15 for a median task** and about ₹55 for the biggest. Each model also uses its own number of tokens, so these are estimates until a paid model runs the suite.
- **Sandbox:** about ₹3 a run (Daytona, 2 vCPU / 2 GB, 15 minutes). Today it's ₹0, on this laptop.
- **Previews and hosting:** ₹0 on Vercel's free plan for now.

**So:** about **₹15–20 for a typical task** on a Sonnet-class model with caching, and ₹60 for a big one. Small models cost less but fail more, and failures cost too (the fix round, retries).

## Draft prices (₹, plus GST; to test with beta users)

| Plan | Price | Includes |
| --- | --- | --- |
| **Bring your own** | ₹799 / month | The office, standups, approvals, backlog, QA, security and previews. You connect your own API keys or local models and pay their bills. Sandbox up to 100 runs a month |
| **Managed** | ₹1,999 / month | Everything above with our models, plus **₹1,000 of task credit** (about 30–60 typical tasks) |
| **Top-up credit** | from ₹500 | Pay as you go after the included credit |
| **Expert fix** | ₹499 per stuck task | A person finishes what the team couldn't (us, during the beta) |

**How a task is charged:** the measured model and sandbox cost × 2. That's roughly ₹30 for a typical task and ₹100–120 for a big one. Mira's size estimate (S / M / L) shows the expected price before a task starts, and the standup shows what was spent.

**Why these numbers:**
- ₹1,999 sits below a Cursor or Claude subscription plus a freelancer.
- The ×2 margin covers failed attempts (10% in the evals), support and payment fees.
- Bring-your-own at ₹799 answers the interviews' ask for a lower price with your own keys.

**To find out in the beta:** how many tasks a solo founder runs a month (our guess: 30–60), whether founders prefer per-task prices or a monthly bundle, and whether ₹799 / ₹1,999 feel right next to what they already pay.

## What's still open

- **Model × role tests** (which model in which seat) need at least one paid-model key. The free model already passes 18 of 20, so this is about quality and the hard tasks (G-01), not about passing Gate 2.
- **Nightly evals:** switch on with `EVAL_NIGHTLY=true` once you're happy to spend the free quota nightly.
- **Prompt caching** in our model calls (G-32), before running paid models at scale.
- `usd_to_inr` in `backend/evals/prices.toml` is still the placeholder ₹88.
