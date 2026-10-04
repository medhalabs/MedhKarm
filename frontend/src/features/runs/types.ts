import type { StackChoiceInput } from "@/features/starters";

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
  security?: string[]; // the security engineer's warnings, if any
  preview_url?: string; // DevOps' preview to try before approving
  preview_error?: string;
  browser_test?: string;
};

/** A founder's GitHub repository (backend: repos/schemas.py RepoSource). */
export type RepoSource = { url: string; branch: string | null };

/** How released work went to GitHub (backend: repos/schemas.py Delivery). */
export type Delivery = {
  status: "opened" | "created" | "no_changes" | "skipped";
  branch: string;
  commit: string;
  pull_request_url: string;
  repo_url: string; // the repository the work went to (set when one was created)
  reason: string;
};

/** DevOps' deployment (backend: deploys/schemas.py). */
export type Deployment = {
  url: string;
  state: string; // READY when it worked
  target: string;
  kind: string;
  error: string;
};

export type Run = {
  id: string;
  request: string;
  test_command: string; // empty: detected from the repository when the run starts
  repo: RepoSource | null;
  new_repo: { name: string | null } | null; // a repository to create on release
  stack: StackChoiceInput | null; // the founder's stack choices (new projects)
  status: RunStatus;
  gate: Gate | null;
  error: string | null;
  delivery: Delivery | null;
  deployment: Deployment | null; // where the released app is live
  created_at: string;
  updated_at: string;
};

/** Result of a form's server action, shown under the form. */
export type FormState = { error: string | null };
