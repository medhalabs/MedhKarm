// Browser-safe exports of the events feature, for client components. index.ts also exports
// server-only code (it reads the session cookie), which can't be bundled for the browser.
export { eventStreamUrl } from "./api/streamUrl";
export type { ActivityEvent, EventType } from "./types";
