// Mirrors backend/app/features/model_settings/schemas.py.

export type Provider =
  "ollama" | "anthropic" | "openai" | "gemini" | "openrouter" | "groq" | "local";

export type KeyMode = "managed" | "own";

export type ModelChoices = {
  mode: KeyMode;
  default_model: string;
  role_models: Record<string, string>;
  local_url: string;
};

export type SavedKey = { provider: Provider; hint: string };

export type CompanyModels = ModelChoices & { company_id: string; keys: SavedKey[] };

export type ModelOption = { provider: Provider; models: string[]; server_key: boolean };

export type ModelsView = {
  settings: CompanyModels;
  options: ModelOption[];
  roles: Record<string, string>;
};

export type KeyCheck = { provider: Provider; model: string; ok: boolean; error: string };

export type FormState = { error: string | null; saved?: boolean; check?: KeyCheck };

export const PROVIDER_NAMES: Record<Provider, string> = {
  ollama: "Ollama Cloud",
  anthropic: "Anthropic (Claude)",
  openai: "OpenAI",
  gemini: "Google Gemini",
  openrouter: "OpenRouter",
  groq: "Groq",
  local: "Local models (your connector)",
};
