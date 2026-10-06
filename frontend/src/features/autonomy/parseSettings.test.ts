import { describe, expect, it } from "vitest";

import { parseSettings } from "./parseSettings";

function form(entries: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(entries)) data.set(key, value);
  return data;
}

describe("parseSettings", () => {
  it("reads checkboxes, numbers with separators and one pattern per line or comma", () => {
    const settings = parseSettings(
      form({
        level: "small",
        small_files: "5",
        ask_sensitive_files: "on",
        ask_large_change: "on",
        large_files: "20",
        max_tokens: "2,000,000",
        never_touch: "payments/*\n *.sql, .env* \n",
        go_live: "on",
      }),
    );
    expect(settings).toMatchObject({
      level: "small",
      small_files: 5,
      ask_sensitive_files: true,
      ask_open_comments: false, // an unchecked box is off
      ask_large_change: true,
      large_files: 20,
      max_tokens: 2_000_000,
      never_touch: ["payments/*", "*.sql", ".env*"],
      go_live: true,
    });
  });

  it("falls back to safe values for a blank or unknown level and bad numbers", () => {
    const settings = parseSettings(form({ level: "yolo", small_files: "abc", max_tokens: "-3" }));
    expect(settings.level).toBe("every");
    expect(settings.small_files).toBe(3);
    expect(settings.max_tokens).toBe(1_000_000);
    expect(settings.go_live).toBe(false);
  });
});
