# Teams (team templates)

**Status:** Done (Phase 1, step 2): software team template  
**Code:** `backend/app/features/teams/` · templates in `backend/app/features/teams/templates/` · wiring in `backend/app/workers/wiring.py`  
**Last updated:** 2026-10-01

## What it is

A team is a **settings file**, not code. Each template lists the team's roles (title, office name, responsibilities, the instructions that shape how the agent behaves, the tools it may use, its model, how many of it), which workflow the team runs, and how its work is checked. The software team is `templates/software.toml`. Changing how an agent behaves means editing its `instructions` in that file, and the content and operations teams later are new files, not new code.

## How it works

1. `load_templates()` reads every `templates/*.toml` file and **rejects** anything the platform can't run: unknown tools, an unknown workflow or checker, duplicate roles, a workflow whose required roles aren't active, too few display names, `count` above `max_count`.
2. `build_team_runtime(settings)` (in `app/workers/wiring.py`) picks the template named by `TEAM_TEMPLATE` (default `software`) and builds the agents from it:
   - **CTO** → the planner: the role's `model` and `instructions`
   - **Developer** → the developer engine: the role's `model`, `tools`, `instructions`, `max_steps` and `mcp` grants (MCP servers it may use, with limits: [integrations.md](integrations.md))
   - **QA** → the checking step named by the template's `checker` (`test_command` today)
3. The template's `[approval]` section holds the team's **approval rules** for the release gate ([approvals.md](approvals.md)); the loader rejects rules that use facts the workflow doesn't provide (`WORKFLOW_FACTS` in `catalog.py`).
4. `TeamService.assemble()` lists who's on the team: each active role, `count` times, named from `display_names` in order. The office and the API use this.

### The software team

| Role | Name in the office | Active | What it does today |
| --- | --- | --- | --- |
| `pm` Product Manager | Mira | No (Phase 2) | Will ask questions and show screens |
| `cto` CTO | Kabir | Yes | Splits the request into tasks and assigns developers (`instructions`), reviews each task (`review_instructions`) |
| `developer` Developer (1–3, chosen by the CTO per run) | Isha, Arjun, Ravi | Yes | Writes code and tests with `read_file`, `write_file`, `list_files`, `run_command`, `finish`, plus the `python_docs` MCP tools (read-only, 10 calls per task); up to 25 steps |
| `qa` QA engineer | Tara | Yes | Runs the test command (`checker = "test_command"`) |
| `devops` DevOps | Neel | No (Phase 2) | Will deploy previews and releases |

Role ids are also the actors in the activity log ([events.md](events.md)).

## Code map

| File | Responsibility |
| --- | --- |
| `templates/software.toml` | The software team |
| `catalog.py` | The vocabulary templates may use: `KNOWN_TOOLS`, `WORKFLOW_ROLES` (roles each workflow needs), `KNOWN_CHECKERS`, `WORKFLOW_FACTS` (facts approval rules may use) |
| `schemas.py` | `RoleSpec` (with `mcp` grants), `TeamTemplate` (with its `approval` policy), `TemplateSummary`, `TeamMember`, `Team` |
| `loader.py` | `load_templates()`, `parse_template()` with validation |
| `service.py` | `TeamService`: list, get, assemble |
| `exceptions.py` | `InvalidTemplateError`, `TemplateNotFoundError` |
| `dependencies.py`, `router.py` | API |
| `app/workers/wiring.py` | `build_team_runtime()`, `build_engine(settings, role)` |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/teams/templates` | All templates: id, name, description, active role titles | None yet |
| GET | `/teams/templates/{id}` | One template in full (roles, instructions, tools) | None yet |
| GET | `/teams/templates/{id}/team` | The default team: each member's role, title and name | None yet |

Unknown id → 404 `team_template_not_found`.

## Data model

None in the database. Templates are files in the repository, read once per process.

## Events

None of its own. Role ids are the `actor` values in the activity log; `Actor` in `events/schemas.py` includes every role id used by a template (a test checks this).

## Dependencies

- **Used by:** `app/workers/wiring.py` (build command and eval runner)
- **Config:** `TEAM_TEMPLATE` (default `software`); `BUILTIN_MAX_STEPS` is the fallback when a role sets no `max_steps`; `BUILTIN_APPLY_PATCH=true` adds `apply_patch` to the developer's tools

## Design decisions

- 2026-10-01 — Templates are TOML files in the repo (versioned, reviewed like code), not database rows. Customer-editable teams can move to the database later without changing the schema.
- 2026-10-01 — Strict validation at load time with a fixed vocabulary (`catalog.py`): a typo in a template fails at startup, not halfway through a customer's build. Tests keep the vocabulary in sync with the engine's tools and the activity log's actors.
- 2026-10-01 — PM and DevOps are defined now but `active = false`, so the office and the plan can show the whole team while the workflow only uses roles that exist in code.
- 2026-10-01 — Each role may name its own model, so e.g. a stronger model for the CTO and a cheaper one for developers is a one-line change.

## How to run and test

- Unit tests: `uv run pytest app/features/teams tests/test_team_wiring.py`
- See the team: `curl http://127.0.0.1:8000/teams/templates/software/team`
- Try a different behaviour: edit a role's `instructions` in `software.toml`, then run a build (see [workflows.md](workflows.md)).

## Adding a team

1. Copy `templates/software.toml` to `templates/<id>.toml` and change roles, tools and instructions.
2. If it needs a new tool, workflow or checker, implement it and add its name to `catalog.py` (the loader rejects unknown names).
3. Add any new role ids to `Actor` in `events/schemas.py`.
4. Run the tests; the shipped-templates test loads every file.

## Known limitations and gotchas

- One workflow (`build_app`) and one checker (`test_command`) exist; human review and approval rules come with later teams.
- Templates are cached per process: restart the API or worker after editing one.
- The OpenHands engine uses the developer's model but not its `instructions` or `tools` (OpenHands has its own).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `InvalidTemplateError` at startup | A template uses an unknown tool, workflow or checker, or misses a required role | Read the message; fix the template or add the name to `catalog.py` |
| Edited instructions have no effect | Process still has the old template cached | Restart |
| `team_template_not_found` | `TEAM_TEMPLATE` names a file that doesn't exist | Check `templates/` |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-01 | `[[roles.mcp]]` grants (server, tools, read-only, calls per task), validated against the MCP catalog; developers get `python_docs` |
| 2026-10-01 | `[approval]` rules in templates, validated against `WORKFLOW_FACTS`; developer and CTO instructions forbid faking tests |
| 2026-10-01 | `review_instructions` for the CTO; developer `max_count` used by the CTO's assignment |
| 2026-10-01 | Created: template schema and validation, software team, API, wiring builds the CTO and developer from the template |
