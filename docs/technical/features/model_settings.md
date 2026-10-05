# Model settings (bring your own keys and models)

**Status:** Built (Phase 3): managed or own keys per founder, a model for the team and per agent, local models through a connector, keys checked when added. Tried live through the API on Oct 5, 2026. The page isn't tried in a browser yet.  
**Code:** `backend/app/features/model_settings/` · `backend/app/core/tenant.py` · `backend/app/shared/secret_box.py` · `backend/app/workers/handlers/scope.py` · `frontend/src/features/model_settings/` · page `/admin/models` · migration `0012_model_settings`  
**Last updated:** 2026-10-05

## What it is

Each founder chooses who pays for their team's AI:
- **Managed** (default, the ₹1,999 plan): we run the models on our keys. Any key the founder adds is used for that provider, and the rest run on ours.
- **Bring your own** (the ₹799 plan): only the founder's keys and local models. A model without one of their keys doesn't run, and the error says what to add.

They can also pick:
- **the team's model** (blank: our default, `gpt-oss:20b` on Ollama Cloud)
- **a different model for one agent:** Mira (PM), Kabir (CTO), the developers, Tara (QA)
- **local models** (`local/<name>`): Ollama on their own machine, reached through a connector URL. Today the connector is a tunnel: `cloudflared tunnel --url http://localhost:11434`.

**Providers:** Ollama Cloud, Anthropic, OpenAI, Gemini, OpenRouter, Groq, and local. Any model the provider has can be typed in. The suggestions are the ones we know.

**Keys:**
- They are stored encrypted, and only their last four characters are ever shown again.
- Each key is checked with one tiny call when added. The provider's own words come back, e.g. "Invalid API Key".

## How it works

1. **Every agent's model is a `CompanyRoutedProvider`** (`routed.py`), built once per worker with its role and the template's model.
2. **Each call asks `ModelSettingsService.config(company, role, fallback)`** which model, endpoint and key to use. The company is the one whose work is running, read from `current_company` (`app/core/tenant.py`).
   - **Model:** the role's own choice, else the team's model, else the template's model for the role, else `DEFAULT_MODEL`.
   - **Key:** the company's own key for that provider, else ours (managed), else `MissingKeyError` (own keys).
   - **`local/x`** becomes `ollama_chat/x` at the founder's connector URL, with their optional token.
   - **No company** (evals, old runs): ours, as before.
3. **Who sets the company:**
   - **The worker:** `CompanyScoped` wraps the jobs that call models: build start/resume (the run's company), backlog planning (the project's), message replies (the message's). Tasks started inside a job inherit it, so LangGraph nodes and the developer engine see it.
   - **The API:** the intake chats (`/intake`, `/intake/project`).
4. **Settings are cached for 30 s per company** in each process. A founder's change reaches running workers within that.
5. **Saving checks that every chosen model can run.** On own keys, the provider's key must be added. On managed, either their key or ours. Local models need the connector URL.
6. **Encryption** (`SecretBox`): Fernet, keyed by `SECRETS_KEY` (default `AUTH_SECRET`, or a fixed development secret). A key sealed under another secret is reported as "add it again", never sent garbled.

## Code map

| File | Responsibility |
| --- | --- |
| `schemas.py` | `Provider`, `PREFIX`, `provider_of`, `KeyMode`, `ModelChoices` (validation), `CompanyModels` (the view), `StoredModels`, `NewKey`, `KeyCheck`, `ModelOption`, `ModelsView` |
| `catalog.py` | Suggested models, the cheap model each key check uses, our providers' env vars |
| `service.py` | `ModelSettingsService`: get, save, add/remove key, check, `config` (per call) |
| `routed.py` | `CompanyRoutedProvider`: the per-call `LLMProvider`; reuses built providers per model and key |
| `repository.py` · `memory_repository.py` · `models.py` | The `model_settings` table |
| `dependencies.py` | `server_providers`, `secret_box`, `model_settings_service(settings)`, `get_model_settings_service()` |
| `router.py` | `/settings/models` |
| `core/tenant.py` | `current_company`, `company_scope()` |
| `shared/secret_box.py` | `SecretBox.seal` / `open` |
| `workers/handlers/scope.py` | `CompanyScoped` job wrapper |
| `workers/wiring.py` | `_provider(settings, role, model)`: metered and routed |
| `frontend/…/model_settings/` | `ModelsPage`, `ChoicesForm`, `KeyRow`, `parseChoices`, server actions |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/settings/models` | `{settings, options, roles}`: choices and key hints; providers with suggestions and whether we have a key; the agents that use a model | Bearer |
| PUT | `/settings/models` | Save `{mode, default_model, role_models, local_url}`; 400 when a choice can't run | Bearer |
| POST | `/settings/models/keys` | Add or replace `{provider, key}` | Bearer |
| DELETE | `/settings/models/keys/{provider}` | Remove a key | Bearer |
| POST | `/settings/models/keys/{provider}/check` | One tiny call → `{provider, model, ok, error}` | Bearer |

## Data model

`model_settings`:
- `company_id` (PK, FK companies, cascade)
- `mode` (`managed` / `own`)
- `default_model`, `role_models` (jsonb: role → model), `local_url`
- `keys` (jsonb: provider → `{sealed, hint}`)
- `updated_at`

## Events

None new. `model.used` now names the model the company actually used.

## Dependencies

- **Uses:** `models` (`provider_for`, `resolve_model_config`, `LLMProvider`), `teams` (role names), `auth`
- **Used by:** the worker's wiring (every agent), `intake`
- **Config:** `SECRETS_KEY` (new; default `AUTH_SECRET`). Our own keys: `OLLAMA_API_KEY`, plus `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY` in the environment, which LiteLLM reads.

## Design decisions

- 2026-10-05 — **Resolve per call, not per worker.** The team is built once, and each call picks its company's model and key, so one worker serves every founder. New providers need no change to agents (open/closed).
- 2026-10-05 — **The company travels in a context variable,** set once per job or request. The graph, engines and nodes don't pass it along, and tasks started inside inherit it.
- 2026-10-05 — **Own keys never fall back to ours.** On the ₹799 plan our bill must stay zero, so a missing key is an error that says what to add.
- 2026-10-05 — **Encrypted at rest with Fernet.** Only the last four characters are ever returned, and keys aren't logged (`ModelConfig.api_key` is hidden from repr).
- 2026-10-05 — **Local models through a tunnel first.** It works today with a single command. A purpose-built connector (outbound, no public URL) is the next step (G-46).

## How to run and test

- `uv run pytest app/features/model_settings tests/test_company_scope.py` (plus `-m integration` for the table)
- **Live (Oct 5, 2026), through the API:**
  - A fake Groq key was checked against Groq and answered "Invalid API Key".
  - Own keys with no key: the intake answered "You're on your own keys and there's no ollama key…".
  - Kabir on `gpt-oss:120b` for his role only answered in about 5 s.
  - Anthropic chosen without a key was refused on save.

## Known limitations and gotchas

- **The OpenHands engine** reads its model when the worker starts, so it ignores founders' choices (G-45). The built-in engine, the default, follows them.
- **Local models need a public tunnel URL** (G-46).
- **Usage isn't marked as on our keys or theirs** yet; billing needs that (G-47).
- **Changing `SECRETS_KEY`** (or `AUTH_SECRET` without it) makes saved keys unreadable. Founders then add them again.
- **Our other providers' keys** must be real environment variables (not only in `.env`), because LiteLLM reads `os.environ`.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| "We don't run X models on our keys" when saving | Managed, no key of theirs or ours for X | Add their key, or set ours in the environment |
| A run stops with "no … key for …" | Own keys, and the chosen model's provider has no key | Add the key, or choose another model |
| "can't be read any more" | `SECRETS_KEY` / `AUTH_SECRET` changed | Add the key again |
| Local model calls time out | The tunnel or Ollama on the founder's machine is down | Restart both; update the URL if the tunnel changed it |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-05 | Created: managed / own keys, team and per-agent models, local models via a connector URL, encrypted keys with a check call, per-call routing by company |
