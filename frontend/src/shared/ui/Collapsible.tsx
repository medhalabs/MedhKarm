"use client";

import { useState } from "react";

import { ChevronIcon } from "./icons";

/** Long content shown as a preview with a fade; "Show all" opens it. Short content shows whole. */
export function Collapsible({ long, children }: { long: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(!long);
  return (
    <div>
      <div className={open ? "" : "relative max-h-48 overflow-hidden"}>
        {children}
        {!open && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-white dark:from-zinc-900" />
        )}
      </div>
      {long && (
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
        >
          {open ? "Show less" : "Show the full request"}
          <ChevronIcon className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
        </button>
      )}
    </div>
  );
}
