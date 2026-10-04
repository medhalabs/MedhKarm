import { notFound } from "next/navigation";
import BarChart from "@/components/BarChart";
import { ADMIN_COLLECTIONS, isAdmin, perDay, preview } from "@/lib/admin/stats";
import { requireUser } from "@/lib/auth";
import { getStore } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const user = await requireUser();
  if (!isAdmin(user.email)) notFound();
  const store = getStore();
  const sections = await Promise.all(
    ADMIN_COLLECTIONS.map(async (name) => {
      const collection = store.collection(name);
      const [total, latest, recent] = await Promise.all([
        collection.count(),
        collection.find({}, 5),
        collection.find({}, 1000),
      ]);
      return { name, total, latest, days: perDay(recent) };
    }),
  );
  return (
    <main>
      <h1>Admin</h1>
      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
        {sections.map((s) => (
          <div key={s.name} className="card">
            <div className="muted">{s.name}</div>
            <div style={{ fontSize: 32, fontWeight: 600 }}>{s.total}</div>
            <BarChart data={s.days} label={`New ${s.name}, last 14 days`} />
          </div>
        ))}
      </div>
      {sections.map((s) => (
        <section key={s.name}>
          <h2>Latest {s.name}</h2>
          {s.latest.length === 0 ? (
            <p className="muted">Nothing yet.</p>
          ) : (
            <table>
              <tbody>
                {s.latest.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.createdAt.slice(0, 16).replace("T", " ")}</td>
                    <td>{preview(doc)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ))}
    </main>
  );
}
