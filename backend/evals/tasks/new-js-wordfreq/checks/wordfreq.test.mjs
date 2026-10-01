import { test } from "node:test";
import assert from "node:assert/strict";
import { topWords } from "../wordfreq.mjs";

test("example", () => {
  assert.deepEqual(topWords("the cat and the hat", 2), [["the", 2], ["and", 1]]);
});

test("case-insensitive with apostrophes and punctuation", () => {
  assert.deepEqual(topWords("Don't stop. DON'T! Stop, don't.", 2), [["don't", 3], ["stop", 2]]);
});

test("fewer words than n", () => {
  assert.deepEqual(topWords("one two", 5), [["one", 1], ["two", 1]]);
  assert.deepEqual(topWords("", 3), []);
});

test("invalid n throws", () => {
  assert.throws(() => topWords("a b", 0));
  assert.throws(() => topWords("a b", 1.5));
});
