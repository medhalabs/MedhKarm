# Models

**Status:** Done (Phase 0)  
**Code:** `backend/app/features/models/`  
**Last updated:** 2026-10-01

## What it is

The single way agents talk to AI models. Agents depend on the `LLMProvider` interface ("send messages and tools, get text and tool calls back"), never on a vendor SDK, so any agent can run on any model. Today the default is `gpt-oss:120b` on Ollama Cloud.

## How it works

1. `build_provider(settings, model)` in `service.py` picks the provider for a model name. Names starting with `ollama/` or `ollama_chat/` get the Ollama Cloud URL and key; others use the standard env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`).
2. `LiteLLMProvider.complete()` calls `litellm.acompletion` with messages and tools in OpenAI chat format, retrying up to 3 times on provider errors.
3. The response becomes an `LLMResponse`: text, parsed `ToolCall`s (arguments as a dict) and `TokenUsage`.
4. Any failure after retries is raised as `ModelCallError` (HTTP 502 if it reaches the API).

## Code map

| File | Responsibility |
| --- | --- |
| `interfaces.py` | `LLMProvider` Protocol: `model_name`, `complete(messages, tools)` |
| `schemas.py` | `Message`, `ToolSpec`, `ToolCall`, `TokenUsage`, `LLMResponse` |
| `service.py` | `build_provider()`: model name → configured provider |
| `providers/litellm_provider.py` | Real provider via LiteLLM, with retries |
| `providers/scripted_provider.py` | Test provider that replays prepared responses and records calls |
| `exceptions.py` | `ModelCallError` |

## API

None yet (used by other features in-process).

## Data model

None. Token usage is returned per call; storing it arrives with the event log.

## Events

None yet.

## Dependencies

- **Other features used:** none
- **Interfaces defined:** `LLMProvider` → `LiteLLMProvider`, `ScriptedLLMProvider`
- **External services:** Ollama Cloud (`https://ollama.com`); any LiteLLM-supported provider
- **Config:** `DEFAULT_MODEL` (default `ollama_chat/gpt-oss:120b`), `OLLAMA_API_BASE`, `OLLAMA_API_KEY`

## Design decisions

- 2026-10-01 — Start on Ollama Cloud's free models. All six (`gpt-oss:120b`, `gpt-oss:20b`, `gemma4:31b`, `nemotron-3-nano:30b`, `nemotron-3-super`, `nemotron-3-ultra`) made correct tool calls in a direct test. `gpt-oss:120b` is the default; it completed real coding tasks through LiteLLM.
- 2026-10-01 — Use `ollama_chat/` (Ollama's chat endpoint), not `ollama/` (completion endpoint): tool calling needs the chat endpoint.
- 2026-10-01 — Retry 3 times inside the provider: Ollama Cloud returned an occasional 500 that succeeded on retry.
- 2026-10-01 — OpenAI message format everywhere: LiteLLM converts it for each provider, so nothing else changes when models change.

## How to run and test

- Unit tests (LiteLLM mocked): `uv run pytest app/features/models`
- Live check: set `OLLAMA_API_KEY` in `backend/.env`, then run a build (see [workflows.md](workflows.md)).

## Known limitations and gotchas

- No streaming yet; each call returns when complete.
- No per-role model choice yet: one default model for every agent.
- LiteLLM prints a "Give Feedback / Get Help" banner on errors; harmless.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModelCallError ... 401` | Missing or wrong `OLLAMA_API_KEY` | Check `backend/.env` |
| `ModelCallError ... 500` after retries | Ollama Cloud outage or free-tier limits | Retry later, or switch `DEFAULT_MODEL` to another free model |
| Model answers in text but never calls tools | Wrong prefix (`ollama/`) | Use `ollama_chat/<model>` |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-01 | Created: LiteLLM provider, Ollama Cloud defaults, retries, scripted test provider |
