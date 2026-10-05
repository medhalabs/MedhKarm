import { PageHeader } from "@/shared/ui/PageHeader";

import { getModelSettings } from "../api/getModelSettings";
import { ChoicesForm } from "./ChoicesForm";
import { KeyRow } from "./KeyRow";

/** Whose keys run the team, which models each agent uses, and the founder's own keys. */
export async function ModelsPage() {
  const view = await getModelSettings();
  const saved = new Map(view.settings.keys.map((k) => [k.provider, k.hint]));
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Models"
        description="Run your team on our models, or bring your own API keys and local models and pay their bills yourself."
      />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <ChoicesForm view={view} />
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Your keys</h2>
          </div>
          <p className="px-5 pt-4 text-xs text-zinc-500">
            Keys are stored encrypted and never shown again: only their last four characters. Each
            one is checked with a tiny call when you add it.
          </p>
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {view.options.map((o) => (
              <KeyRow
                key={o.provider}
                provider={o.provider}
                hint={saved.get(o.provider) ?? null}
                serverKey={o.server_key}
              />
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
