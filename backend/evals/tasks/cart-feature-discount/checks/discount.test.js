import { test } from "node:test";
import assert from "node:assert/strict";
import { Cart } from "../cart.js";

function cart(amount) {
  const c = new Cart();
  c.add("item", amount);
  return c;
}

test("no code: total equals subtotal", () => {
  assert.equal(cart(200).total(), 200);
});

test("SAVE10 is ten percent off, case-insensitive", () => {
  const c = cart(199.99);
  c.applyCode("save10");
  assert.equal(c.total(), 179.99);
});

test("FLAT50 never goes below zero", () => {
  const c = cart(30);
  c.applyCode("FLAT50");
  assert.equal(c.total(), 0);
  const d = cart(80);
  d.applyCode("FLAT50");
  assert.equal(d.total(), 30);
});

test("new code replaces the old one", () => {
  const c = cart(1000);
  c.applyCode("SAVE10");
  c.applyCode("FLAT50");
  assert.equal(c.total(), 950);
});

test("unknown code throws and keeps the current code", () => {
  const c = cart(1000);
  c.applyCode("SAVE10");
  assert.throws(() => c.applyCode("FREE100"));
  assert.equal(c.total(), 900);
});
