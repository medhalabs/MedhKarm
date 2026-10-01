// Shopping cart for an online store. Prices are in rupees.

const GST = { standard: 0.18, reduced: 0.05, exempt: 0 };

export class Cart {
  constructor() {
    this.lines = new Map();
  }

  add(sku, price, qty = 1, category = "standard") {
    if (!(category in GST)) {
      throw new Error(`Unknown category: ${category}`);
    }
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
      this.lines.set(sku, { sku, price, qty, category });
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

  tax() {
    let tax = 0;
    for (const line of this.lines.values()) tax += line.price * line.qty * GST[line.category];
    return Math.round(tax * 100) / 100;
  }

  totalWithTax() {
    return Math.round((this.subtotal() + this.tax()) * 100) / 100;
  }

  subtotal() {
    let total = 0;
    for (const line of this.lines.values()) total += line.price * line.qty;
    return total;
  }
}
