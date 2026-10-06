import { MessageThread } from "@/features/messages";
import Link from "next/link";
import { notFound } from "next/navigation";

import { AutoRefresh } from "@/shared/ui/AutoRefresh";

import { getProjectHealth } from "../api/getHealth";
import { getProject } from "../api/getProjects";
import { describeProject, isBusy, progress } from "../describe";
import { ActionButton } from "./ActionButton";
import { AddItemForm } from "./AddItemForm";
import { AutopilotForm } from "./AutopilotForm";
import { BacklogItemRow } from "./BacklogItemRow";
import { PriyaUpdate } from "./PriyaUpdate";
import { StatusBadge } from "./StatusBadge";

/** One project: Mira's plan and questions, the controls, and the backlog with each item's run. */
export async function ProjectPage({ projectId }: { projectId: string }) {
  const [project, health] = await Promise.all([getProject(projectId), getProjectHealth(projectId)]);
  if (!project) notFound();
  const look = describeProject(project.status);
  const { done, total } = progress(project.items);
  const planned = project.status !== "planning" && project.status !== "plan_ready";

  return (
    <div className="flex flex-col gap-6">
      <Link href="/admin/projects" className="text-sm text-zinc-500 hover:underline">
        ← All projects
      </Link>
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-semibold">{project.name}</h1>
          <StatusBadge label={look.label} tone={look.tone} />
          {planned && (
            <span className="text-sm text-zinc-500">
              {done} of {total} done
            </span>
          )}
        </div>
        <p className="whitespace-pre-line text-zinc-700 dark:text-zinc-300">{project.goal}</p>
        <p className="text-sm text-zinc-500">
          {project.repo ? (
            <>
              Repository:{" "}
              <a href={project.repo.url} className="hover:underline">
                {project.repo.url.replace("https://github.com/", "")}
              </a>
              {project.repo_owned
                ? " (created by MedhKarm; approved work merges on its own)"
                : " (yours; merge each pull request to continue)"}
            </>
          ) : (
            "New project: the first released item creates its private repository."
          )}
        </p>
        {project.error && (
          <p
            role="alert"
            className="rounded-md bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-300"
          >
            {project.error}
          </p>
        )}
      </header>

      {health && project.status !== "planning" && project.status !== "plan_ready" && (
        <PriyaUpdate health={health} />
      )}

      {project.status === "planning" && (
        <p className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm dark:border-sky-900 dark:bg-sky-950/40">
          Mira is turning the goal into a backlog. This page refreshes when she&apos;s done.
        </p>
      )}

      {project.status === "plan_ready" && (
        <section className="flex flex-col gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/40">
          <h2 className="font-semibold">
            Mira&apos;s plan: {project.items.filter((i) => i.status === "proposed").length} items
          </h2>
          {project.questions.length > 0 && (
            <div className="text-sm">
              <p className="font-medium">Her assumptions and questions:</p>
              <ul className="list-disc pl-5">
                {project.questions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-sm">
            Edit, move or delete items below, then approve. Nothing is built until you do.
          </p>
          <div className="flex gap-2">
            <ActionButton
              op="approve"
              projectId={project.id}
              label="Approve the plan"
              look="primary"
            />
            <ActionButton op="replan" projectId={project.id} label="Ask Mira again" />
          </div>
        </section>
      )}

      {planned && (
        <section className="flex flex-wrap items-center gap-x-6 gap-y-3 card p-5">
          <AutopilotForm
            projectId={project.id}
            autopilot={project.autopilot}
            dailyLimit={project.daily_limit}
          />
          <div className="ml-auto flex gap-2">
            {project.status !== "done" && (
              <ActionButton
                op="next"
                projectId={project.id}
                label="Start next item now"
                look="primary"
              />
            )}
            {project.status === "active" && (
              <ActionButton op="pause" projectId={project.id} label="Pause" />
            )}
            {project.status === "paused" && (
              <ActionButton op="resume" projectId={project.id} label="Resume" />
            )}
            <ActionButton op="replan" projectId={project.id} label="Re-plan the rest" />
          </div>
        </section>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Backlog</h2>
        {project.items.length === 0 ? (
          <p className="text-sm text-zinc-500">No items yet.</p>
        ) : (
          <ol className="divide-y divide-zinc-100 dark:divide-zinc-900">
            {project.items.map((item) => (
              <BacklogItemRow key={item.id} item={item} count={project.items.length} />
            ))}
          </ol>
        )}
        {project.status !== "planning" && <AddItemForm projectId={project.id} />}
      </section>
      <AutoRefresh active={isBusy(project)} seconds={5} />
      <MessageThread thread="project" threadId={project.id} />
    </div>
  );
}
