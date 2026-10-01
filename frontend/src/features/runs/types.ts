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

/** A founder's GitHub repository (backend: repos/schemas.py RepoSource). */
export type RepoSource = { url: string; branch: string | null };

/** How released work went back to the repository (backend: repos/schemas.py Delivery). */
export type Delivery = {
  status: "opened" | "no_changes" | "skipped";
  branch: string;
  commit: string;
  pull_request_url: string;
  reason: string;
};

export type Run = {
  id: string;
  request: string;
  test_command: string; // empty: detected from the repository when the run starts
  repo: RepoSource | null;
  status: RunStatus;
  gate: Gate | null;
  error: string | null;
  delivery: Delivery | null;
  created_at: string;
  updated_at: string;
};

/** Result of a form's server action, shown under the form. */
export type FormState = { error: string | null };
