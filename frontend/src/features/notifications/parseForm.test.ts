import { describe, expect, it } from "vitest";

import { parseSettings } from "./parseForm";

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe("parseSettings", () => {
  it("reads the settings and cleans the number", () => {
    expect(
      parseSettings(
        form({
          email: " Me@X.in ",
          whatsapp: "+91 (98765) 43210",
          standup_on: "on",
          standup_hour: "8",
        }),
      ),
    ).toEqual({
      email: "me@x.in",
      whatsapp: "+919876543210",
      standup_on: true,
      standup_hour: 8,
      weekly_on: false,
      nudge_on: false,
    });
  });

  it("needs the country code", () => {
    expect(parseSettings(form({ whatsapp: "9876543210" }))).toEqual({
      error: "Use the full WhatsApp number with country code, e.g. +919876543210.",
    });
  });
});
