import { headers } from "next/headers";

import { getShare } from "../api/getShare";
import { CopyLink } from "./CopyLink";

/** Share this build with anyone: a public link to the time-lapse and the demo video. */
export async function ShareCard({ runId }: { runId: string }) {
  const share = await getShare(runId).catch(() => null);
  const h = await headers();
  const origin = `${h.get("x-forwarded-proto") ?? "http"}://${h.get("host") ?? "localhost:3000"}`;
  return (
    <section className="card p-5" aria-label="Share">
      <p className="font-semibold">Share this build</p>
      <p className="mt-1 text-sm text-zinc-500">
        A public link to the office time-lapse and the demo video. Anyone can open it, no sign-in.
        They see the title, the team&apos;s steps and the demo, not your request, messages or code.
      </p>
      <CopyLink
        runId={runId}
        url={share ? `${origin}/share/${share.token}` : null}
        views={share?.views ?? 0}
      />
    </section>
  );
}
