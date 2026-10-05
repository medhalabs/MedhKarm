import { apiGet } from "@/shared/api/client";

import type { Member } from "../types";

type Template = { roles: { id: string; title: string; display_names: string[] }[] };

/** Everyone on the software team, one desk each: every name in the template, so a task for
 * any developer (Isha, Arjun, Ravi) shows at the right desk. */
export async function getTeam(): Promise<Member[]> {
  const template = await apiGet<Template>("/teams/templates/software");
  return template.roles.flatMap((role) =>
    role.display_names.map((name) => ({ role: role.id, title: role.title, name })),
  );
}
