import { OfficePage } from "@/features/office";

export default async function Page({ params }: PageProps<"/admin/runs/[runId]/office">) {
  const { runId } = await params;
  return <OfficePage runId={runId} />;
}
