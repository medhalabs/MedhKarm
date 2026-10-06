import { describe, expect, it } from "vitest";

import { briefBody } from "./briefBody";
import type { Brief } from "./types";

const base: Brief = {
  request: "A coffee shop app",
  summary: "",
  repo_url: null,
  branch: null,
  create_repo: true,
  new_repo_name: null,
  stack: { payments: "razorpay" },
  test_command: null,
};

describe("briefBody", () => {
  it("a new project carries its stack and repo choice", () => {
    expect(briefBody(base)).toEqual({
      request: "A coffee shop app",
      create_repo: true,
      stack: { payments: "razorpay" },
    });
  });

  it("an existing repository carries the repo, not a stack", () => {
    const body = briefBody({ ...base, repo_url: "https://github.com/me/shop", branch: "dev" });
    expect(body).toEqual({
      request: "A coffee shop app",
      repo: { url: "https://github.com/me/shop", branch: "dev" },
    });
  });
});
