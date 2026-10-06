import { STATE_LOOK, overall } from "../signoffLabel";
import { getSignoffs } from "../api/getSignoffs";
import type { Signoff } from "../types";

function Row({ s, compact, runId }: { s: Signoff; compact: boolean; runId: string }) {
  const look = STATE_LOOK[s.state];
  return (
    <li className="flex gap-3 px-5 py-3">
      <span
        className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold ${look.tone}`}
        title={look.word}
        aria-label={look.word}
      >
        {look.mark}
      </span>
      <div className="min-w-0 text-sm">
        <p className="font-medium">
          {s.name} <span className="font-normal text-zinc-500">· {s.title}</span>
        </p>
        <p className="text-zinc-600 dark:text-zinc-400">
          {s.headline}
          {s.url && (
            <>
              {" "}
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="text-indigo-600 underline-offset-2 hover:underline dark:text-indigo-400"
              >
                Open →
              </a>
            </>
          )}
        </p>
        {s.video_id !== null && (
          <p className="mt-0.5">
            <a
              href={`/admin/runs/${runId}#demo`}
              className="text-indigo-600 underline-offset-2 hover:underline dark:text-indigo-400"
            >
              ▶ Watch the demo
            </a>
          </p>
        )}
        {!compact && s.details.length > 0 && (
          <ul className="mt-1 list-disc pl-4 text-xs text-zinc-500">
            {s.details.slice(0, 5).map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
        )}
      </div>
    </li>
  );
}

/** Who signed off the release and what they say: developers, CTO, QA, security, DevOps, the
 * documentation lead, and you. Built from the run's activity log. */
export async function SignoffCard({
  runId,
  compact = false,
}: {
  runId: string;
  compact?: boolean;
}) {
  const signoffs = await getSignoffs(runId).catch(() => null);
  if (!signoffs) return null;
  return (
    <section className="card" aria-label="Release sign-off">
      <div className="card-header">
        <h2 className="card-title">Release sign-off</h2>
        <span className="text-xs text-zinc-500">{overall(signoffs.map((s) => s.state))}</span>
      </div>
      <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
        {signoffs.map((s) => (
          <Row key={s.role} s={s} compact={compact} runId={runId} />
        ))}
      </ul>
    </section>
  );
}
