import { BlueprintPage } from "@/features/blueprints";

export default async function Page({ params }: PageProps<"/admin/blueprints/[blueprintId]">) {
  const { blueprintId } = await params;
  return <BlueprintPage blueprintId={blueprintId} />;
}
