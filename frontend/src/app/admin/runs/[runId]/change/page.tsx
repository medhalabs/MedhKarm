import { ChangePage } from "@/features/runs";

export default async function Page({ params }: PageProps<"/admin/runs/[runId]/change">) {
  const { runId } = await params;
  return <ChangePage runId={runId} />;
}
