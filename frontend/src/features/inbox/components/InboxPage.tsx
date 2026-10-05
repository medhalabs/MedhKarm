import Link from "next/link";

import { MessageList } from "@/features/messages";
import { timeAgo } from "@/shared/lib/format";

import { decideAction, itemAction } from "../api/actions";
import { getInbox } from "../api/getInbox";
import { AnswerForm } from "./AnswerForm";

const card = "flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800";
const button =
  "rounded-md px-3 py-1.5 text-sm font-medium border border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900";

/** Everything waiting for the founder: releases, Mira's questions, blocked work, replies. */
export async function InboxPage() {
  const inbox = await getInbox();
  const empty = !inbox.approvals.length && !inbox.questions.length && !inbox.blocked.length;

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-semibold">Inbox</h1>
      {empty && <p className="text-zinc-500">Nothing needs you right now.</p>}

      {inbox.approvals.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-semibold">Waiting for your approval</h2>
          {inbox.approvals.map((a) => (
            <article key={a.run_id} className={card}>
              <p className="font-medium">{a.request.split("\n")[0]}</p>
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
                  <button type="submit" className={`${button} bg-emerald-50 dark:bg-emerald-950`}>
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
          <h2 className="font-semibold">Mira&apos;s questions</h2>
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
          <h2 className="font-semibold">Blocked work</h2>
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
          <h2 className="font-semibold">Latest replies from the team</h2>
          <MessageList messages={inbox.replies} />
        </section>
      )}
    </div>
  );
}
