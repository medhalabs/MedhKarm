"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { eventStreamUrl, type ActivityEvent } from "@/features/events/client";

import { officeState } from "../officeState";
import { taskBoard } from "../taskBoard";
import type { Member } from "../types";
import { OfficeFloor } from "./OfficeFloor";
import { TaskBoard } from "./TaskBoard";

const QUIET = new Set(["model.used"]); // too frequent to pace a replay by
const SPEEDS = [1, 2, 4];
const STEP_MS = 1400; // one event per step at 1×: agents finish tasks in seconds

function merge(known: ActivityEvent[], incoming: ActivityEvent[]): ActivityEvent[] {
  const seen = new Set(known.map((e) => e.id));
  return [...known, ...incoming.filter((e) => !seen.has(e.id))].sort((a, b) => a.id - b.id);
}

/** The office for one run: live while it runs, or replayed as a paced time-lapse. */
export function OfficeView({
  runId,
  team,
  initialEvents,
}: {
  runId: string;
  team: Member[];
  initialEvents: ActivityEvent[];
}) {
  const [events, setEvents] = useState(initialEvents);
  const finished = events.some((e) => e.type === "run.finished");
  const [mode, setMode] = useState<"live" | "replay">(finished ? "replay" : "live");
  const steps = useMemo(() => events.filter((e) => !QUIET.has(e.type)), [events]);
  const [step, setStep] = useState(finished ? 0 : steps.length);
  const [playing, setPlaying] = useState(finished);
  const [speed, setSpeed] = useState(2);
  const lastId = useRef(initialEvents.at(-1)?.id ?? 0);

  // Live: follow the run's activity stream until it finishes
  useEffect(() => {
    if (finished) return;
    const source = new EventSource(eventStreamUrl(runId, lastId.current));
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as ActivityEvent;
      lastId.current = Math.max(lastId.current, event.id);
      setEvents((known) => merge(known, [event]));
    };
    return () => source.close();
  }, [runId, finished]);

  // Replay: one step at a time; it stops by itself at the end
  const running = mode === "replay" && playing && step < steps.length;
  useEffect(() => {
    if (!running) return;
    const timer = setTimeout(() => setStep((s) => s + 1), STEP_MS / speed);
    return () => clearTimeout(timer);
  }, [running, step, speed]);

  const shown = mode === "live" ? events : events.filter((e) => e.id <= (steps[step - 1]?.id ?? 0));
  const state = useMemo(() => officeState(team, shown), [team, shown]);
  const board = useMemo(() => taskBoard(shown), [shown]);
  const current = mode === "live" ? steps.at(-1) : steps[step - 1];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <Link href={`/admin/runs/${runId}`} className="text-zinc-500 hover:underline">
          ← Back to the run
        </Link>
        <div
          className="ml-auto flex rounded-md border border-zinc-300 dark:border-zinc-700"
          role="group"
          aria-label="View"
        >
          {(["live", "replay"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => {
                setMode(m);
                if (m === "replay") {
                  setStep(0);
                  setPlaying(true);
                }
              }}
              aria-pressed={mode === m}
              className={`px-3 py-1 ${mode === m ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900" : ""}`}
            >
              {m === "live" ? (finished ? "Final" : "Live") : "Replay"}
            </button>
          ))}
        </div>
      </div>

      <OfficeFloor team={team} state={state} />

      <p className="min-h-6 text-sm text-zinc-600 dark:text-zinc-400" aria-live="polite">
        {current ? current.summary : "Nothing has happened yet."}
      </p>

      {mode === "replay" && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <button
            type="button"
            onClick={() => {
              if (step >= steps.length) {
                setStep(0);
                setPlaying(true);
              } else setPlaying(!running);
            }}
            className="w-20 rounded-md border border-zinc-300 px-3 py-1 dark:border-zinc-700"
          >
            {running ? "Pause" : "Play"}
          </button>
          <input
            type="range"
            min={0}
            max={steps.length}
            value={step}
            onChange={(e) => {
              setPlaying(false);
              setStep(Number(e.target.value));
            }}
            aria-label="Replay position"
            className="min-w-48 flex-1"
          />
          <span className="tabular-nums text-zinc-500">
            {step} / {steps.length}
          </span>
          <div className="flex gap-1" role="group" aria-label="Speed">
            {SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSpeed(s)}
                aria-pressed={speed === s}
                className={`rounded px-2 py-0.5 ${speed === s ? "bg-zinc-200 dark:bg-zinc-800" : ""}`}
              >
                {s}×
              </button>
            ))}
          </div>
        </div>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="font-semibold">Task board</h2>
        <TaskBoard tasks={board} />
      </section>
    </div>
  );
}
