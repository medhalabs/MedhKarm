import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { OfficeView } from "@/features/office";
import { factsLine, facts, getPublicShare } from "@/features/shares";
import { WaitlistForm } from "@/features/waitlist";

type Props = PageProps<"/share/[token]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { token } = await params;
  const share = await getPublicShare(token).catch(() => null);
  if (!share) return { title: "MedhKarm", robots: { index: false } };
  const description = `Built by an AI team: ${factsLine(share.stats)}. Watch the time-lapse and the demo.`;
  return {
    title: `${share.title} · built by an AI team`,
    description,
    robots: { index: false }, // a link you share, not a page for search engines
    openGraph: { title: share.title, description, type: "article" },
    twitter: { card: "summary", title: share.title, description },
  };
}

/** A finished build, public: the time-lapse of the team working, the demo video and the facts. */
export default async function SharePage({ params }: Props) {
  const { token } = await params;
  const share = await getPublicShare(token);
  if (!share) notFound();

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white">
            M
          </span>
          <span className="text-sm font-semibold tracking-tight">MedhKarm</span>
        </Link>
        <Link href="/" className="text-sm text-zinc-500 hover:underline">
          What is this?
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-4 pb-16">
        <section>
          <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase dark:text-indigo-300">
            Built by an AI team
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">{share.title}</h1>
          <ul className="mt-3 flex flex-wrap gap-2">
            {facts(share.stats).map((f) => (
              <li
                key={f}
                className="rounded-full bg-white px-3 py-1 text-xs text-zinc-700 ring-1 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700"
              >
                {f}
              </li>
            ))}
          </ul>
          {share.live_url && (
            <a
              href={share.live_url}
              target="_blank"
              rel="noreferrer"
              className="btn-primary mt-4 inline-flex"
            >
              Try the app →
            </a>
          )}
        </section>

        {share.has_demo && (
          <section className="card overflow-hidden" aria-label="Demo">
            <div className="card-header">
              <h2 className="card-title">The demo</h2>
              <span className="text-xs text-zinc-500">
                QA using the app, recorded from its test
              </span>
            </div>
            <div className="p-4">
              <video
                controls
                preload="metadata"
                playsInline
                className="max-h-[28rem] w-full rounded-lg bg-zinc-950"
                src={`/api/shares/${encodeURIComponent(token)}/demo`}
              />
            </div>
          </section>
        )}

        <section aria-label="The team at work">
          <h2 className="mb-3 text-lg font-semibold">Watch the team work</h2>
          <OfficeView
            runId={token}
            team={share.team}
            initialEvents={share.events}
            live={false}
            backHref={null}
          />
        </section>

        <section className="card p-6" aria-label="Join the waitlist">
          <h2 className="text-lg font-semibold">Want a team like this for your idea?</h2>
          <p className="mt-1 mb-4 max-w-xl text-sm text-zinc-600 dark:text-zinc-400">
            MedhKarm is a free community beta for builders in India. Tell your CTO what you want, a
            documentation lead writes the plan, the team builds and tests it, and you approve before
            anything goes live.
          </p>
          <div className="max-w-md">
            <WaitlistForm source="share" />
          </div>
        </section>
      </main>
    </div>
  );
}
