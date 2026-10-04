/** The founder's stack choices for a new project (backend: starters/schemas.py StackChoice).
 * Anything left out, the team decides: from the request first, then its defaults. */
export type StackChoiceInput = {
  frontend?: string;
  api?: string;
  database?: string;
  hosting?: string;
  payments?: string;
  modules?: string[]; // omitted: picked from the request
  starter?: boolean; // omitted: a starter when the request is an app
  notes?: string;
};

export const STACK_FIELDS = ["frontend", "api", "database", "hosting", "payments"] as const;

export const MODULES = [
  { name: "auth", title: "Sign-in" },
  { name: "payments", title: "Payments" },
  { name: "reminders", title: "Reminders" },
  { name: "dashboards", title: "Admin dashboard" },
] as const;
