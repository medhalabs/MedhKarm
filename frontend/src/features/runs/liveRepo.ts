import type { Run } from "./types";

/** The GitHub repository a released run's work lives in: the founder's own repository, or the
 * one we created for a new project. null when it never reached GitHub (no change can build on
 * it yet). */
export function liveRepoUrl(run: Run): string | null {
  if (run.status !== "released") return null;
  return run.repo?.url ?? run.delivery?.repo_url ?? null;
}

/** The last release is still an open pull request: a change would start without it. */
export function hasOpenPullRequest(run: Run): boolean {
  return run.delivery?.status === "opened";
}
