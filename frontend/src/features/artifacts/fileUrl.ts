/** Where the browser plays a run's file: the Next.js route that adds the founder's session. */
export function fileUrl(runId: string, artifactId: number): string {
  return `/api/runs/${encodeURIComponent(runId)}/artifacts/${artifactId}`;
}
