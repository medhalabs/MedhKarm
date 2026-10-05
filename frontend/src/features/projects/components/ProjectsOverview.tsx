import Link from "next/link";

import { timeAgo } from "@/shared/lib/format";
import { AutoRefresh } from "@/shared/ui/AutoRefresh";
import { PageHeader } from "@/shared/ui/PageHeader";

import { listProjects } from "../api/getProjects";
import { describeProject } from "../describe";
import { ProjectIntake } from "./ProjectIntake";
import { StatusBadge } from "./StatusBadge";

/** Every project, and a form to start one (Mira plans its backlog). */
export async function ProjectsOverview() {
  const projects = await listProjects().catch(() => null);
  const planning = projects?.some((p) => p.status === "planning") ?? false;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Projects"
        description="Bigger goals, planned into a backlog by Mira and built item by item."
      />
      <ProjectIntake />
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-zinc-500">All projects</h2>
        {projects === null && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            Couldn&apos;t reach the backend.
          </p>
        )}
        {projects?.length === 0 && (
          <p className="card p-8 text-center text-sm text-zinc-500">
            No projects yet. Tell Mira about one above and she&apos;ll plan its backlog.
          </p>
        )}
        <ul className="grid gap-3 md:grid-cols-2">
          {projects?.map((project) => {
            const look = describeProject(project.status);
            return (
              <li key={project.id}>
                <Link
                  href={`/admin/projects/${project.id}`}
                  className="card flex h-full flex-col gap-2 p-5 transition hover:border-indigo-300 hover:shadow-md dark:hover:border-indigo-800 dark:hover:bg-zinc-900/50"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold">{project.name}</span>
                    <StatusBadge label={look.label} tone={look.tone} />
                  </div>
                  <p className="line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
                    {project.goal}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {project.autopilot ? `Autopilot, ${project.daily_limit} a day` : "Manual"} ·
                    updated {timeAgo(project.updated_at)}
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      </section>
      <AutoRefresh active={planning} />
    </div>
  );
}
