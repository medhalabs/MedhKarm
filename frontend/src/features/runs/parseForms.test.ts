import { describe, expect, it } from "vitest";

import { parseDecision, parseStartRun } from "./parseForms";

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe("parseStartRun", () => {
  it("leaves the test command and the stack to the team for a new project", () => {
    expect(parseStartRun(form({ request: " Build a calculator " }))).toEqual({
      request: "Build a calculator",
      create_repo: false,
      stack: {},
    });
  });

  it("sends the founder's stack for a new project only", () => {
    expect(
      parseStartRun(form({ request: "A clinic website", stack_api: "python", module_auth: "on" })),
    ).toMatchObject({ stack: { api: "python", modules: ["auth"] } });
    expect(
      parseStartRun(
        form({ request: "Add search", repo_url: "https://github.com/a/notes", stack_api: "java" }),
      ),
    ).not.toHaveProperty("stack");
  });

  it("leaves the test command to the backend for a repo", () => {
    expect(
      parseStartRun(
        form({ request: "Add search", repo_url: "https://github.com/a/notes", repo_branch: "" }),
      ),
    ).toEqual({ request: "Add search", repo: { url: "https://github.com/a/notes", branch: null } });
  });

  it("creates a named repo for a new project when ticked", () => {
    expect(
      parseStartRun(form({ request: "Build a timer", create_repo: "on", new_repo_name: "timer" })),
    ).toEqual({
      request: "Build a timer",
      create_repo: true,
      new_repo_name: "timer",
      stack: {},
    });
    expect(
      parseStartRun(
        form({ request: "Build a timer", create_repo: "on", new_repo_name: "my timer" }),
      ),
    ).toEqual({ error: "Repository names use letters, digits, '.', '_' and '-'." });
  });

  it("only takes GitHub addresses", () => {
    expect(parseStartRun(form({ request: "Add search", repo_url: "git@github.com:a/b" }))).toEqual({
      error: "Use the repository's GitHub address: https://github.com/owner/name",
    });
  });

  it("needs a request", () => {
    expect(parseStartRun(form({ request: " " }))).toEqual({
      error: "Say what the team should build.",
    });
  });
});

describe("parseDecision", () => {
  it("reads the button pressed and the note", () => {
    expect(parseDecision(form({ decision: "reject", feedback: "Not yet" }))).toEqual({
      approved: false,
      feedback: "Not yet",
    });
    expect(parseDecision(form({ decision: "maybe" }))).toEqual({
      error: "Choose approve or reject.",
    });
  });
});
