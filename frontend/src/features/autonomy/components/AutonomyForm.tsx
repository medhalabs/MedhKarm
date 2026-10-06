"use client";

import { useActionState, useTransition } from "react";

import { resetAutonomyAction, saveAutonomyAction } from "../api/actions";
import type { AutonomyView, FormState, Level } from "../types";

const initial: FormState = { error: null };

const LEVELS: { value: Level; title: string; text: string }[] = [
  {
    value: "every",
    title: "Ask me before every release",
    text: "Nothing goes out without your yes. The safest choice, and where everyone starts.",
  },
  {
    value: "small",
    title: "Release small, clean changes on its own",
    text: "A few files, checks passed, nothing open. Everything bigger waits for you.",
  },
  {
    value: "checks",
    title: "Release on its own when every check passes",
    text: "The team ships as soon as tests, QA and security are happy, unless a question below applies.",
  },
];

function Check({
  name,
  checked,
  children,
}: {
  name: string;
  checked: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="flex items-start gap-2 text-sm">
      <input type="checkbox" name={name} defaultChecked={checked} className="mt-1" />
      <span>{children}</span>
    </label>
  );
}

function Num({ name, value, suffix }: { name: string; value: number; suffix: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      <input
        name={name}
        defaultValue={value}
        inputMode="numeric"
        className="field w-24 px-2 py-0.5 text-sm"
        aria-label={suffix}
      />
      {suffix}
    </span>
  );
}

/** The dial, what still asks, what is never allowed, and going live. */
export function AutonomyForm({ view }: { view: AutonomyView }) {
  const projectId = view.project_id ?? "";
  const [state, save, saving] = useActionState(saveAutonomyAction.bind(null, projectId), initial);
  const [resetting, reset] = useTransition();
  const s = view.settings;

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <form action={save} className="card flex flex-col">
        <div className="card-header">
          <h2 className="card-title">{view.scope === "project" ? "This project" : "Everything"}</h2>
          {view.scope === "project" && !view.own && (
            <span className="text-xs text-zinc-500">Using your settings for everything</span>
          )}
        </div>
        <div className="flex flex-col gap-6 p-5">
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-sm font-medium">
              How much should the team do on its own?
            </legend>
            {LEVELS.map((l) => (
              <label
                key={l.value}
                className="flex cursor-pointer gap-3 rounded-xl border border-zinc-200 p-3 has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-50/60 dark:border-zinc-800 dark:has-[:checked]:bg-indigo-950/30"
              >
                <input
                  type="radio"
                  name="level"
                  value={l.value}
                  defaultChecked={s.level === l.value}
                  className="mt-1"
                />
                <span>
                  <span className="block text-sm font-semibold">{l.title}</span>
                  <span className="block text-xs text-zinc-500">{l.text}</span>
                </span>
              </label>
            ))}
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              &ldquo;Small&rdquo; means{" "}
              <Num name="small_files" value={s.small_files} suffix="files or fewer" />
            </p>
          </fieldset>

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-sm font-medium">
              Always stop and ask me when… (when it isn&apos;t asking about every release)
            </legend>
            <Check name="ask_sensitive_files" checked={s.ask_sensitive_files}>
              it changes secrets, dependencies, the database or deployment settings
            </Check>
            <Check name="ask_open_comments" checked={s.ask_open_comments}>
              the CTO accepted work with review comments still open
            </Check>
            <Check name="ask_security_warnings" checked={s.ask_security_warnings}>
              the security engineer has warnings
            </Check>
            <Check name="ask_preview_failed" checked={s.ask_preview_failed}>
              the preview doesn&apos;t build
            </Check>
            <Check name="ask_large_change" checked={s.ask_large_change}>
              it changes more than <Num name="large_files" value={s.large_files} suffix="files" />
            </Check>
            <Check name="ask_expensive" checked={s.ask_expensive}>
              it uses more than <Num name="max_tokens" value={s.max_tokens} suffix="model tokens" />
            </Check>
          </fieldset>

          <label className="flex flex-col gap-1 text-sm font-medium">
            Never let the team change these files
            <textarea
              name="never_touch"
              rows={3}
              defaultValue={s.never_touch.join("\n")}
              placeholder={"payments/*\n*.sql"}
              className="field font-mono text-xs"
            />
            <span className="text-xs font-normal text-zinc-500">
              One path or pattern per line. A release that touches one is stopped without asking.
            </span>
          </label>

          <Check name="go_live" checked={s.go_live}>
            After a release, <strong>publish it to the internet</strong> (when deploys are set up).
            Switch off to get the code only and publish yourself.
          </Check>

          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Saving…" : "Save"}
            </button>
            {view.scope === "project" && view.own && (
              <button
                type="button"
                disabled={resetting}
                className="btn-secondary"
                onClick={() => reset(() => resetAutonomyAction(projectId))}
              >
                Use my settings for everything
              </button>
            )}
            {state.saved && (
              <span className="text-sm text-emerald-700 dark:text-emerald-400">Saved.</span>
            )}
            {state.error && (
              <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                {state.error}
              </p>
            )}
          </div>
        </div>
      </form>

      <aside className="flex flex-col gap-4">
        <section className="card" aria-label="What this means">
          <div className="card-header">
            <h2 className="card-title">What this means</h2>
          </div>
          <ul className="flex flex-col gap-2 p-5 text-sm text-zinc-700 dark:text-zinc-300">
            {view.summary.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
        <section className="card" aria-label="Always yours">
          <div className="card-header">
            <h2 className="card-title">Always yours</h2>
          </div>
          <p className="p-5 text-sm text-zinc-600 dark:text-zinc-400">
            Whatever you choose, the team never handles your passwords, takes payments from your
            customers&apos; money, or deletes your data on its own. A release that fails its checks
            or has a blocking security problem never goes out.
          </p>
        </section>
      </aside>
    </div>
  );
}
