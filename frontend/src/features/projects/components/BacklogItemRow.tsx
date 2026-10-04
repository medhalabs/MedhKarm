import Link from "next/link";

import { describeItem, itemActions } from "../describe";
import type { BacklogItem } from "../types";
import { ActionButton } from "./ActionButton";
import { StatusBadge } from "./StatusBadge";

const LABELS = { up: "↑", down: "↓", delete: "Delete", skip: "Skip", retry: "Retry" };
const TITLES = {
  up: "Move up",
  down: "Move down",
  delete: "Delete",
  skip: "Skip",
  retry: "Try again",
};

export function BacklogItemRow({ item, count }: { item: BacklogItem; count: number }) {
  const look = describeItem(item.status);
  const actions = itemActions(item).filter(
    (a) => !(a === "up" && item.position === 1) && !(a === "down" && item.position === count),
  );
  return (
    <li className="flex gap-3 py-3">
      <span className="w-6 shrink-0 pt-0.5 text-right font-mono text-xs text-zinc-500">
        {item.position}
      </span>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`font-medium ${item.status === "skipped" ? "text-zinc-400 line-through" : ""}`}
          >
            {item.title}
          </span>
          <span className="rounded border border-zinc-300 px-1 text-xs text-zinc-500 dark:border-zinc-700">
            {item.size}
          </span>
          <StatusBadge label={look.label} tone={look.tone} />
          {item.run_id && (
            <Link
              href={`/admin/runs/${item.run_id}`}
              className="text-xs text-zinc-500 hover:underline"
            >
              run {item.run_id}
              {item.attempts > 1 ? ` (try ${item.attempts})` : ""}
            </Link>
          )}
          {item.pull_request_url && (
            <a
              href={item.pull_request_url}
              className="text-xs text-sky-700 hover:underline dark:text-sky-400"
            >
              pull request
            </a>
          )}
        </div>
        {item.description && (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{item.description}</p>
        )}
        {item.acceptance.length > 0 && (
          <ul className="list-disc pl-5 text-xs text-zinc-500">
            {item.acceptance.map((check) => (
              <li key={check}>{check}</li>
            ))}
          </ul>
        )}
        {item.note && <p className="text-xs text-amber-800 dark:text-amber-400">{item.note}</p>}
      </div>
      {actions.length > 0 && (
        <div className="flex shrink-0 items-start gap-1">
          {actions.map((action) => (
            <ActionButton
              key={action}
              op={action === "up" || action === "down" ? "move" : action}
              projectId={item.project_id}
              itemId={item.id}
              fields={
                action === "up" || action === "down"
                  ? { position: item.position + (action === "up" ? -1 : 1) }
                  : undefined
              }
              label={LABELS[action]}
              title={TITLES[action]}
              look="small"
            />
          ))}
        </div>
      )}
    </li>
  );
}
