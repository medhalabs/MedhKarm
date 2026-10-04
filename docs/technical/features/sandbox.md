# Sandbox

**Status:** Done for local development (Phase 0): plain Docker and OpenHands agent server  
**Code:** `backend/app/features/sandbox/`  
**Last updated:** 2026-10-01

## What it is

An isolated, throwaway workspace where agents write and run code, so AI-written code and downloaded packages never run on our own machines directly. Each build run gets its own sandbox. Today it's a local Docker container; a hosted VM sandbox replaces it in Phase 2 behind the same interface (see [04-tech-stack.md](../../04-tech-stack.md)).

## How it works

1. `DockerSandboxProvider.create()` starts a container from `SANDBOX_IMAGE` (default `medhkarm-sandbox:4`: Python, Node 22 with npm, pytest, the Next.js starter's packages in the npm cache; built from `backend/sandbox-image/` on first use by `ensure_sandbox_image()` in `app/workers/wiring.py`) running `sleep infinity`, labelled `medhkarm.sandbox=true`, limited to 1 CPU and 1 GB of memory. The workspace is `/workspace`.
2. `run(command, timeout_seconds)` executes via `docker exec` wrapped in `timeout`; exit code 124 means it timed out. Output is stdout and stderr combined.
3. `write_file` uploads a tar archive; `read_file` runs `cat`; `list_files` lists files, skipping hidden folders and `__pycache__`.
4. Every path goes through `safe_relative_path()`: absolute paths and `..` are refused with `UnsafePathError`.
5. The sandbox's id is the container id. `attach(id)` reconnects to it, which lets a paused run continue in a different process. `destroy(id)` removes it.

### Daytona (hosted, from the beta)

`DaytonaSandboxProvider` (`providers/daytona_provider.py`, chosen Oct 5, 2026: [11-hosted-sandbox.md](../../11-hosted-sandbox.md)):
- Same contract and the same image: built from `backend/sandbox-image/`'s Dockerfile (Daytona caches the build), or from a prepared snapshot (`DAYTONA_SNAPSHOT`). 2 vCPU, 2 GB, 10 GB disk; workspace `/workspace`; labelled `medhkarm=sandbox`.
- Commands run through `process.exec` wrapped in `timeout`, like Docker; files go through `fs.upload_file` / `fs.download_file`.
- After 30 minutes without activity a sandbox **stops and keeps its files**. A run waiting days at the founder's gate costs storage only, and `attach` starts the sandbox again.
- Switch with `SANDBOX_PROVIDER=daytona` and `DAYTONA_API_KEY` (optional `DAYTONA_TARGET`, default `us`). The default stays `docker` while Pavan is the only user.
- Unit-tested with a fake client. Not yet run against Daytona (no account until the beta).

### OpenHands agent-server sandbox

Used with the OpenHands developer engine (`DEVELOPER_ENGINE=openhands`).

1. `OpenHandsSandboxProvider.create()` starts `OPENHANDS_SERVER_IMAGE` (`ghcr.io/openhands/agent-server:1.50.1-python`, about 1.2 GB, native arm64 on Apple Silicon) with the Docker SDK. It gets 2 CPUs, 4 GB of memory and a random host port bound to `127.0.0.1` only, and is labelled `medhkarm.sandbox.kind=openhands`.
2. It waits for the server's `/health` endpoint (up to 120 s; about 5 s in practice), then talks to it through OpenHands' `RemoteWorkspace` over HTTP.
3. The project lives in `/workspace/project`. The agent server writes its own logs to `/workspace/bash_events`, which stay out of the project's file list.
4. It implements `AgentServerSandbox`: a `Sandbox` that also exposes `agent_server_url` and `workspace_dir`, which is what the OpenHands engine needs.
5. `attach(id)` reads the container's published port with `docker inspect` and reconnects.

## Code map

| File | Responsibility |
| --- | --- |
| `interfaces.py` | `SandboxCommands`, `SandboxFiles`, `Sandbox`, `AgentServerSandbox`, `SandboxProvider` Protocols |
| `schemas.py` | `CommandResult` (`exit_code`, `output`, `ok`) |
| `paths.py` | `safe_relative_path()`: keeps every path inside the workspace |
| `providers/docker_provider.py` | `DockerSandbox`, `DockerSandboxProvider` |
| `providers/openhands_provider.py` | `OpenHandsSandbox`, `OpenHandsSandboxProvider` (agent-server container) |
| `providers/memory_provider.py` | In-memory sandbox for tests; commands answered by a function you pass in |
| `exceptions.py` | `SandboxError`, `SandboxNotFoundError`, `UnsafePathError` |

## API

None (used in-process by workflows and the developer engine).

## Data model

None. Only the sandbox id is stored, inside the workflow checkpoint.

## Events

None yet.

## Dependencies

- **Other features used:** none
- **Interfaces defined:** `SandboxProvider`, `Sandbox` → Docker and in-memory implementations
- **External services:** Docker Engine (Docker Desktop locally), `docker` Python SDK
- **Config:** `SANDBOX_IMAGE`, `OPENHANDS_SERVER_IMAGE`

## Design decisions

- 2026-10-01 — Docker locally, hosted VM sandbox from Phase 2. Only our own code runs for now; containers share the host kernel, which isn't enough isolation for customers' code.
- 2026-10-01 — Commands and files are separate small interfaces (interface segregation); `Sandbox` combines them.
- 2026-10-01 — Network is on by default so `pip install` / `npm install` work; `network_enabled=False` turns it off. Finer rules (allow-list) come with the hosted sandbox.
- 2026-10-01 — The agent-server container is started by us, not by OpenHands' `DockerWorkspace`: `DockerWorkspace` stops its container when the Python object is garbage-collected, which would kill a sandbox while its run waits for approval.
- 2026-10-01 — The image tag is pinned to the installed `openhands-sdk` version so client and server match.
- 2026-10-01 — The Docker SDK is synchronous, so each call runs in a thread (`asyncio.to_thread`) to keep the event loop free.

## How to run and test

- Unit tests: `uv run pytest app/features/sandbox`
- Against real Docker (both providers): `uv run pytest -m integration app/features/sandbox`

## Known limitations and gotchas

- One image for every project; stack-specific images (Node + Python) come with the app template.
- A crashed run can leave containers behind. List them with `docker ps --filter label=medhkarm.sandbox`; remove with `docker rm -f $(docker ps -aq --filter label=medhkarm.sandbox)`.
- First `create()` pulls the image, which takes longer.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `docker.errors.DockerException: Error while fetching server API version` | Docker Desktop not running | Start Docker Desktop |
| `SandboxNotFoundError` on resume | Container was removed (manually or by a reboot) | Start a new run; sandbox persistence arrives with the hosted sandbox |
| Command exit code 124 | Hit the timeout | Raise `timeout_seconds` or make the command faster |
| `Agent server ... not healthy after 120s` | Image still downloading, or Docker short on memory | `docker pull` the image first; give Docker Desktop at least 6 GB |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-05 | `DaytonaSandboxProvider` (hosted, for customers' code from the beta) behind `SANDBOX_PROVIDER` (default `docker`); `daytona` SDK added |
| 2026-10-05 | `list_files` skips dependency and cache folders (`node_modules`, `venv`, `__pycache__`, hidden folders): on the starter, a listing went from 22,229 files (about 324k tokens, past the model's limit) to 53 |
| 2026-10-05 | Image `medhkarm-sandbox:4`: Node 22 with npm and corepack from the official image (Debian's `nodejs` had no npm, so JavaScript projects couldn't install); the Next.js starter's packages pre-loaded in the npm cache (`/opt/medhkarm/npm-cache`), so it installs offline in about 9 s; 3.24 GB. The starter's install, tests, type-check, lint and build fit the 1 CPU / 1 GB limit (about 41 s) |
| 2026-10-04 | Image `medhkarm-sandbox:3`: adds Playwright 1.63.0, pytest-playwright 0.9.0, uvicorn and headless Chromium (image 2.86 GB, from 1.21 GB) |
| 2026-10-04 | Image `medhkarm-sandbox:2`: adds Semgrep 1.179.0, pip-audit 2.10.1 and `/opt/medhkarm/semgrep.yml` |
| 2026-10-01 | `medhkarm-sandbox:dev` image gains `graphifyy==0.9.73` (code graph, about 100 MB); rebuild with `docker build -t medhkarm-sandbox:dev backend/sandbox-image` |
| 2026-10-01 | Default image is now `medhkarm-sandbox:dev` (has pytest), built automatically when missing: with plain `python:3.13-slim`, developers faked pytest |
| 2026-10-01 | Added the OpenHands agent-server sandbox and `AgentServerSandbox` |
| 2026-10-01 | Created: Docker and in-memory sandboxes, path guard, attach by id |
