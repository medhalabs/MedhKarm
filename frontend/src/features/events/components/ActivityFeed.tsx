"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { formatNumber } from "@/shared/lib/format";

import { eventStreamUrl } from "../api/streamUrl";
import { isFinished, mergeEvents, STATUS_CHANGING, totalTokens } from "../describeEvent";
import { EVENT_TYPES, type ActivityEvent } from "../types";
import { EventRow } from "./EventRow";

const RECONNECT_MS = 3000;

/**
 * A run's activity, live. Starts from the events the server rendered, then follows the
 * backend's event stream. When a step may have changed the run's status (gate reached,
 * decided, finished), it refreshes the page around it.
 */
export function ActivityFeed({
  runId,
  initialEvents,
}: {
  runId: string;
  initialEvents: ActivityEvent[];
}) {
  const router = useRouter();
  const [events, setEvents] = useState(initialEvents);
  const [live, setLive] = useState(false);
  const [showThinking, setShowThinking] = useState(false);
  const lastId = useRef(initialEvents.at(-1)?.id ?? 0);
  const finished = isFinished(events);

  useEffect(() => {
    if (finished) return;
    let source: EventSource | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let closed = false;

    const connect = () => {
      source = new EventSource(eventStreamUrl(runId, lastId.current));
      source.onopen = () => setLive(true);
      const onEvent = (message: MessageEvent<string>) => {
        const event = JSON.parse(message.data) as ActivityEvent;
        lastId.current = Math.max(lastId.current, event.id);
        setEvents((shown) => mergeEvents(shown, [event]));
        if (STATUS_CHANGING.has(event.type)) router.refresh();
      };
      for (const type of EVENT_TYPES) source.addEventListener(type, onEvent);
      // The backend ends the stream after a quiet spell or when the run finishes; the browser
      // would reconnect from the start, so reconnect ourselves from the last event seen.
      source.onerror = () => {
        source?.close();
        setLive(false);
        if (!closed) retry = setTimeout(connect, RECONNECT_MS);
      };
    };
    connect();

    return () => {
      closed = true;
      clearTimeout(retry);
      source?.close();
    };
  }, [runId, finished, router]);

  const shown = showThinking ? events : events.filter((event) => event.type !== "model.used");

  return (
    <section className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          Activity
          {!finished && (
            <span className={`text-xs font-normal ${live ? "text-emerald-600" : "text-zinc-500"}`}>
              {live ? "● live" : "connecting…"}
            </span>
          )}
        </h2>
        <div className="flex items-center gap-4 text-sm text-zinc-500">
          <span>
            {formatNumber(events.length)} events · {formatNumber(totalTokens(events))} tokens
          </span>
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={showThinking}
              onChange={(e) => setShowThinking(e.target.checked)}
            />
            Show model calls
          </label>
        </div>
      </div>
      {shown.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Nothing yet. The team starts once a worker picks the run up.
        </p>
      ) : (
        <ol className="divide-y divide-zinc-100 dark:divide-zinc-900">
          {[...shown].reverse().map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </ol>
      )}
    </section>
  );
}
