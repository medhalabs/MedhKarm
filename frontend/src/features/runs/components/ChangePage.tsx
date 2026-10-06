import Link from "next/link";
import { notFound } from "next/navigation";

import { titleFrom } from "@/shared/lib/title";
import { PageHeader } from "@/shared/ui/PageHeader";

import { getRun } from "../api/getRun";
import { hasOpenPullRequest, liveRepoUrl } from "../liveRepo";
import { IntakeChat } from "./IntakeChat";

/** Ask for a change to a released project: the same conversation with Kabir, about that
 * project's repository. Small changes can be built straight away; bigger ones get a plan. */
export async function ChangePage({ runId }: { runId: string }) {
  const run = await getRun(runId);
  if (!run) notFound();
  const repo = liveRepoUrl(run);
  const name = titleFrom(run.request, 80);

  return (
    <div className="flex flex-col gap-6">
      <Link
        href={`/admin/runs/${run.id}`}
        className="w-fit text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
      >
        ← Back to the run
      </Link>
      <PageHeader
        title="Request a change"
        description={`A change to “${name}”. Tell Kabir what you'd like different.`}
      />
      {repo ? (
        <>
          {hasOpenPullRequest(run) && (
            <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
              Your last release is still an open pull request on GitHub. Merge it first, or the team
              will start this change without it.
            </p>
          )}
          <IntakeChat about={{ repo_url: repo, name }} />
        </>
      ) : (
        <p className="card p-6 text-sm text-zinc-600 dark:text-zinc-400">
          {run.status === "released"
            ? "This release never reached GitHub, so there's nothing for a change to build on yet. Connect GitHub (a token on the server) and release again."
            : "Changes can be requested once the work is released."}
        </p>
      )}
    </div>
  );
}
