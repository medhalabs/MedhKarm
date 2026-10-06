import { apiUrl } from "@/shared/api/client";
import { sessionToken } from "@/shared/api/session";

export const dynamic = "force-dynamic";

const PASSED_ON = ["content-type", "content-length", "content-range", "accept-ranges"];

/** Plays one of a run's files (the demo video) with the founder's session token. Byte ranges
 * are passed through: Safari and Chrome won't play or skip through a video without them. */
export async function GET(
  request: Request,
  ctx: RouteContext<"/api/runs/[runId]/artifacts/[artifactId]">,
) {
  const { runId, artifactId } = await ctx.params;
  const token = await sessionToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
  const range = request.headers.get("range");
  if (range) headers.Range = range;
  const upstream = await fetch(
    apiUrl(`/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifactId)}`),
    { headers, signal: request.signal, cache: "no-store" },
  );
  const out = new Headers({ "Cache-Control": "private, max-age=3600" });
  for (const name of PASSED_ON) {
    const value = upstream.headers.get(name);
    if (value) out.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}
