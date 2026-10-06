import type { Brief } from "./types";

/** The agreed brief in the shape of `POST /runs` (also the brief of a blueprint). */
export function briefBody(brief: Brief): Record<string, unknown> {
  return {
    request: brief.request,
    ...(brief.test_command ? { test_command: brief.test_command } : {}),
    ...(brief.repo_url
      ? { repo: { url: brief.repo_url, branch: brief.branch } }
      : {
          create_repo: brief.create_repo,
          ...(brief.new_repo_name ? { new_repo_name: brief.new_repo_name } : {}),
          stack: brief.stack,
        }),
  };
}
