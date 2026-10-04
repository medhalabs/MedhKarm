import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { Collection, Doc, Store, Where } from "./types";

type Data = Record<string, Doc[]>;

function matches(doc: Doc, where: Where): boolean {
  return Object.entries(where).every(([key, value]) => doc[key] === value);
}

/** Local mode: records in memory, saved to a JSON file when `file` is given (development). */
export class MemoryStore implements Store {
  private data: Data;

  constructor(private readonly file?: string) {
    this.data = file && existsSync(file) ? (JSON.parse(readFileSync(file, "utf8")) as Data) : {};
  }

  collection<T extends Doc>(name: string): Collection<T> {
    const rows = (): T[] => (this.data[name] ??= []) as T[];
    const save = () => {
      if (!this.file) return;
      mkdirSync(path.dirname(this.file), { recursive: true });
      writeFileSync(this.file, JSON.stringify(this.data, null, 2));
    };
    const newestFirst = (list: T[]) =>
      [...list].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    return {
      async insert(data) {
        const doc = { ...data, id: randomUUID(), createdAt: new Date().toISOString() } as T;
        rows().push(doc);
        save();
        return doc;
      },
      async get(id) {
        return rows().find((d) => d.id === id) ?? null;
      },
      async find(where = {}, limit = 100) {
        return newestFirst(rows().filter((d) => matches(d, where))).slice(0, limit);
      },
      async findOne(where) {
        return newestFirst(rows().filter((d) => matches(d, where)))[0] ?? null;
      },
      async update(id, changes) {
        const doc = rows().find((d) => d.id === id);
        if (!doc) return null;
        Object.assign(doc, changes, { id: doc.id, createdAt: doc.createdAt });
        save();
        return doc;
      },
      async remove(id) {
        const list = rows();
        const index = list.findIndex((d) => d.id === id);
        if (index < 0) return false;
        list.splice(index, 1);
        save();
        return true;
      },
      async count(where = {}) {
        return rows().filter((d) => matches(d, where)).length;
      },
    };
  }
}
