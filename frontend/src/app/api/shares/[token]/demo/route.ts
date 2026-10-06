import { apiUrl } from "@/shared/api/client";

export const dynamic = "force-dynamic";

const PASSED_ON = ["content-type", "content-length", "content-range", "accept-ranges"];

/** Plays a shared build's demo video for anyone with the link. No sign-in is involved, and byte
 * ranges are passed through: browsers won't play or skip through a video without them. */
export async function GET(request: Request, ctx: RouteContext<"/api/shares/[token]/demo">) {
  const { token } = await ctx.params;
  const headers: Record<string, string> = {};
  const range = request.headers.get("range");
  if (range) headers.Range = range;
  const upstream = await fetch(apiUrl(`/public/shares/${encodeURIComponent(token)}/demo`), {
    headers,
    signal: request.signal,
    cache: "no-store",
  });
  const out = new Headers({ "Cache-Control": "public, max-age=300" });
  for (const name of PASSED_ON) {
    const value = upstream.headers.get(name);
    if (value) out.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}
