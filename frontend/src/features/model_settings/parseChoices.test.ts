import { describe, expect, it } from "vitest";

import { parseChoices } from "./parseChoices";

describe("parseChoices", () => {
  it("keeps only the roles given a model, trimmed", () => {
    const form = new FormData();
    form.set("mode", "own");
    form.set("default_model", " anthropic/claude-sonnet-5-5 ");
    form.set("role_qa", "groq/openai/gpt-oss-20b");
    form.set("role_cto", "  ");
    form.set("local_url", "");
    expect(parseChoices(form, ["cto", "qa"])).toEqual({
      mode: "own",
      default_model: "anthropic/claude-sonnet-5-5",
      role_models: { qa: "groq/openai/gpt-oss-20b" },
      local_url: "",
    });
  });

  it("defaults to our keys", () => {
    expect(parseChoices(new FormData(), []).mode).toBe("managed");
  });
});
