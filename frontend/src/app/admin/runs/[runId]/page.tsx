import { RunPage } from "@/features/runs";

export default async function AdminRunPage({ params }: PageProps<"/admin/runs/[runId]">) {
  const { runId } = await params;
  return <RunPage runId={runId} />;
}
