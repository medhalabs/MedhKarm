import { test } from "node:test";
import assert from "node:assert/strict";
import { Cart } from "../cart.js";

test("default category is standard 18%", () => {
  const c = new Cart();
  c.add("phone", 1000);
  assert.equal(c.tax(), 180);
  assert.equal(c.totalWithTax(), 1180);
});

test("mixed categories", () => {
  const c = new Cart();
  c.add("phone", 1000, 1, "standard");
  c.add("rice", 50, 2, "reduced");
  c.add("milk", 30, 1, "exempt");
  assert.equal(c.tax(), 185);
  assert.equal(c.totalWithTax(), 1315);
});

test("rounding", () => {
  const c = new Cart();
  c.add("pen", 9.99, 1, "reduced");
  assert.equal(c.tax(), 0.5);
});

test("unknown category throws", () => {
  assert.throws(() => new Cart().add("x", 10, 1, "luxury"));
});

test("existing calls still work", () => {
  const c = new Cart();
  c.add("tea", 120, 2);
  assert.equal(c.subtotal(), 240);
  assert.equal(c.itemCount(), 2);
});
