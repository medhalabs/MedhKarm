import type { DayCount } from "@/lib/admin/stats";

/** A small bar chart in plain HTML: one bar per day, height relative to the busiest day. */
export default function BarChart({ data, label }: { data: DayCount[]; label: string }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <figure style={{ margin: 0 }}>
      <figcaption className="muted">{label}</figcaption>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 120 }} role="img" aria-label={label}>
        {data.map((d) => (
          <div
            key={d.day}
            title={`${d.day}: ${d.count}`}
            style={{
              flex: 1,
              height: `${(d.count / max) * 100}%`,
              minHeight: 2,
              background: "var(--accent)",
              borderRadius: 3,
            }}
          />
        ))}
      </div>
    </figure>
  );
}
