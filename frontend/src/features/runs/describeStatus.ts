import type { RunStatus } from "./types";

type StatusLook = {
  label: string;
  tone: "neutral" | "busy" | "attention" | "good" | "bad";
  active: boolean; // the team is (or will be) working on it: worth refreshing
};

const LOOKS: Record<RunStatus, StatusLook> = {
  queued: { label: "Queued", tone: "neutral", active: true },
  running: { label: "Working", tone: "busy", active: true },
  waiting_for_approval: { label: "Needs you", tone: "attention", active: false },
  released: { label: "Released", tone: "good", active: false },
  rejected: { label: "Stopped by you", tone: "neutral", active: false },
  failed: { label: "Checks failed", tone: "bad", active: false },
  error: { label: "Something broke", tone: "bad", active: false },
  cancelled: { label: "Cancelled", tone: "neutral", active: false },
};

export function describeStatus(status: RunStatus): StatusLook {
  return LOOKS[status] ?? { label: status, tone: "neutral", active: false };
}

/** The founder's request, shortened for lists: its first line, at most `max` characters. */
export function shortRequest(request: string, max = 90): string {
  const firstLine = request.trim().split("\n")[0] ?? "";
  return firstLine.length <= max ? firstLine : `${firstLine.slice(0, max - 1).trimEnd()}…`;
}
