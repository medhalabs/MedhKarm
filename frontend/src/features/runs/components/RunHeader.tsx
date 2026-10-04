import { formatDateTime, timeAgo } from "@/shared/lib/format";

import type { Run } from "../types";
import { RunStatusBadge } from "./RunStatusBadge";

export function RunHeader({ run }: { run: Run }) {
  return (
    <header className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <RunStatusBadge status={run.status} />
        <span className="font-mono text-xs text-zinc-500">run {run.id}</span>
        <span className="text-xs text-zinc-500">
          started {formatDateTime(run.created_at)} · last change {timeAgo(run.updated_at)}
        </span>
      </div>
      <p className="text-lg leading-snug font-medium whitespace-pre-line">{run.request}</p>
      {run.repo && (
        <p className="text-sm text-zinc-500">
          On{" "}
          <a href={run.repo.url} className="font-mono underline" target="_blank" rel="noreferrer">
            {run.repo.url.replace("https://github.com/", "")}
          </a>
          {run.repo.branch && <span className="font-mono"> ({run.repo.branch})</span>}
        </p>
      )}
      <p className="text-sm text-zinc-500">
        {run.test_command ? (
          <>
            Done when <code className="font-mono">{run.test_command}</code> passes.
          </>
        ) : (
          "Test command: detected from the project when work starts."
        )}
      </p>
      {run.delivery?.pull_request_url && (
        <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          Pull request opened:{" "}
          <a
            href={run.delivery.pull_request_url}
            className="underline"
            target="_blank"
            rel="noreferrer"
          >
            {run.delivery.pull_request_url}
          </a>
        </p>
      )}
      {!run.repo && run.new_repo && !run.delivery && (
        <p className="text-sm text-zinc-500">
          When released: a new private GitHub repo
          {run.new_repo.name && <span className="font-mono"> {run.new_repo.name}</span>}.
        </p>
      )}
      {run.delivery?.repo_url && (
        <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          Repository created:{" "}
          <a href={run.delivery.repo_url} className="underline" target="_blank" rel="noreferrer">
            {run.delivery.repo_url}
          </a>
        </p>
      )}
      {run.deployment && (
        <p className="text-sm">
          {run.deployment.state === "READY" ? (
            <>
              Live at{" "}
              <a href={run.deployment.url} className="underline" target="_blank" rel="noreferrer">
                {run.deployment.url}
              </a>
            </>
          ) : (
            <span className="text-red-700 dark:text-red-400">
              Couldn&apos;t put it live: {run.deployment.error || run.deployment.state}
            </span>
          )}
        </p>
      )}
      {run.delivery && !run.delivery.pull_request_url && !run.delivery.repo_url && (
        <p className="text-sm text-zinc-500">Not delivered to GitHub: {run.delivery.reason}</p>
      )}
      {run.error && (
        <p
          role="alert"
          className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300"
        >
          {run.error}
        </p>
      )}
    </header>
  );
}
