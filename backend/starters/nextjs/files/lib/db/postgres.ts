import { randomUUID } from "node:crypto";
import { Pool } from "pg";
import type { Collection, Doc, Store, Where } from "./types";

const PRIVATE_IP = /^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

/** Encrypted, with the certificate checked, for databases across the internet (Supabase,
 * managed Postgres). Not for this machine, private networks or docker-compose services
 * (hosts without a dot). `?sslmode=...` in the URL decides when it's given. */
export function needsTls(connectionString: string): boolean {
  if (/[?&]sslmode=/.test(connectionString)) return false; // pg reads it from the URL
  const host = new URL(connectionString).hostname;
  return host.includes(".") && !PRIVATE_IP.test(host);
}

/** Postgres mode (Supabase or any Postgres): every collection lives in one `documents` table
 * (db/migrations/001_documents.sql) as JSON. Add real tables with migrations when a
 * collection needs joins or heavy queries. */
export class PostgresStore implements Store {
  private readonly pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString, ssl: needsTls(connectionString) || undefined, max: 5 });
  }

  collection<T extends Doc>(name: string): Collection<T> {
    const pool = this.pool;
    const toDoc = (row: { id: string; created_at: Date; data: Record<string, unknown> }) =>
      ({ ...row.data, id: row.id, createdAt: row.created_at.toISOString() }) as T;
    // Only placeholders go into the SQL text; every value is a parameter.
    const filter = (where: Where, offset: number) => {
      const keys = Object.keys(where);
      const sql = keys
        .map((_, i) => " and data->>$" + (offset + 2 * i) + " is not distinct from $" + (offset + 2 * i + 1))
        .join("");
      const params = keys.flatMap((key) => [key, where[key] === null ? null : String(where[key])]);
      return { sql, params };
    };
    return {
      async insert(data) {
        const id = randomUUID();
        const { rows } = await pool.query(
          "insert into documents (id, collection, data) values ($1, $2, $3) returning *",
          [id, name, data],
        );
        return toDoc(rows[0]);
      },
      async get(id) {
        const { rows } = await pool.query(
          "select * from documents where collection = $1 and id = $2",
          [name, id],
        );
        return rows[0] ? toDoc(rows[0]) : null;
      },
      async find(where = {}, limit = 100) {
        const f = filter(where, 2);
        const { rows } = await pool.query(
          "select * from documents where collection = $1" + f.sql +
            " order by created_at desc limit $" + (f.params.length + 2),
          [name, ...f.params, Math.max(1, Math.floor(limit))],
        );
        return rows.map(toDoc);
      },
      async findOne(where) {
        return (await this.find(where, 1))[0] ?? null;
      },
      async update(id, changes) {
        const { rows } = await pool.query(
          "update documents set data = data || $3 where collection = $1 and id = $2 returning *",
          [name, id, changes],
        );
        return rows[0] ? toDoc(rows[0]) : null;
      },
      async remove(id) {
        const { rowCount } = await pool.query(
          "delete from documents where collection = $1 and id = $2",
          [name, id],
        );
        return (rowCount ?? 0) > 0;
      },
      async count(where = {}) {
        const f = filter(where, 2);
        const { rows } = await pool.query(
          "select count(*)::int as n from documents where collection = $1" + f.sql,
          [name, ...f.params],
        );
        return rows[0].n as number;
      },
    };
  }
}
