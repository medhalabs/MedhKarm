import type { BoardTask, Column } from "../types";

const COLUMNS: { id: Column; title: string }[] = [
  { id: "todo", title: "To do" },
  { id: "working", title: "Working" },
  { id: "review", title: "In review" },
  { id: "done", title: "Done" },
];

export function TaskBoard({ tasks }: { tasks: BoardTask[] }) {
  if (tasks.length === 0) return <p className="text-sm text-zinc-500">No tasks planned yet.</p>;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {COLUMNS.map((column) => (
        <section
          key={column.id}
          className="flex flex-col gap-2 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-900"
        >
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            {column.title} · {tasks.filter((t) => t.column === column.id).length}
          </h3>
          {tasks
            .filter((t) => t.column === column.id)
            .map((t) => (
              <article
                key={t.id}
                className="rounded-md border border-zinc-200 bg-white p-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
              >
                <p className="leading-snug">{t.title}</p>
                <p className="mt-1 text-xs text-zinc-500">
                  {t.owner}
                  {t.rounds > 0 && ` · sent back ${t.rounds}×`}
                </p>
              </article>
            ))}
        </section>
      ))}
    </div>
  );
}
