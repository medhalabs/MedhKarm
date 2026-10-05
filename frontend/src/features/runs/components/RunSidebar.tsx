import Link from "next/link";

import { OfficeIcon } from "@/shared/ui/icons";

import type { Run, RunStatus } from "../types";
import { CancelRunButton } from "./CancelRunButton";

const CANCELLABLE: RunStatus[] = ["queued", "running", "waiting_for_approval"];

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 px-5 py-3">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="text-sm break-words text-zinc-800 dark:text-zinc-200">{children}</dd>
    </div>
  );
}

function ExternalLink({ href }: { href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-indigo-600 underline-offset-2 hover:underline dark:text-indigo-400"
    >
      {href.replace(/^https:\/\/(github\.com\/)?/, "")}
    </a>
  );
}

/** The office link, the run's facts and where its work went, and Cancel. */
export function RunSidebar({ run }: { run: Run }) {
  return (
    <aside className="flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start">
      <Link
        href={`/admin/runs/${run.id}/office`}
        className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-5 text-white shadow-sm"
      >
        <div className="absolute -top-6 -right-6 h-24 w-24 rounded-full bg-white/10" />
        <div className="absolute right-8 -bottom-8 h-20 w-20 rounded-full bg-white/10" />
        <OfficeIcon className="h-6 w-6 opacity-90" />
        <p className="mt-3 font-semibold">Watch the team</p>
        <p className="mt-1 text-sm text-indigo-100">
          See who&apos;s doing what in the office, live or as a replay.
        </p>
        <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium group-hover:underline">
          Open the office →
        </span>
      </Link>

      <dl className="card divide-y divide-zinc-100 dark:divide-zinc-800">
        <Row label="Run">
          <span className="font-mono text-xs">{run.id}</span>
        </Row>
        <Row label="Done when">
          {run.test_command ? (
            <code className="font-mono text-xs">{run.test_command}</code>
          ) : (
            "Detected from the project"
          )}
        </Row>
        {run.repo && (
          <Row label="Repository">
            <ExternalLink href={run.repo.url} />
            {run.repo.branch && <span className="font-mono text-xs"> ({run.repo.branch})</span>}
          </Row>
        )}
        {!run.repo && run.new_repo && !run.delivery && (
          <Row label="When released">
            A new private GitHub repo
            {run.new_repo.name && <span className="font-mono text-xs"> {run.new_repo.name}</span>}
          </Row>
        )}
        {run.delivery?.pull_request_url && (
          <Row label="Pull request">
            <ExternalLink href={run.delivery.pull_request_url} />
          </Row>
        )}
        {run.delivery?.repo_url && (
          <Row label="Repository created">
            <ExternalLink href={run.delivery.repo_url} />
          </Row>
        )}
        {run.delivery && !run.delivery.pull_request_url && !run.delivery.repo_url && (
          <Row label="GitHub">Not delivered: {run.delivery.reason}</Row>
        )}
        {run.deployment && (
          <Row label="Live">
            {run.deployment.state === "READY" ? (
              <ExternalLink href={run.deployment.url} />
            ) : (
              <span className="text-red-700 dark:text-red-400">
                Couldn&apos;t put it live: {run.deployment.error || run.deployment.state}
              </span>
            )}
          </Row>
        )}
      </dl>

      {CANCELLABLE.includes(run.status) && <CancelRunButton runId={run.id} />}
    </aside>
  );
}
