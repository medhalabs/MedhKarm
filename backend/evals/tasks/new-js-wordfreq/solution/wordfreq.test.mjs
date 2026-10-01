import { test } from "node:test";
import assert from "node:assert/strict";
import { topWords } from "./wordfreq.mjs";

test("basic", () => {
  assert.deepEqual(topWords("a a b", 1), [["a", 2]]);
});
