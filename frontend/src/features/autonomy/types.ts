// Mirrors backend/app/features/autonomy/schemas.py.

export type Level = "every" | "small" | "checks";

export type AutonomySettings = {
  level: Level;
  small_files: number;
  ask_sensitive_files: boolean;
  ask_open_comments: boolean;
  ask_security_warnings: boolean;
  ask_preview_failed: boolean;
  ask_large_change: boolean;
  large_files: number;
  ask_expensive: boolean;
  max_tokens: number;
  never_touch: string[];
  go_live: boolean;
};

export type AutonomyView = {
  scope: "company" | "project";
  project_id: string | null;
  own: boolean;
  settings: AutonomySettings;
  summary: string[];
};

export type FormState = { error: string | null; saved?: boolean };
