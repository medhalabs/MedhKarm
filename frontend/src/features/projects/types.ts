import type { StackChoiceInput } from "@/features/starters";

// Mirrors backend/app/features/projects/schemas.py.

export type ProjectStatus = "planning" | "plan_ready" | "active" | "paused" | "done";

export type ItemStatus =
  "proposed" | "todo" | "in_progress" | "waiting_for_merge" | "done" | "blocked" | "skipped";

export type BacklogItem = {
  id: string;
  project_id: string;
  position: number;
  title: string;
  description: string;
  acceptance: string[];
  size: "S" | "M" | "L";
  status: ItemStatus;
  run_id: string | null;
  attempts: number;
  note: string;
  pull_request_url: string;
  started_at: string | null;
  done_at: string | null;
};

export type Project = {
  id: string;
  name: string;
  goal: string;
  repo: { url: string; branch: string | null } | null;
  repo_owned: boolean;
  test_command: string;
  stack: StackChoiceInput | null; // the founder's stack choices (new projects)
  status: ProjectStatus;
  autopilot: boolean;
  daily_limit: number;
  questions: string[];
  error: string;
  created_at: string;
  updated_at: string;
};

export type ProjectDetail = Project & { items: BacklogItem[] };

export type FormState = { error: string | null };

/** A project agreed with Mira (backend: intake/schemas.py ProjectBrief). */
export type ProjectBrief = {
  name: string;
  goal: string;
  summary: string;
  repo_url: string | null;
  stack: StackChoiceInput & { modules?: string[] | null; starter?: boolean | null };
  autopilot: boolean;
  daily_limit: number;
};

export type ProjectIntakeReply = { agent: string; text: string; brief: ProjectBrief | null };

/** Priya's report on a project (backend: projects/health.py). */
export type ProjectHealth = {
  project_id: string;
  name: string;
  items_total: number;
  done: number;
  in_progress: number;
  blocked: number;
  waiting: number;
  runs: number;
  tokens: number;
  days_since_activity: number | null;
  state: "not_started" | "moving" | "needs_you" | "stalled" | "done";
  summary: string;
};
