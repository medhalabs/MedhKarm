import { describe, expect, it } from "vitest";

import { fileUrl } from "./fileUrl";

describe("fileUrl", () => {
  it("points at the proxy route, not the backend", () => {
    expect(fileUrl("abc123", 7)).toBe("/api/runs/abc123/artifacts/7");
  });
});
