import type { HealthStatus } from "./types";

/** Turns a health response (or null when unreachable) into what the UI shows. */
export function describeHealth(health: HealthStatus | null): { label: string; healthy: boolean } {
  if (!health) {
    return { label: "Backend unreachable", healthy: false };
  }
  const healthy = health.status === "ok";
  return {
    label: healthy
      ? `Backend OK · ${health.service} v${health.version} (${health.environment})`
      : `Backend reports: ${health.status}`,
    healthy,
  };
}
