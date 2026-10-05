"""Suggested models per provider, and the cheap one each key check uses. Founders can type any
model their provider has; these are the ones we know work with the team's tool calls."""

from app.features.model_settings.schemas import Provider

SUGGESTED: dict[Provider, list[str]] = {
    Provider.OLLAMA: [
        "ollama_chat/gpt-oss:20b",
        "ollama_chat/gpt-oss:120b",
        "ollama_chat/gemma4:31b",
    ],
    Provider.ANTHROPIC: [
        "anthropic/claude-sonnet-5-5",
        "anthropic/claude-haiku-4-5-20251001",
        "anthropic/claude-opus-5-5",
    ],
    Provider.OPENAI: ["openai/gpt-5-mini", "openai/gpt-5"],
    Provider.GEMINI: ["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"],
    Provider.OPENROUTER: ["openrouter/openai/gpt-oss-120b", "openrouter/openai/gpt-oss-20b"],
    Provider.GROQ: ["groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b"],
    Provider.LOCAL: ["local/gpt-oss:20b", "local/qwen3-coder:30b"],
}

# The cheapest model to check a key with when the founder hasn't chosen one of that provider's.
CHECK_MODEL: dict[Provider, str] = {
    Provider.OLLAMA: "ollama_chat/gpt-oss:20b",
    Provider.ANTHROPIC: "anthropic/claude-haiku-4-5-20251001",
    Provider.OPENAI: "openai/gpt-5-mini",
    Provider.GEMINI: "gemini/gemini-2.5-flash",
    Provider.OPENROUTER: "openrouter/openai/gpt-oss-20b",
    Provider.GROQ: "groq/openai/gpt-oss-20b",
    Provider.LOCAL: "local/gpt-oss:20b",
}

# The environment variables LiteLLM reads for our own (managed) keys.
SERVER_KEY_ENV: dict[Provider, str] = {
    Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.GEMINI: "GEMINI_API_KEY",
    Provider.OPENROUTER: "OPENROUTER_API_KEY",
    Provider.GROQ: "GROQ_API_KEY",
}
