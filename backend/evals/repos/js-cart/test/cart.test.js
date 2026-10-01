import { test } from "node:test";
import assert from "node:assert/strict";
import { Cart } from "../cart.js";

test("add merges lines of the same sku", () => {
  const cart = new Cart();
  cart.add("tea", 120, 1);
  cart.add("tea", 120, 2);
  assert.equal(cart.itemCount(), 3);
});

test("subtotal sums price times quantity", () => {
  const cart = new Cart();
  cart.add("tea", 120, 2);
  cart.add("biscuit", 30);
  assert.equal(cart.subtotal(), 270);
});

test("remove deletes a line", () => {
  const cart = new Cart();
  cart.add("tea", 120);
  cart.remove("tea");
  assert.equal(cart.itemCount(), 0);
});

test("rejects bad input", () => {
  const cart = new Cart();
  assert.throws(() => cart.add("tea", -1));
  assert.throws(() => cart.add("tea", 10, 0));
});
