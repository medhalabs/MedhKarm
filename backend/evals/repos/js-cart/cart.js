// Shopping cart for an online store. Prices are in rupees.

export class Cart {
  constructor() {
    this.lines = new Map();
  }

  add(sku, price, qty = 1) {
    if (typeof price !== "number" || price < 0) {
      throw new Error("Price must be a non-negative number");
    }
    if (!Number.isInteger(qty) || qty <= 0) {
      throw new Error("Quantity must be a positive integer");
    }
    const line = this.lines.get(sku);
    if (line) {
      line.qty += qty;
    } else {
      this.lines.set(sku, { sku, price, qty });
    }
  }

  remove(sku) {
    this.lines.delete(sku);
  }

  itemCount() {
    let count = 0;
    for (const line of this.lines.values()) count += line.qty;
    return count;
  }

  subtotal() {
    let total = 0;
    for (const line of this.lines.values()) total += line.price * line.qty;
    return total;
  }
}
