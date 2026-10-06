import { AutonomyPage } from "@/features/autonomy";

export default async function Page({ searchParams }: PageProps<"/admin/autonomy">) {
  const { project } = await searchParams;
  return <AutonomyPage projectId={typeof project === "string" ? project : undefined} />;
}
