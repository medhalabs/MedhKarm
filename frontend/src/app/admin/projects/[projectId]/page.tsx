import { ProjectPage } from "@/features/projects";

export default async function AdminProjectPage({
  params,
}: PageProps<"/admin/projects/[projectId]">) {
  const { projectId } = await params;
  return <ProjectPage projectId={projectId} />;
}
