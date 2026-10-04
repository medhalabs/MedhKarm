# Local setup

**Last updated:** 2026-10-01

How to get MedhKarm running on a new machine. About 10 minutes.

## Prerequisites

| Tool | Version used | Check |
| --- | --- | --- |
| Node.js | 24+ (tested on 26) | `node -v` |
| npm | 11+ | `npm -v` |
| Python | 3.13 (uv installs it if missing) | `python3 --version` |
| uv | 0.8+ | `uv --version` |
| Docker Desktop | any recent | `docker info` |

## 1. Start Postgres and Redis

From the repo root:

```bash
docker compose up -d --wait
```

| Service | Host port | Credentials |
| --- | --- | --- |
| Postgres 17 + pgvector | **5442** (not 5432, to avoid clashing with other local Postgres instances) | user `medhkarm`, password `medhkarm`, db `medhkarm` |
| Redis 7 | 6379 | none |

Stop them with `docker compose stop`; delete all local data with `docker compose down -v`.

## 2. Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

- API: http://127.0.0.1:8000 · interactive docs: http://127.0.0.1:8000/docs · health: http://127.0.0.1:8000/health
- Before pushing: `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests && uv run lint-imports && uv run pytest`
- Tests that need real Docker: `uv run pytest -m integration`

### Run a build (agents writing code)

The normal way: the API and a worker, each in its own terminal. Both need `OLLAMA_API_KEY` in `backend/.env` and Docker running (steps 1–2 below).

```bash
uv run uvicorn app.main:app --port 8000     # terminal 1
uv run python -m app.workers.main           # terminal 2 (run more for more capacity)
```

```bash
curl -X POST 127.0.0.1:8000/runs -H 'content-type: application/json' \
  -d '{"request": "Create slugify.py with slugify(text) and pytest tests in test_slugify.py", "test_command": "pip install -q pytest >/dev/null 2>&1; python -m pytest -q"}'
curl 127.0.0.1:8000/runs/<run_id>                       # status: queued, running, waiting_for_approval, ...
curl 127.0.0.1:8000/runs/<run_id>/events                # what the team did
curl -X POST 127.0.0.1:8000/runs/<run_id>/approval -H 'content-type: application/json' -d '{"approved": true}'
```

Or from the command line, without the API or a worker:

1. Get an Ollama Cloud key at https://ollama.com/settings/keys and set `OLLAMA_API_KEY` in `backend/.env`. Never commit it.
2. Make sure Docker Desktop and Postgres (`docker compose up -d`) are running.
3. Start a run. It plans, writes code in a fresh Docker sandbox, re-runs the tests, then pauses at the release gate:

   ```bash
   uv run python -m app.workers.build_run start \
     --request "Create slugify.py with slugify(text) and pytest tests in test_slugify.py" \
     --test-command "pip install -q pytest >/dev/null 2>&1; python -m pytest -q"
   ```

4. Approve or reject it, from any terminal, any time later:

   ```bash
   uv run python -m app.workers.build_run resume <run_id> --approve
   ```

To work on an existing GitHub repository, add `--repo https://github.com/owner/name` (and `--branch` if not the default); the test command is then detected. Without `--repo`, a released run creates a new private repository with the work (`--new-repo-name`, or `--no-new-repo` to skip). For private repositories, pull requests and new repositories, set `GITHUB_TOKEN` in `backend/.env`: a fine-grained token with Contents and Pull requests read and write on those repositories ([features/repos.md](features/repos.md)).

See everything the team did, step by step: `uv run python -m app.workers.build_run events <run_id>`.

Check a finished run against Gate 1 (team from config, 10+ steps, approval, restart, logging, cost, standup): `uv run python -m app.workers.gate_check <run_id>`.

The first run builds the `medhkarm-sandbox:3` image (Python, Node, pytest, Graphify; a minute or two, once). After pulling changes to `backend/sandbox-image/`, rebuild it: `docker build -t medhkarm-sandbox:3 backend/sandbox-image`. Details: [features/workflows.md](features/workflows.md).

### Run the eval suite

```bash
uv run python -m app.workers.run_evals validate   # no model needed; checks the 20 tasks are fair
uv run python -m app.workers.run_evals run        # all 20 tasks through the software team
```

The first run builds the `medhkarm-sandbox:3` image (about a minute). Details: [features/evals.md](features/evals.md).

To use the OpenHands engine instead, add `--engine openhands` (or set `DEVELOPER_ENGINE=openhands` in `backend/.env`). Pull its 1.2 GB image once beforehand so the first run doesn't wait:

```bash
docker pull ghcr.io/openhands/agent-server:1.50.1-python
```

## 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

- App: http://localhost:3000. The home page shows **"Backend OK · MedhKarm API v0.1.0 (development)"** when the backend is reachable.
- Admin page: http://localhost:3000/admin. Start runs, watch them live and approve releases. Needs the API and a worker running (section 2).
- In Claude Code's desktop app, `.claude/launch.json` starts the API (`api`) and the frontend (`frontend`) in the browser pane; start the worker in a terminal.
- Before pushing: `npm run lint && npm run typecheck && npm test && npm run format:check`

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Home page says "Backend unreachable" | Backend not running, or wrong URL | Start the backend; check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` is `http://127.0.0.1:8000` |
| Backend running but frontend still can't reach it | `localhost` resolves to IPv6 (`::1`) while uvicorn listens on IPv4 only | Use `127.0.0.1`, not `localhost`, in `NEXT_PUBLIC_API_URL` |
| `docker compose up` fails: port 5432 / 5442 already in use | Another Postgres is using the port | Change the host port in `docker-compose.yml` and `DATABASE_URL` in `backend/.env` together |
| `npm install` fails with ERESOLVE on `@types/node` | Old Node types vs Vitest | Keep `@types/node` at `^24` or newer |
| Alembic can't connect | Postgres not up, or `.env` missing | `docker compose ps`; `cp .env.example .env` in `backend/` |
| Build run fails with `ModelCallError` | Missing/wrong `OLLAMA_API_KEY`, or Ollama Cloud outage | Check `backend/.env`; retry later or change `DEFAULT_MODEL` |
| Leftover sandbox containers | A run crashed before `finish` | `docker rm -f $(docker ps -aq --filter label=medhkarm.sandbox)` |
