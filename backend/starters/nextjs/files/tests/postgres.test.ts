import { readFileSync } from "node:fs";
import { Pool } from "pg";
import { expect, it } from "vitest";
import { PostgresStore } from "@/lib/db/postgres";

type Note = { id: string; createdAt: string; title: string; done: boolean; tag: string | null };

// Runs only with TEST_DATABASE_URL: a throwaway database (it creates the documents table).
it.runIf(process.env.TEST_DATABASE_URL)("stores records in Postgres", async () => {
  const url = process.env.TEST_DATABASE_URL!;
  const pool = new Pool({ connectionString: url });
  await pool.query(readFileSync("db/migrations/001_documents.sql", "utf8"));
  await pool.end();
  const notes = new PostgresStore(url).collection<Note>("notes");
  const a = await notes.insert({ title: "Buy milk", done: false, tag: null });
  await new Promise((r) => setTimeout(r, 5));
  await notes.insert({ title: "Call Ravi", done: true, tag: "work" });
  expect((await notes.find()).map((n) => n.title)).toEqual(["Call Ravi", "Buy milk"]);
  expect((await notes.find({ done: true })).map((n) => n.title)).toEqual(["Call Ravi"]);
  expect((await notes.find({ tag: null })).map((n) => n.title)).toEqual(["Buy milk"]);
  expect(await notes.find({}, 1)).toHaveLength(1);
  expect(await notes.count({ done: false })).toBe(1);
  expect((await notes.update(a.id, { done: true }))?.done).toBe(true);
  expect(await notes.findOne({ title: "Buy milk" })).toMatchObject({ done: true });
  expect(await notes.remove(a.id)).toBe(true);
  expect(await notes.get(a.id)).toBeNull();
});
