import Link from "next/link";

import { listProjects } from "@/features/projects";
import { PageHeader } from "@/shared/ui/PageHeader";

import { getAutonomy } from "../api/getAutonomy";
import { AutonomyForm } from "./AutonomyForm";

/** How much the team does on its own: for everything, or for one project. */
export async function AutonomyPage({ projectId }: { projectId?: string }) {
  const [view, projects] = await Promise.all([
    getAutonomy(projectId),
    listProjects().catch(() => []),
  ]);
  const scopes = [
    { id: "", name: "Everything" },
    ...projects.map((p) => ({ id: p.id, name: p.name })),
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Autonomy"
        description="Decide what the team does on its own, what it asks you first, and what it must never do."
      />
      <nav className="flex flex-wrap gap-2" aria-label="Scope">
        {scopes.map((s) => {
          const active = (projectId ?? "") === s.id;
          return (
            <Link
              key={s.id || "all"}
              href={
                s.id ? `/admin/autonomy?project=${encodeURIComponent(s.id)}` : "/admin/autonomy"
              }
              className={`rounded-full px-3 py-1 text-sm ${
                active
                  ? "bg-indigo-600 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
              }`}
            >
              {s.name}
            </Link>
          );
        })}
      </nav>
      <AutonomyForm key={`${projectId ?? "all"}-${view.own}`} view={view} />
    </div>
  );
}
