// Mirrors backend/app/features/messages/schemas.py.

export type Message = {
  id: number;
  thread: "run" | "project";
  thread_id: string;
  author: string; // "founder" or the agent's role
  name: string; // "You", "Mira", "Kabir", …
  to: string;
  body: string;
  created_at: string;
};

export type FormState = { error: string | null };

/** Who the founder can write to (the team template's roles that answer). */
export const AGENTS = [
  { role: "cto", label: "Kabir (CTO)" },
  { role: "pm", label: "Mira (PM)" },
  { role: "developer", label: "Isha (developer)" },
  { role: "qa", label: "Tara (QA)" },
] as const;
