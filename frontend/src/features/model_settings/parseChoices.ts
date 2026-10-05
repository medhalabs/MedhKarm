import type { ModelChoices } from "./types";

/** The choices form → the API body. Blank model fields mean "the team's default". */
export function parseChoices(form: FormData, roles: string[]): ModelChoices {
  const text = (name: string) => String(form.get(name) ?? "").trim();
  const role_models: Record<string, string> = {};
  for (const role of roles) {
    const model = text(`role_${role}`);
    if (model) role_models[role] = model;
  }
  return {
    mode: form.get("mode") === "own" ? "own" : "managed",
    default_model: text("default_model"),
    role_models,
    local_url: text("local_url"),
  };
}
