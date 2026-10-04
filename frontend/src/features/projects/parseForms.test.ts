import { describe, expect, it } from "vitest";

import { parseNewItem, parseNewProject } from "./parseForms";

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe("parseNewProject", () => {
  it("reads a new project", () => {
    expect(
      parseNewProject(
        form({ name: "Habits", goal: "Track daily habits", autopilot: "on", daily_limit: "3" }),
      ),
    ).toEqual({
      name: "Habits",
      goal: "Track daily habits",
      repo: null,
      autopilot: true,
      daily_limit: 3,
    });
  });

  it("checks the repository address", () => {
    expect(
      parseNewProject(
        form({ name: "Shop", goal: "Add coupons to my shop", repo_url: "gitlab.com/x" }),
      ),
    ).toEqual({ error: "Use the repository's GitHub address: https://github.com/owner/name" });
  });
});

describe("parseNewItem", () => {
  it("splits acceptance checks by line", () => {
    expect(
      parseNewItem(form({ title: "Export CSV", acceptance: "has header\n\n one row each " })),
    ).toEqual({
      title: "Export CSV",
      description: "",
      acceptance: ["has header", "one row each"],
    });
  });
});
