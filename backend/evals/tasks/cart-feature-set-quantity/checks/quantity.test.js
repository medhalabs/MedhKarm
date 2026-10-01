import { test } from "node:test";
import assert from "node:assert/strict";
import { Cart } from "../cart.js";

test("sets quantity", () => {
  const c = new Cart();
  c.add("tea", 120, 1);
  c.setQuantity("tea", 4);
  assert.equal(c.itemCount(), 4);
  assert.equal(c.subtotal(), 480);
});

test("zero removes the line", () => {
  const c = new Cart();
  c.add("tea", 120, 2);
  c.setQuantity("tea", 0);
  assert.equal(c.itemCount(), 0);
  assert.equal(c.lines.has("tea"), false);
});

test("invalid quantities throw", () => {
  const c = new Cart();
  c.add("tea", 120, 2);
  assert.throws(() => c.setQuantity("tea", -1));
  assert.throws(() => c.setQuantity("tea", 1.5));
  assert.equal(c.itemCount(), 2);
});

test("unknown sku throws", () => {
  assert.throws(() => new Cart().setQuantity("nope", 1));
});
