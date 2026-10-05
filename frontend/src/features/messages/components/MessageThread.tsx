import { ScrollArea } from "@/shared/ui/ScrollArea";

import { getThread } from "../api/getThread";
import { MessageForm } from "./MessageForm";
import { MessageList } from "./MessageList";

/** Talk to the team about a run or a project. Replies arrive within a minute or so. */
export async function MessageThread({
  thread,
  threadId,
}: {
  thread: "run" | "project";
  threadId: string;
}) {
  const messages = await getThread(thread, threadId).catch(() => []);
  const waiting = messages.length > 0 && messages[messages.length - 1].author === "founder";
  return (
    <section className="card flex flex-col gap-4 p-5">
      <div>
        <h2 className="card-title">Messages</h2>
        <p className="mt-0.5 text-xs text-zinc-500">
          Write to anyone on the team; it reaches their next piece of work.
        </p>
      </div>
      {messages.length > 0 && (
        <ScrollArea className="max-h-80 pr-1" stickToBottom>
          <MessageList messages={messages} />
        </ScrollArea>
      )}
      {waiting && (
        <p className="text-xs text-zinc-500">Waiting for a reply… refresh in a minute.</p>
      )}
      <MessageForm thread={thread} threadId={threadId} />
    </section>
  );
}
