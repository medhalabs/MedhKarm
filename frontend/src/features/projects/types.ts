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
