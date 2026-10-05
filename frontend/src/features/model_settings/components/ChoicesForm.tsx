"use client";

import { useActionState } from "react";

import { saveChoicesAction } from "../api/actions";
import type { FormState, ModelsView } from "../types";

const initial: FormState = { error: null };

/** Whose keys, the team's model, a model per agent, and the local connector's URL. */
export function ChoicesForm({ view }: { view: ModelsView }) {
  const [state, save, saving] = useActionState(saveChoicesAction, initial);
  const s = view.settings;
  const roles = Object.keys(view.roles);
  const suggestions = view.options.flatMap((o) => o.models);

  return (
    <form action={save} className="card flex flex-col">
      <div className="card-header">
        <h2 className="card-title">Who runs your team</h2>
      </div>
      <div className="flex flex-col gap-5 p-5">
        <fieldset className="grid gap-2 sm:grid-cols-2">
          <legend className="sr-only">Whose keys</legend>
          <ModeOption
            value="managed"
            checked={s.mode === "managed"}
            title="Managed"
            text="We run the models. Any key you add is used for its provider; the rest run on ours."
          />
          <ModeOption
            value="own"
            checked={s.mode === "own"}
            title="Bring your own"
            text="Only your keys and local models. A model without your key won't run."
          />
        </fieldset>

        <datalist id="model-suggestions">
          {suggestions.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>

        <label className="flex flex-col gap-1 text-sm font-medium">
          The team&apos;s model
          <input
            name="default_model"
            list="model-suggestions"
            defaultValue={s.default_model}
            placeholder="Our default (gpt-oss:20b on Ollama Cloud)"
            className="field"
          />
          <span className="text-xs font-normal text-zinc-500">
            Start with the provider, e.g. anthropic/claude-sonnet-5-5 or local/qwen3-coder:30b.
          </span>
        </label>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">A different model for one agent (optional)</p>
          <input type="hidden" name="roles" value={roles.join(",")} />
          <div className="grid gap-2 sm:grid-cols-2">
            {roles.map((role) => (
              <label key={role} className="flex flex-col gap-1 text-xs text-zinc-500">
                {view.roles[role]}
                <input
                  name={`role_${role}`}
                  list="model-suggestions"
                  defaultValue={s.role_models[role] ?? ""}
                  placeholder="The team's model"
                  className="field"
                />
              </label>
            ))}
          </div>
        </div>

        <label className="flex flex-col gap-1 text-sm font-medium">
          Local models: your connector&apos;s URL
          <input
            name="local_url"
            type="url"
            defaultValue={s.local_url}
            placeholder="https://your-tunnel.trycloudflare.com"
            className="field"
          />
          <span className="text-xs font-normal text-zinc-500">
            Run Ollama on your machine, then share it with{" "}
            <code className="rounded bg-zinc-100 px-1 dark:bg-zinc-800">
              cloudflared tunnel --url http://localhost:11434
            </code>{" "}
            and paste the address it prints. Choose models as local/&lt;name&gt;.
          </span>
        </label>

        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving…" : "Save"}
          </button>
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
  );
}

function ModeOption({
  value,
  checked,
  title,
  text,
}: {
  value: string;
  checked: boolean;
  title: string;
  text: string;
}) {
  return (
    <label className="flex cursor-pointer gap-3 rounded-xl border border-zinc-200 p-3 has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-50/60 dark:border-zinc-800 dark:has-[:checked]:bg-indigo-950/30">
      <input type="radio" name="mode" value={value} defaultChecked={checked} className="mt-1" />
      <span>
        <span className="block text-sm font-semibold">{title}</span>
        <span className="block text-xs text-zinc-500">{text}</span>
      </span>
    </label>
  );
}
