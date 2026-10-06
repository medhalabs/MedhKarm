import type { AutonomySettings, Level } from "./types";

const LEVELS: Level[] = ["every", "small", "checks"];

/** The form → the settings the API takes. Numbers fall back to the defaults when blank. */
export function parseSettings(form: FormData): AutonomySettings {
  const number = (name: string, fallback: number) => {
    const value = Number(String(form.get(name) ?? "").replace(/[, _]/g, ""));
    return Number.isFinite(value) && value > 0 ? Math.round(value) : fallback;
  };
  const on = (name: string) => form.get(name) === "on";
  const level = String(form.get("level") ?? "every") as Level;
  return {
    level: LEVELS.includes(level) ? level : "every",
    small_files: number("small_files", 3),
    ask_sensitive_files: on("ask_sensitive_files"),
    ask_open_comments: on("ask_open_comments"),
    ask_security_warnings: on("ask_security_warnings"),
    ask_preview_failed: on("ask_preview_failed"),
    ask_large_change: on("ask_large_change"),
    large_files: number("large_files", 15),
    ask_expensive: on("ask_expensive"),
    max_tokens: number("max_tokens", 1_000_000),
    never_touch: String(form.get("never_touch") ?? "")
      .split(/[\n,]/)
      .map((line) => line.trim())
      .filter(Boolean),
    go_live: on("go_live"),
  };
}
