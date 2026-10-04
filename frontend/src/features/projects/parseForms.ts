/** Reads and checks the projects forms before anything is sent to the backend. */

import { parseStack, type StackChoiceInput } from "@/features/starters";

export type NewProjectInput = {
  name: string;
  goal: string;
  repo: { url: string } | null;
  autopilot: boolean;
  daily_limit: number;
  stack?: StackChoiceInput; // a new project's stack and modules (empty: the team picks)
};

export type NewItemInput = { title: string; description: string; acceptance: string[] };

export function parseNewProject(form: FormData): NewProjectInput | { error: string } {
  const name = String(form.get("name") ?? "").trim();
  const goal = String(form.get("goal") ?? "").trim();
  const repoUrl = String(form.get("repo_url") ?? "").trim();
  const limit = Number(form.get("daily_limit") ?? 2);
  if (name.length < 2) return { error: "Give the project a name." };
  if (goal.length < 10) return { error: "Describe the goal in a sentence or two." };
  if (repoUrl && !/^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/.test(repoUrl))
    return { error: "Use the repository's GitHub address: https://github.com/owner/name" };
  if (!Number.isInteger(limit) || limit < 1 || limit > 10)
    return { error: "Items per day is a number from 1 to 10." };
  const stack = repoUrl ? null : parseStack(form);
  if (stack && "error" in stack) return stack;
  return {
    name,
    goal,
    repo: repoUrl ? { url: repoUrl } : null,
    autopilot: form.get("autopilot") === "on",
    daily_limit: limit,
    ...(stack ? { stack } : {}),
  };
}

export function parseNewItem(form: FormData): NewItemInput | { error: string } {
  const title = String(form.get("title") ?? "").trim();
  if (title.length < 3) return { error: "Give the item a short title." };
  const acceptance = String(form.get("acceptance") ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return { title, description: String(form.get("description") ?? "").trim(), acceptance };
}
