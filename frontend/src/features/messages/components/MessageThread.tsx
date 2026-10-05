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
    <section className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <h2 className="font-semibold">Messages</h2>
      <MessageList messages={messages} />
      {waiting && (
        <p className="text-xs text-zinc-500">Waiting for a reply… refresh in a minute.</p>
      )}
      <MessageForm thread={thread} threadId={threadId} />
    </section>
  );
}
