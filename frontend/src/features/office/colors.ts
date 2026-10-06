/** One colour per role, readable on light and dark floors. */
export const ROLE_COLORS: Record<string, string> = {
  pm: "#8b5cf6",
  cto: "#4f46e5",
  developer: "#0284c7",
  qa: "#d97706",
  security: "#e11d48",
  devops: "#0d9488",
  docs: "#db2777",
  design: "#0891b2",
  office: "#ca8a04",
};

export function roleColor(role: string): string {
  return ROLE_COLORS[role] ?? "#71717a";
}
