/** The data layer: named collections of JSON records. Pages and API routes use only this, so
 * the same code runs on local storage, Supabase or any Postgres. */

export type Doc = { id: string; createdAt: string } & Record<string, unknown>;

export type Where = Record<string, string | number | boolean | null>;

export interface Collection<T extends Doc> {
  insert(data: Omit<T, "id" | "createdAt">): Promise<T>;
  get(id: string): Promise<T | null>;
  /** Records whose fields equal every value in `where`, newest first. */
  find(where?: Where, limit?: number): Promise<T[]>;
  findOne(where: Where): Promise<T | null>;
  update(id: string, changes: Partial<Omit<T, "id" | "createdAt">>): Promise<T | null>;
  remove(id: string): Promise<boolean>;
  count(where?: Where): Promise<number>;
}

export interface Store {
  collection<T extends Doc>(name: string): Collection<T>;
}
