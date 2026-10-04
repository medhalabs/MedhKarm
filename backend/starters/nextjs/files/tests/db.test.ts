import { describe, expect, it } from "vitest";
import { MemoryStore } from "@/lib/db/memory";

type Note = { id: string; createdAt: string; title: string; done: boolean };

describe("local store", () => {
  it("inserts, finds, updates and removes records", async () => {
    const notes = new MemoryStore().collection<Note>("notes");
    const first = await notes.insert({ title: "Buy milk", done: false });
    await notes.insert({ title: "Call Ravi", done: true });

    expect(await notes.get(first.id)).toMatchObject({ title: "Buy milk" });
    expect((await notes.find({ done: true })).map((n) => n.title)).toEqual(["Call Ravi"]);
    expect(await notes.count()).toBe(2);

    await notes.update(first.id, { done: true });
    expect(await notes.count({ done: true })).toBe(2);

    expect(await notes.remove(first.id)).toBe(true);
    expect(await notes.get(first.id)).toBeNull();
  });
});

describe("database connections", () => {
  it("encrypts connections across the internet, not on private networks", async () => {
    const { needsTls } = await import("@/lib/db/postgres");
    expect(needsTls("postgres://u:p@db.abcd.supabase.co:5432/postgres")).toBe(true);
    expect(needsTls("postgres://u:p@db:5432/app")).toBe(false);
    expect(needsTls("postgres://u:p@localhost:5432/app")).toBe(false);
    expect(needsTls("postgres://u:p@10.0.0.5:5432/app")).toBe(false);
    expect(needsTls("postgres://u:p@db.example.com/app?sslmode=require")).toBe(false);
  });
});
