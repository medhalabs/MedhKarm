import { describe, expect, it } from "vitest";

import { hasOpenPullRequest, liveRepoUrl } from "./liveRepo";
import type { Run } from "./types";

const base = { id: "r1", request: "x", status: "released" } as Run;

describe("liveRepoUrl", () => {
  it("is the repository a new project was created in", () => {
    const run = { ...base, delivery: { status: "created", repo_url: "https://github.com/me/c" } };
    expect(liveRepoUrl(run as Run)).toBe("https://github.com/me/c");
  });

  it("is the founder's own repository for a change to it", () => {
    const run = { ...base, repo: { url: "https://github.com/me/shop", branch: null } };
    expect(liveRepoUrl(run as Run)).toBe("https://github.com/me/shop");
  });

  it("is nothing for work that never reached GitHub, or isn't released", () => {
    expect(liveRepoUrl(base)).toBeNull();
    expect(
      liveRepoUrl({ ...base, status: "running", repo: { url: "u", branch: null } }),
    ).toBeNull();
  });
});

describe("hasOpenPullRequest", () => {
  it("is true while the release waits to be merged", () => {
    expect(hasOpenPullRequest({ ...base, delivery: { status: "opened" } } as Run)).toBe(true);
    expect(hasOpenPullRequest({ ...base, delivery: { status: "created" } } as Run)).toBe(false);
  });
});
