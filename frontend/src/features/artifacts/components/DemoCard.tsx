import { fileUrl } from "../fileUrl";
import { listArtifacts } from "../api/listArtifacts";

/** The demo: a short video of QA using the app, recorded from the browser test that passed.
 * Nothing is shown when no video was recorded. */
export async function DemoCard({ runId, compact = false }: { runId: string; compact?: boolean }) {
  const [demo] = await listArtifacts(runId, "demo").catch(() => []);
  if (!demo) return null;
  return (
    <section id="demo" className="card scroll-mt-6" aria-label="Demo">
      <div className="card-header">
        <h2 className="card-title">Demo</h2>
        <span className="text-xs text-zinc-500">
          Tara using the app, recorded from her browser test
        </span>
      </div>
      <div className="p-4">
        <video
          controls
          preload="metadata"
          playsInline
          className={`w-full rounded-lg bg-zinc-950 ${compact ? "max-h-64" : "max-h-[28rem]"}`}
          src={fileUrl(runId, demo.id)}
        >
          Your browser can&apos;t play this video.
        </video>
      </div>
    </section>
  );
}
