import { apiUrl } from "@/shared/api/client";
import { sessionToken } from "@/shared/api/session";

export const dynamic = "force-dynamic";

/** Passes a run's live activity through from the backend, with the founder's session token. */
export async function GET(request: Request, ctx: RouteContext<"/api/runs/[runId]/events/stream">) {
  const { runId } = await ctx.params;
  const afterId = new URL(request.url).searchParams.get("after_id") ?? "0";
  const token = await sessionToken();
  const upstream = await fetch(
    apiUrl(
      `/runs/${encodeURIComponent(runId)}/events/stream?after_id=${encodeURIComponent(afterId)}`,
    ),
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: request.signal,
      cache: "no-store",
    },
  );
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("Content-Type") ?? "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
