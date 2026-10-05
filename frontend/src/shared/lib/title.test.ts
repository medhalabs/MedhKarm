import { describe, expect, it } from "vitest";

import { titleFrom } from "./title";

describe("titleFrom", () => {
  it("uses the first line without Markdown marks", () => {
    expect(titleFrom("\n## Create a **premium** landing page\n\nMore")).toBe(
      "Create a premium landing page",
    );
    expect(titleFrom("> [Docs](https://x.y) first")).toBe("Docs first");
    expect(titleFrom("x".repeat(200), 10)).toBe("xxxxxxxxx…");
  });
});
