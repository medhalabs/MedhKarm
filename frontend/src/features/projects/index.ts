// Public exports of the projects feature. Import from "@/features/projects", never from deeper paths.
export { listProjects } from "./api/getProjects";
export { ProjectPage } from "./components/ProjectPage";
export { ProjectsOverview } from "./components/ProjectsOverview";
export type { BacklogItem, Project, ProjectDetail } from "./types";
