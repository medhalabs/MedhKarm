import Link from "next/link";

import { DemoCard } from "@/features/artifacts";
import { MessageList } from "@/features/messages";
import { SignoffCard } from "@/features/signoffs";
import { timeAgo } from "@/shared/lib/format";
import { titleFrom } from "@/shared/lib/title";
import { PageHeader } from "@/shared/ui/PageHeader";

import { decideAction, itemAction } from "../api/actions";
import { getInbox } from "../api/getInbox";
import { AnswerForm } from "./AnswerForm";

const card = "card flex flex-col gap-3 p-5";
const button = "btn-secondary";

/** Everything waiting for the founder: releases, Mira's questions, blocked work, replies. */
export async function InboxPage() {
  const inbox = await getInbox();
  const empty =
    !inbox.plans.length &&
    !inbox.approvals.length &&
    !inbox.questions.length &&
    !inbox.blocked.length;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Inbox" description="Everything your team needs from you, in one place." />
      {empty && (
        <p className="card p-8 text-center text-sm text-zinc-500">
          Nothing needs you right now. The team will let you know.
        </p>
      )}

      {inbox.plans.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-500">Plans to read and approve</h2>
          {inbox.plans.map((p) => (
            <article key={p.blueprint_id} className={card}>
              <p className="font-medium">{p.title}</p>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <span className="text-zinc-500">Lekha finished {timeAgo(p.waiting_since)}</span>
                <Link href={`/admin/blueprints/${p.blueprint_id}`} className="btn-primary ml-auto">
                  Read the plan
                </Link>
              </div>
            </article>
          ))}
        </section>
      )}

      {inbox.approvals.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-500">Waiting for your approval</h2>
          {inbox.approvals.map((a) => (
            <article key={a.run_id} className={card}>
              <p className="font-medium">{titleFrom(a.request)}</p>
              {a.summary && <p className="text-sm text-zinc-600 dark:text-zinc-400">{a.summary}</p>}
              {a.reasons.length > 0 && (
                <ul className="list-disc pl-5 text-sm text-amber-800 dark:text-amber-300">
                  {a.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              )}
              {a.security.length > 0 && (
                <p className="text-sm text-amber-800 dark:text-amber-300">
                  Security: {a.security.join("; ")}
                </p>
              )}
              <DemoCard runId={a.run_id} compact />
              <SignoffCard runId={a.run_id} compact />
              <div className="flex flex-wrap items-center gap-3 text-sm">
                {a.preview_url && (
                  <a href={a.preview_url} target="_blank" rel="noreferrer" className="underline">
                    Try the preview →
                  </a>
                )}
                <Link href={`/admin/runs/${a.run_id}`} className="underline">
                  See the run
                </Link>
                <span className="text-zinc-500">waiting {timeAgo(a.waiting_since)}</span>
                <form action={decideAction.bind(null, a.run_id, true)} className="ml-auto">
                  <button type="submit" className="btn-primary bg-emerald-600 hover:bg-emerald-500">
                    Approve
                  </button>
                </form>
                <form action={decideAction.bind(null, a.run_id, false)}>
                  <button type="submit" className={button}>
                    Reject
                  </button>
                </form>
              </div>
            </article>
          ))}
        </section>
      )}

      {inbox.questions.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-500">Mira&apos;s questions</h2>
          {inbox.questions.map((q) => (
            <article key={q.project_id} className={card}>
              <Link href={`/admin/projects/${q.project_id}`} className="font-medium underline">
                {q.project_name}
              </Link>
              <AnswerForm project={q} />
            </article>
          ))}
        </section>
      )}

      {inbox.blocked.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-500">Blocked work</h2>
          {inbox.blocked.map((b) => (
            <article key={b.item_id} className={card}>
              <p>
                <span className="font-medium">{b.title}</span>{" "}
                <Link
                  href={`/admin/projects/${b.project_id}`}
                  className="text-sm text-zinc-500 underline"
                >
                  {b.project_name}
                </Link>
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">{b.note}</p>
              <div className="flex gap-3">
                <form action={itemAction.bind(null, b.project_id, b.item_id, "retry")}>
                  <button type="submit" className={button}>
                    Retry
                  </button>
                </form>
                <form action={itemAction.bind(null, b.project_id, b.item_id, "skip")}>
                  <button type="submit" className={button}>
                    Skip
                  </button>
                </form>
              </div>
            </article>
          ))}
        </section>
      )}

      {inbox.replies.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-500">Latest replies from the team</h2>
          <MessageList messages={inbox.replies} />
        </section>
      )}
    </div>
  );
}
