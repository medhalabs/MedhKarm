import { MODULES } from "../types";

const field = "field";

const SUGGESTIONS: Record<string, { label: string; options: string[]; hint: string }> = {
  frontend: { label: "Frontend", options: ["nextjs", "none", "vue", "angular"], hint: "nextjs" },
  api: { label: "API", options: ["nextjs", "python", "java", "node", "go"], hint: "nextjs" },
  database: {
    label: "Database",
    options: ["supabase", "postgres", "mysql", "mongodb", "sqlite"],
    hint: "supabase",
  },
  hosting: {
    label: "Hosting",
    options: ["vercel", "docker", "digitalocean", "aws", "gcp"],
    hint: "vercel",
  },
  payments: {
    label: "Payments",
    options: ["razorpay", "stripe", "cashfree", "paypal", "none"],
    hint: "razorpay",
  },
};

/** Optional stack choices for a new project. Empty = the team picks (from the request, then
 * Next.js, Supabase, Vercel, Razorpay). Any name works: unknown ones are built from the notes. */
export function StackFields() {
  return (
    <details className="rounded-md border border-zinc-200 p-3 text-sm dark:border-zinc-800">
      <summary className="cursor-pointer font-medium">
        Stack for a new project (optional: leave empty and the team picks)
      </summary>
      <div className="mt-3 flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {Object.entries(SUGGESTIONS).map(([name, s]) => (
            <label key={name} className="flex flex-col gap-1 font-medium">
              {s.label}
              <input
                name={`stack_${name}`}
                list={`stack-${name}-options`}
                maxLength={40}
                placeholder="auto"
                title={`Empty: the team picks (usually ${s.hint})`}
                className={`${field} text-sm`}
              />
              <datalist id={`stack-${name}-options`}>
                {s.options.map((option) => (
                  <option key={option} value={option} />
                ))}
              </datalist>
            </label>
          ))}
        </div>
        <fieldset className="flex flex-wrap items-center gap-4">
          <legend className="mb-1 font-medium">
            Ready-made modules (none ticked: picked from the request)
          </legend>
          {MODULES.map((m) => (
            <label key={m.name} className="flex items-center gap-2">
              <input type="checkbox" name={`module_${m.name}`} />
              {m.title}
            </label>
          ))}
          <label className="ml-auto flex items-center gap-2">
            Starter
            <select name="stack_starter" defaultValue="auto" className={`${field} py-1`}>
              <option value="auto">when it&apos;s an app</option>
              <option value="yes">always</option>
              <option value="no">never (start empty)</option>
            </select>
          </label>
        </fieldset>
        <label className="flex flex-col gap-1 font-medium">
          Notes about the stack (links to docs for anything new, e.g. a payment provider)
          <textarea name="stack_notes" rows={2} maxLength={3000} className={field} />
        </label>
      </div>
    </details>
  );
}
