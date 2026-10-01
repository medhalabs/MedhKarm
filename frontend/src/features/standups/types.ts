// Mirrors backend/app/features/standups/schemas.py.

export type StandupItem = {
  run_id: string;
  project: string;
  text: string;
  member: string | null;
  at: string | null;
};

export type ProjectSummary = {
  run_id: string;
  project: string;
  status: string;
  tasks_done: number;
  tasks_total: number;
  tokens: number;
};

export type Standup = {
  day: string;
  timezone: string;
  since: string;
  until: string;
  headline: string;
  done: StandupItem[];
  planned: StandupItem[];
  blocked: StandupItem[];
  needs_you: StandupItem[];
  projects: ProjectSummary[];
  sent_back: number;
  tokens: number;
};
