import { describe, expect, it } from "vitest";

import { describeHealth } from "./describeHealth";

describe("describeHealth", () => {
  it("reports unreachable when there is no response", () => {
    expect(describeHealth(null)).toEqual({ label: "Backend unreachable", healthy: false });
  });

  it("reports healthy with service details when status is ok", () => {
    const result = describeHealth({
      status: "ok",
      service: "MedhKarm API",
      version: "0.1.0",
      environment: "development",
    });

    expect(result.healthy).toBe(true);
    expect(result.label).toBe("Backend OK · MedhKarm API v0.1.0 (development)");
  });

  it("reports unhealthy for any other status", () => {
    const result = describeHealth({
      status: "degraded",
      service: "MedhKarm API",
      version: "0.1.0",
      environment: "development",
    });

    expect(result.healthy).toBe(false);
  });
});
