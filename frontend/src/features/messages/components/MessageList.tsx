import { timeAgo } from "@/shared/lib/format";

import type { Message } from "../types";

export function MessageList({ messages }: { messages: Message[] }) {
  if (messages.length === 0) return null;
  return (
    <ul className="flex flex-col gap-2">
      {messages.map((m) => (
        <li
          key={m.id}
          className={`rounded-md p-3 text-sm ${
            m.author === "founder"
              ? "bg-zinc-100 dark:bg-zinc-900"
              : "border border-zinc-200 dark:border-zinc-800"
          }`}
        >
          <p className="mb-1 text-xs text-zinc-500">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">{m.name}</span> ·{" "}
            {timeAgo(m.created_at)}
          </p>
          <p className="whitespace-pre-line">{m.body}</p>
        </li>
      ))}
    </ul>
  );
}
