/** Server-sent events: everything after `afterId`, live. Goes through this app
 * (app/api/runs/[runId]/events/stream), which adds the session token: the browser's
 * EventSource can't send one itself. */
export function eventStreamUrl(runId: string, afterId: number): string {
  return `/api/runs/${encodeURIComponent(runId)}/events/stream?after_id=${afterId}`;
}
