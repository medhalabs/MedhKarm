# Technology stack

Decided Oct 1, 2026. A Next.js frontend over a Python backend, Postgres on Supabase, and LangGraph for orchestration so every agent can run on any model.

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js | UI only; business logic stays in the backend |
| Backend | Python, uv, FastAPI, Pydantic | Agent, workflow and model libraries are strongest in Python |
| Database | Postgres on Supabase, with pgvector | Relational data, JSONB for agent output, embeddings, row-level security, plus auth, storage and realtime |
| Database access | SQLAlchemy 2.0 async (or SQLModel), Alembic, asyncpg | Typed models and versioned migrations |
| Frontend ↔ backend | TypeScript client generated from FastAPI's OpenAPI spec | Types always match; Supabase handles sign-in and FastAPI checks its token |
| Orchestration | LangGraph with Postgres checkpoints | Works with any model; `interrupt()` for approval gates; runs survive restarts. Replaces Temporal for the MVP |
| Background jobs | Postgres job table (`FOR UPDATE SKIP LOCKED`, leases, retries), chosen Oct 1, 2026 over arq on Redis | Durable and visible, one less service; workers run graphs and the morning standup ([jobs.md](technical/features/jobs.md)) |
| Model layer | LiteLLM; development default `ollama_chat/gpt-oss:20b` on Ollama Cloud (free tier); paid models later for customers | One interface for Claude, OpenAI, Gemini, Ollama and others |
| Developer engine | Two engines behind one `DeveloperEngine` interface: built-in tool loop (default) and OpenHands SDK 1.50 (`DEVELOPER_ENGINE=openhands`) | Model-agnostic; the Claude Agent SDK can be added later for Claude users |
| Sandbox | Docker locally, behind a `Sandbox` interface; hosted sandbox chosen in Phase 2 | Isolated environment per project; see below |
| Tracing and costs | Langfuse | Works with LangGraph; tokens and cost per agent and task |

## Why Postgres

| Need | How Postgres covers it |
| --- | --- |
| Companies, projects, agents, tasks, approvals, billing | Relational tables with foreign keys |
| Agent output of varying shape | `JSONB` columns, queryable and indexable |
| Event log for the office, reports and costs | Append-only table; partition by month once large |
| Project memory and search | `pgvector` in the same database |
| Live office updates | Supabase Realtime or `LISTEN/NOTIFY` |
| Tenant isolation | Row-level security |
| Workflow state | LangGraph checkpoints in the same Postgres |

Hosting: **Supabase** (auth, storage, realtime, same service as generated apps). Alternatives: Neon (instant database copies for testing), AWS RDS (later, for enterprise compliance).

## Why LangGraph over the Claude Agent SDK

The Claude Agent SDK runs only Claude models, which conflicts with letting customers pick any model per agent. LangGraph is model-agnostic and provides:

| Need | LangGraph feature |
| --- | --- |
| Approval gates | `interrupt()` pauses; resumes on founder approval |
| Long-running, restart-safe runs | Postgres checkpointer (`langgraph-checkpoint-postgres`) |
| Fixed pipeline PM → CTO → Dev → QA → DevOps | Graph nodes and edges; QA failure loops back to Dev |
| Team Lead delegating | Supervisor pattern with agents as subgraphs |
| Live office feed | Step streaming into the event log |

**Gap:** LangGraph is orchestration only; it has no built-in coding agent. The Developer uses OpenHands (model-agnostic, via LiteLLM) running in the sandbox.

## Why Docker for the sandbox, for now

Decided Oct 1, 2026. Agents run code they wrote plus packages from the internet (`npm install`, builds, tests), so it always runs in an isolated sandbox, never on our servers directly.

- **Now (local development, Phase 0–1):** Docker on the developer's machine. Only our own code runs, and OpenHands uses Docker as its default sandbox.
- **Later (Phase 2, before customer code runs):** a hosted VM sandbox, chosen then on price and features. Candidates: E2B, Fly Machines, Daytona, Modal. Docker containers share the host kernel, which is too weak isolation for many customers' untrusted code, and we'd have to scale and manage the machines ourselves.
- **Why switching is cheap:** all code talks to a `Sandbox` interface (`backend/app/features/sandbox/interfaces.py`); Docker and the hosted option are two implementations of it.

## Rules

- Use LangGraph, not all of LangChain: tools and prompts stay plain Python and Pydantic; LangChain only for model calls.
- The Developer is a contract, "task + repo in, diff + test results out", so the engine behind it can change (OpenHands now; Claude Agent SDK for Claude users later) without touching the graph.
- Test tool calling for each model early: a "model × role" test joins the eval suite in Phase 2.
- Decide auth ownership once: Supabase handles sign-in; FastAPI verifies the Supabase token on every request.
