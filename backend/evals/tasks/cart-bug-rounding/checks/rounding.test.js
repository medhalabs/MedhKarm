import { test } from "node:test";
import assert from "node:assert/strict";
import { Cart } from "../cart.js";

test("classic float case", () => {
  const cart = new Cart();
  cart.add("a", 0.1);
  cart.add("b", 0.2);
  assert.equal(cart.subtotal(), 0.3);
});

test("quantities", () => {
  const cart = new Cart();
  cart.add("a", 19.99, 3);
  assert.equal(cart.subtotal(), 59.97);
});

test("empty cart", () => {
  assert.equal(new Cart().subtotal(), 0);
});
