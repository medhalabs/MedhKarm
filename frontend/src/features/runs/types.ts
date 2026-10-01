// Mirrors backend/app/features/runs/schemas.py.

export type RunStatus =
  "queued" | "running" | "waiting_for_approval" | "released" | "rejected" | "failed" | "error";

/** What the founder is asked at the release gate (backend: workflows/nodes/approval.py). */
export type Gate = {
  gate: string;
  question: string;
  reasons: string[];
  rules: string[]; // approval rules that asked; empty = every release is asked
  summary: string;
  files_changed: string[];
  tokens?: number;
  tests: string;
};

export type Run = {
  id: string;
  request: string;
  test_command: string;
  status: RunStatus;
  gate: Gate | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

/** Result of a form's server action, shown under the form. */
export type FormState = { error: string | null };
