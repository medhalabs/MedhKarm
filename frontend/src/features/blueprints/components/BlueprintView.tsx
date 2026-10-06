"use client";

import { useActionState, useState, useTransition } from "react";

import { Markdown } from "@/shared/ui/Markdown";

import { approveAction, commentAction, retryAction } from "../api/actions";
import { type Blueprint, type FormState, isBusy } from "../types";

const initial: FormState = { error: null };

/** The documents (pick one to read), Lekha's progress, the comment box and the approve button. */
export function BlueprintView({
  blueprint,
  selected,
}: {
  blueprint: Blueprint;
  selected?: string;
}) {
  const [openId, setOpenId] = useState(selected ?? blueprint.docs[0]?.id);
  const open = blueprint.docs.find((d) => d.id === openId) ?? blueprint.docs[0];
  const busy = isBusy(blueprint.status);
  const [commented, comment, commenting] = useActionState(
    commentAction.bind(null, blueprint.id),
    initial,
  );
  const [approving, approve] = useTransition();
  const [approveError, setApproveError] = useState<string | null>(null);

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[14rem_minmax(0,1fr)]">
      <nav className="card flex flex-col p-2" aria-label="Documents">
        {blueprint.docs.map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => setOpenId(d.id)}
            className={`rounded-lg px-3 py-2 text-left text-sm ${
              d.id === open?.id
                ? "bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800/60"
            }`}
          >
            {d.title}
          </button>
        ))}
        {busy && (
          <p className="px-3 py-2 text-xs text-zinc-500" aria-live="polite">
            {blueprint.progress || "Lekha is working"}…
          </p>
        )}
      </nav>

      <div className="flex min-w-0 flex-col gap-6">
        <article className="card min-h-48 p-6">
          {open ? (
            <>
              <Markdown>{open.content}</Markdown>
              <p className="mt-4 text-xs text-zinc-500">
                Goes into your project as <code>{open.path}</code>
              </p>
            </>
          ) : (
            <p className="text-sm text-zinc-500">
              {blueprint.progress || "Lekha is getting started"}… The first document appears in a
              minute.
            </p>
          )}
        </article>

        {blueprint.status === "failed" && (
          <div className="card flex flex-col gap-3 border-red-200 p-5 dark:border-red-900">
            <p className="text-sm text-red-700 dark:text-red-400">{blueprint.error}</p>
            <form action={() => retryAction(blueprint.id)}>
              <button type="submit" className="btn-secondary">
                Ask Lekha again
              </button>
            </form>
          </div>
        )}

        {blueprint.comments.length > 0 && (
          <section className="card flex flex-col gap-3 p-5" aria-label="Comments">
            {blueprint.comments.map((c) => (
              <p key={c.at} className="text-sm">
                <span className="font-semibold">{c.author === "founder" ? "You" : "Lekha"}: </span>
                {c.text}
              </p>
            ))}
          </section>
        )}

        {blueprint.status === "ready" && (
          <section className="card flex flex-col gap-4 p-5">
            <form action={comment} className="flex flex-col gap-2">
              <label htmlFor="comment" className="text-sm font-medium">
                Want something different? Tell Lekha.
              </label>
              <textarea
                id="comment"
                name="text"
                rows={3}
                maxLength={5000}
                placeholder="e.g. Add a tip option at checkout, and keep the first version to a single shop"
                className="field"
              />
              <div className="flex items-center gap-3">
                <button type="submit" disabled={commenting} className="btn-secondary">
                  {commenting ? "Sending…" : "Ask for changes"}
                </button>
                {commented.error && (
                  <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                    {commented.error}
                  </p>
                )}
              </div>
            </form>
            <div className="flex flex-wrap items-center gap-3 border-t border-zinc-100 pt-4 dark:border-zinc-800">
              <button
                type="button"
                disabled={approving}
                className="btn-primary bg-emerald-600 hover:bg-emerald-500"
                onClick={() =>
                  approve(async () => {
                    const result = await approveAction(blueprint.id);
                    if (result?.error) setApproveError(result.error);
                  })
                }
              >
                {approving ? "Starting the build…" : "Approve the plan and build"}
              </button>
              <span className="text-xs text-zinc-500">
                The team builds the first milestone and puts these documents in your project.
              </span>
              {approveError && (
                <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                  {approveError}
                </p>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
