"use client";

import { useActionState } from "react";

import { addKeyAction, checkKeyAction, removeKeyAction } from "../api/actions";
import { type FormState, type KeyCheck, PROVIDER_NAMES, type Provider } from "../types";

const initial: FormState = { error: null };

/** One provider: its saved key (check, remove) or a box to add one. */
export function KeyRow({
  provider,
  hint,
  serverKey,
}: {
  provider: Provider;
  hint: string | null;
  serverKey: boolean;
}) {
  const [added, add, adding] = useActionState(addKeyAction, initial);
  const [checked, check, checking] = useActionState(checkKeyAction, initial);
  const [removed, remove, removing] = useActionState(removeKeyAction, initial);
  const result = checked.check ?? added.check;
  const error = added.error ?? checked.error ?? removed.error;

  return (
    <li className="flex flex-col gap-2 px-5 py-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">{PROVIDER_NAMES[provider]}</span>
        <span className="text-xs text-zinc-500">
          {hint
            ? `Your key ${hint}`
            : serverKey
              ? "On our key"
              : provider === "local"
                ? "Optional token"
                : "No key"}
        </span>
      </div>
      {hint ? (
        <div className="flex gap-2">
          <form action={check}>
            <input type="hidden" name="provider" value={provider} />
            <button type="submit" disabled={checking} className="btn-secondary">
              {checking ? "Checking…" : "Check"}
            </button>
          </form>
          <form action={remove}>
            <input type="hidden" name="provider" value={provider} />
            <button type="submit" disabled={removing} className="btn-secondary">
              {removing ? "Removing…" : "Remove"}
            </button>
          </form>
        </div>
      ) : (
        <form action={add} className="flex gap-2">
          <input type="hidden" name="provider" value={provider} />
          <input
            name="key"
            type="password"
            autoComplete="off"
            placeholder={provider === "local" ? "Token, if your connector needs one" : "API key"}
            aria-label={`${PROVIDER_NAMES[provider]} key`}
            className="field min-w-0 flex-1 py-1.5"
          />
          <button type="submit" disabled={adding} className="btn-secondary">
            {adding ? "Adding…" : "Add"}
          </button>
        </form>
      )}
      {result && <CheckResult check={result} />}
      {error && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </li>
  );
}

function CheckResult({ check }: { check: KeyCheck }) {
  return check.ok ? (
    <p className="text-xs text-emerald-700 dark:text-emerald-400">Works with {check.model}.</p>
  ) : (
    <p className="text-xs text-red-600 dark:text-red-400">
      Didn&apos;t work with {check.model}: {check.error}
    </p>
  );
}
