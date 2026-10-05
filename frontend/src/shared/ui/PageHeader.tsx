/** A page's title, a line about it, and optional actions on the right. */
export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {title}
        </h1>
        {description && <p className="mt-1 text-sm text-zinc-500">{description}</p>}
      </div>
      {children}
    </div>
  );
}

/** A small number with a label, e.g. "3 · Waiting for you". */
export function Stat({
  value,
  label,
  tone = "zinc",
}: {
  value: number;
  label: string;
  tone?: "zinc" | "sky" | "amber" | "emerald";
}) {
  const dot = {
    zinc: "bg-zinc-400",
    sky: "bg-sky-500",
    amber: "bg-amber-500",
    emerald: "bg-emerald-500",
  }[tone];
  return (
    <div className="card flex min-w-32 flex-col gap-1 px-4 py-3">
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      <span className="flex items-center gap-1.5 text-xs text-zinc-500">
        <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
        {label}
      </span>
    </div>
  );
}
