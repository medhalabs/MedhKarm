// Mirrors backend/app/features/signoffs/schemas.py.

export type SignoffState = "ok" | "warn" | "fail" | "waiting" | "skipped";

export type Signoff = {
  role: string;
  name: string;
  title: string;
  state: SignoffState;
  headline: string;
  details: string[];
  url: string;
  video_id: number | null; // QA's demo video, an artifact of the run
};
