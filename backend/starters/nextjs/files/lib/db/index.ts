import path from "node:path";
import { dataMode, env, isProduction } from "../config";
import { MemoryStore } from "./memory";
import { PostgresStore } from "./postgres";
import type { Store } from "./types";

export type { Collection, Doc, Store, Where } from "./types";

let store: Store | undefined;

/** The app's data store: Postgres when DATABASE_URL is set, otherwise local. In local mode
 * development keeps data in .data/store.json; tests and production previews keep it in memory. */
export function getStore(): Store {
  if (!store) {
    if (dataMode() === "postgres") {
      store = new PostgresStore(env("DATABASE_URL")!);
    } else {
      const keep = !isProduction && process.env.VITEST === undefined;
      store = new MemoryStore(keep ? path.join(process.cwd(), ".data", "store.json") : undefined);
    }
  }
  return store;
}

/** Tests: start from an empty store. */
export function resetStore(next?: Store): void {
  store = next;
}
