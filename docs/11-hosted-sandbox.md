# Hosted sandbox: which one runs customers' code

**Decided Oct 5, 2026: Daytona** (Pavan). **When:** from the beta (Phase 3). Until then Pavan is the only user and runs stay on local Docker.

**Ready:** `DaytonaSandboxProvider` is built and unit-tested. To switch: create a Daytona account, put `DAYTONA_API_KEY` in `backend/.env`, set `SANDBOX_PROVIDER=daytona`, and run the evals on it once ([sandbox.md](technical/features/sandbox.md)).

Today every run gets a Docker container on this laptop (gap G-11). Beta users' code must run on someone else's machines. Our code already talks to sandboxes through one interface (`SandboxProvider`: create, attach by id, run, read/write/list files, destroy), so a hosted provider is one new class. Nothing else changes.

## What a run needs

- **Our image:** Python, Node 22 with npm, Playwright with Chromium, Semgrep, plus the starter's npm cache. That's 3.24 GB.
- **Resources:** about 2 vCPU and 2 GB. The Next.js build fits in 1 CPU / 1 GB, but tightly.
- **Run length:** 2 to 30 minutes of work. Then it **waits at the founder's gate** for hours or days, so pausing a sandbox and resuming it later matters more than the price per second.
- **Network** for installing packages and running dependency audits.

## The four options (list prices, Oct 2026)

| | E2B | Daytona | Modal Sandboxes | Fly Machines |
| --- | --- | --- | --- | --- |
| Price | $0.0504 per vCPU-hour + $0.0162 per GiB-hour, billed per second | Same rates as E2B; storage billed separately (tiny) | $0.1419 per physical core-hour (= 2 vCPU) + $0.0242 per GiB-hour | performance-2x (2 CPUs, 4 GB) ≈ $0.089 per hour; shared CPUs much cheaper |
| A 15-minute run at 2 vCPU / 2 GB | ≈ $0.033 (≈ ₹3) | ≈ $0.033 (≈ ₹3) | ≈ $0.048 (≈ ₹4) | ≈ $0.022 (≈ ₹2) |
| Monthly fee | Free Hobby tier; Pro $150/month for longer sessions and more concurrency | None (prepaid wallet) | None (pay as you go) | None |
| Isolation | Firecracker microVMs | Containers/VMs; open source, can self-host | gVisor (the reason for its 3× sandbox price) | Firecracker microVMs |
| Our 3.24 GB image | Custom templates built from a Dockerfile | Any Docker/OCI image | Any image | Any image |
| Waiting at the gate | Pause and resume (state kept) | Stop and start, or archive (files kept) | Sandboxes time out (max 24 h); keep files in a volume or snapshot | Stop and start with a volume |
| Work for us | Small: SDK with run, files and pause | Small: SDK with run, files and stop | Small: SDK; resume needs snapshots | Most: we build the exec and files layer ourselves |

Compute is cheap everywhere: about ₹2–4 a run, against model tokens worth ₹8–150 a run at Claude prices (eval runner, Oct 4). **The choice comes down to waiting at the gate and engineering effort, not price.**

## Recommendation

**Daytona, with E2B as the fallback.**

- **Same compute price as E2B, and no monthly fee**, which matters for a 10–20 user beta.
- **Stop or archive keeps the workspace** while a run waits days for the founder, without paying for compute in the meantime.
- **Runs our Docker image as it is.** It's also open source, so we could host it ourselves later (in India) if needed.
- **Why E2B is the fallback:** it's the most mature, and pause/resume is built for exactly this. But longer sessions need the $150/month Pro plan.
- **Why not the others:** Modal costs more and times sandboxes out after 24 hours. Fly is cheapest, but we'd build the sandbox layer ourselves.

**Next step once you decide:** a `DaytonaSandboxProvider` (about a day), with the eval suite run on it to compare against Docker.

## Sources

- [E2B pricing breakdown (Morph)](https://www.morphllm.com/e2b-pricing)
- [Daytona pricing (Costbench)](https://costbench.com/software/ai-code-execution/daytona/)
- [Modal pricing (Morph)](https://www.morphllm.com/modal-pricing)
- [Fly.io resource pricing](https://fly.io/docs/pricing/)
- [AI sandbox pricing compared (Fly.io)](https://fly.io/learn/ai-sandbox-pricing/)
