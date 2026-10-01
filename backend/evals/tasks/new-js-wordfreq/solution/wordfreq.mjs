export function topWords(text, n) {
  if (!Number.isInteger(n) || n <= 0) throw new Error("n must be a positive integer");
  const counts = new Map();
  for (const word of text.toLowerCase().match(/[a-z']+/g) ?? []) {
    counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))
    .slice(0, n);
}
