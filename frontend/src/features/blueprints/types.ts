// Mirrors backend/app/features/blueprints/schemas.py.

export type BlueprintStatus = "writing" | "ready" | "revising" | "approved" | "failed";

export type Doc = { id: string; title: string; path: string; content: string };

export type Comment = { author: "founder" | "lekha"; text: string; at: string };

export type Blueprint = {
  id: string;
  title: string;
  status: BlueprintStatus;
  docs: Doc[];
  comments: Comment[];
  progress: string;
  error: string;
  run_id: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
};

export type FormState = { error: string | null };

/** Lekha is still working: the page keeps refreshing. */
export function isBusy(status: BlueprintStatus): boolean {
  return status === "writing" || status === "revising";
}
