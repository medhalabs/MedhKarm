"use client";

import { useEffect, useRef, useState, useTransition } from "react";

import { Markdown } from "./Markdown";

export type ChatTurn = { role: "founder" | "agent"; text: string };
export type ChatAnswer<T> = { text: string; brief: T | null } | { error: string };
type Done = { error: string } | undefined | void;

type Props<T> = {
  agent: { name: string; initial: string };
  title: string;
  subtitle: string;
  greeting: string;
  examples: string[];
  placeholder: string;
  skipLabel: string;
  ask: (turns: ChatTurn[]) => Promise<ChatAnswer<T>>;
  start: (brief: T) => Promise<Done>;
  skip: (text: string) => Promise<Done>;
  renderBrief: (
    brief: T,
    controls: { pending: boolean; start: () => void; keepTalking: () => void },
  ) => React.ReactNode;
};

function Bubble({ turn, initial }: { turn: ChatTurn; initial: string }) {
  const mine = turn.role === "founder";
  return (
    <div className={`flex gap-3 ${mine ? "justify-end" : ""}`}>
      {!mine && (
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
          {initial}
        </span>
      )}
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
          mine
            ? "rounded-br-md bg-indigo-600 text-white"
            : "rounded-bl-md bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
        }`}
      >
        {mine ? (
          <p className="leading-relaxed whitespace-pre-line">
            {turn.text.length > 1200 ? `${turn.text.slice(0, 1200)}…` : turn.text}
          </p>
        ) : (
          <Markdown>{turn.text}</Markdown>
        )}
      </div>
    </div>
  );
}

/** Talking to an agent until they hand over a brief the founder confirms (runs with the CTO,
 * projects with the PM). The conversation lives here, in the browser. */
export function ChatIntake<T>(props: Props<T>) {
  const { agent } = props;
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [brief, setBrief] = useState<T | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, run] = useTransition();
  const input = useRef<HTMLTextAreaElement>(null);
  const [focusTick, setFocusTick] = useState(0);
  useEffect(() => {
    if (focusTick) input.current?.focus();
  }, [focusTick]);

  function send(text: string) {
    const message = text.trim();
    if (!message || pending) return;
    const next: ChatTurn[] = [...turns, { role: "founder", text: message }];
    setTurns(next);
    setDraft("");
    setBrief(null);
    setError(null);
    run(async () => {
      const answer = await props.ask(next);
      if ("error" in answer) {
        setError(answer.error);
        return;
      }
      setTurns([...next, { role: "agent", text: answer.text }]);
      setBrief(answer.brief);
    });
  }

  function finish(action: () => Promise<Done>) {
    setError(null);
    run(async () => {
      const result = await action();
      if (result && "error" in result) setError(result.error);
    });
  }

  const written = [...turns.filter((t) => t.role === "founder").map((t) => t.text), draft.trim()]
    .filter(Boolean)
    .join("\n\n");

  return (
    <section className="card flex flex-col">
      <div className="card-header">
        <div>
          <h2 className="card-title">{props.title}</h2>
          <p className="mt-0.5 text-xs text-zinc-500">{props.subtitle}</p>
        </div>
        {turns.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setTurns([]);
              setBrief(null);
              setError(null);
            }}
            className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Start over
          </button>
        )}
      </div>

      <div className="flex flex-col gap-4 p-5" aria-live="polite">
        <Bubble turn={{ role: "agent", text: props.greeting }} initial={agent.initial} />
        {turns.length === 0 && (
          <div className="flex flex-wrap gap-2 pl-11">
            {props.examples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => {
                  setDraft(example);
                  input.current?.focus();
                }}
                className="rounded-full border border-zinc-200 px-3 py-1 text-left text-xs text-zinc-600 transition hover:border-indigo-300 hover:text-indigo-700 dark:border-zinc-700 dark:text-zinc-400"
              >
                {example}
              </button>
            ))}
          </div>
        )}
        {turns.map((turn, i) => (
          <Bubble key={i} turn={turn} initial={agent.initial} />
        ))}
        {pending && !brief && (
          <div className="flex items-center gap-3 pl-11 text-xs text-zinc-500">
            <span className="flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:300ms]" />
            </span>
            {agent.name} is thinking…
          </div>
        )}
        {brief &&
          props.renderBrief(brief, {
            pending,
            start: () => finish(() => props.start(brief)),
            keepTalking: () => {
              setBrief(null);
              setFocusTick((t) => t + 1);
            },
          })}
        {error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="flex flex-col gap-2 border-t border-zinc-100 p-4 dark:border-zinc-800"
      >
        <textarea
          ref={input}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              send(draft);
            }
          }}
          rows={turns.length ? 2 : 3}
          maxLength={50000}
          aria-label={`Message to ${agent.name}`}
          placeholder={turns.length ? `Reply to ${agent.name}…` : props.placeholder}
          className="field resize-y leading-relaxed"
        />
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={() =>
              written.length < 3
                ? setError("Write what you'd like built first.")
                : finish(() => props.skip(written))
            }
            disabled={pending}
            className="text-xs text-zinc-500 hover:text-zinc-900 disabled:opacity-50 dark:hover:text-zinc-100"
          >
            {props.skipLabel}
          </button>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-zinc-400 sm:inline">⌘ + Enter to send</span>
            <button type="submit" disabled={pending || !draft.trim()} className="btn-primary">
              Send
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
