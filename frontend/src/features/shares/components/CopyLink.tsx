"use client";

import { useState, useTransition } from "react";

import { shareAction, stopSharingAction } from "../api/actions";

/** Turn the link on, copy it, or turn it off. */
export function CopyLink({
  runId,
  url,
  views,
}: {
  runId: string;
  url: string | null;
  views: number;
}) {
  const [pending, run] = useTransition();
  const [copied, setCopied] = useState(false);

  if (!url) {
    return (
      <button
        type="button"
        disabled={pending}
        className="btn-secondary mt-3"
        onClick={() => run(() => shareAction(runId))}
      >
        {pending ? "Making the link…" : "Create a public link"}
      </button>
    );
  }
  return (
    <div className="mt-3 flex flex-col gap-2">
      <input
        readOnly
        value={url}
        aria-label="Public link"
        className="field w-full text-xs"
        onFocus={(e) => e.currentTarget.select()}
      />
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="btn-primary"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(url);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            } catch {
              /* the link is selectable above */
            }
          }}
        >
          {copied ? "Copied" : "Copy link"}
        </button>
        <button
          type="button"
          disabled={pending}
          className="btn-secondary"
          onClick={() => run(() => stopSharingAction(runId))}
        >
          Stop sharing
        </button>
        <span className="text-xs text-zinc-500">
          Opened {views} time{views === 1 ? "" : "s"}
        </span>
      </div>
    </div>
  );
}
