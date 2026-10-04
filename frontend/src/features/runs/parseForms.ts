/** Reads and checks the admin forms before anything is sent to the backend. */

import { parseStack, type StackChoiceInput } from "@/features/starters";

export type StartRunInput = {
  request: string;
  test_command?: string; // omitted: detected from the repo or the new project's starter
  repo?: { url: string; branch: string | null };
  create_repo?: boolean; // without a repo: create one on release (backend default: true)
  new_repo_name?: string;
  stack?: StackChoiceInput; // without a repo: the stack and modules (empty: the team picks)
};

const REPO_NAME = /^[A-Za-z0-9._-]{1,100}$/;

const GITHUB_URL = /^https:\/\/github\.com\/[A-Za-z0-9-]{1,39}\/[A-Za-z0-9._-]{1,100}?(\.git)?\/?$/;
export type DecisionInput = { approved: boolean; feedback: string };

export function parseStartRun(form: FormData): StartRunInput | { error: string } {
  const request = String(form.get("request") ?? "").trim();
  const repoUrl = String(form.get("repo_url") ?? "").trim();
  const branch = String(form.get("repo_branch") ?? "").trim() || null;
  const testCommand = String(form.get("test_command") ?? "").trim();
  if (request.length < 3) return { error: "Say what the team should build." };
  if (request.length > 5000) return { error: "Keep the request under 5,000 characters." };
  if (testCommand.length > 500) return { error: "Keep the test command under 500 characters." };
  if (repoUrl && !GITHUB_URL.test(repoUrl))
    return { error: "Use the repository's GitHub address: https://github.com/owner/name" };
  if (!repoUrl) {
    const create = form.get("create_repo") === "on";
    const name = String(form.get("new_repo_name") ?? "").trim();
    if (create && name && (!REPO_NAME.test(name) || name === "." || name === ".."))
      return { error: "Repository names use letters, digits, '.', '_' and '-'." };
    const stack = parseStack(form);
    if ("error" in stack) return stack;
    return {
      request,
      ...(testCommand ? { test_command: testCommand } : {}),
      create_repo: create,
      ...(create && name ? { new_repo_name: name } : {}),
      stack,
    };
  }
  return {
    request,
    ...(testCommand ? { test_command: testCommand } : {}),
    repo: { url: repoUrl, branch },
  };
}

export function parseDecision(form: FormData): DecisionInput | { error: string } {
  const decision = form.get("decision");
  if (decision !== "approve" && decision !== "reject")
    return { error: "Choose approve or reject." };
  const feedback = String(form.get("feedback") ?? "").trim();
  if (feedback.length > 2000) return { error: "Keep the note under 2,000 characters." };
  return { approved: decision === "approve", feedback };
}
