import Link from "next/link";

import { AutoRefresh } from "@/shared/ui/AutoRefresh";
import { PageHeader } from "@/shared/ui/PageHeader";

import { getBlueprint } from "../api/getBlueprint";
import { isBusy } from "../types";
import { BlueprintView } from "./BlueprintView";

const STATUS: Record<string, string> = {
  writing: "Lekha is writing your plan",
  revising: "Lekha is updating your plan",
  ready: "Ready for you to read",
  approved: "Approved: the team is building",
  failed: "Lekha couldn't finish",
};

/** Lekha's plan for one project: read it, comment, then approve to start the build. */
export async function BlueprintPage({ blueprintId, doc }: { blueprintId: string; doc?: string }) {
  const blueprint = await getBlueprint(blueprintId);
  return (
    <div className="flex flex-col gap-6">
      <AutoRefresh active={isBusy(blueprint.status)} seconds={4} />
      <PageHeader
        title={blueprint.title}
        description="The plan, written before any code: read it, ask for changes, then approve."
      >
        <div className="flex items-center gap-3 text-sm">
          <span className="rounded-full bg-zinc-100 px-3 py-1 font-medium dark:bg-zinc-800">
            {STATUS[blueprint.status]}
          </span>
          {blueprint.run_id && (
            <Link href={`/admin/runs/${blueprint.run_id}`} className="btn-secondary">
              See the build →
            </Link>
          )}
        </div>
      </PageHeader>
      <BlueprintView blueprint={blueprint} selected={doc} />
    </div>
  );
}
