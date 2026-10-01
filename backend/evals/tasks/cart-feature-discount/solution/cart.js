// Shopping cart for an online store. Prices are in rupees.

export class Cart {
  constructor() {
    this.lines = new Map();
    this.code = null;
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

  applyCode(code) {
    const normalised = String(code).toUpperCase();
    if (!["SAVE10", "FLAT50"].includes(normalised)) {
      throw new Error(`Unknown code: ${code}`);
    }
    this.code = normalised;
  }

  total() {
    const subtotal = this.subtotal();
    let discount = 0;
    if (this.code === "SAVE10") discount = subtotal * 0.1;
    if (this.code === "FLAT50") discount = 50;
    return Math.round(Math.max(0, subtotal - discount) * 100) / 100;
  }

  subtotal() {
    let total = 0;
    for (const line of this.lines.values()) total += line.price * line.qty;
    return total;
  }
}
