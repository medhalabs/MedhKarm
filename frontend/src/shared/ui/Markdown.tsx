import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Founder-written Markdown (requests, specs, messages), styled for the admin. Raw HTML in the
 * text is never rendered. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => (
            <h3
              className="mt-5 text-base font-semibold text-zinc-900 first:mt-0 dark:text-zinc-100"
              {...p}
            />
          ),
          h2: (p) => (
            <h3
              className="mt-5 text-base font-semibold text-zinc-900 first:mt-0 dark:text-zinc-100"
              {...p}
            />
          ),
          h3: (p) => (
            <h4
              className="mt-4 text-sm font-semibold text-zinc-900 first:mt-0 dark:text-zinc-100"
              {...p}
            />
          ),
          h4: (p) => (
            <h5 className="mt-3 text-sm font-semibold text-zinc-900 dark:text-zinc-100" {...p} />
          ),
          strong: (p) => (
            <strong className="font-semibold text-zinc-900 dark:text-zinc-100" {...p} />
          ),
          ul: (p) => <ul className="list-disc space-y-1 pl-5 marker:text-zinc-400" {...p} />,
          ol: (p) => <ol className="list-decimal space-y-1 pl-5 marker:text-zinc-400" {...p} />,
          blockquote: (p) => (
            <blockquote
              className="border-l-2 border-indigo-300 pl-3 text-zinc-900 italic dark:border-indigo-700 dark:text-zinc-100"
              {...p}
            />
          ),
          code: (p) => (
            <code
              className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-[0.8em] dark:bg-zinc-800"
              {...p}
            />
          ),
          pre: (p) => (
            <pre
              className="overflow-x-auto rounded-lg bg-zinc-950 p-3 text-zinc-100 [&_code]:bg-transparent"
              {...p}
            />
          ),
          a: (p) => (
            <a
              className="text-indigo-600 underline underline-offset-2 dark:text-indigo-400"
              target="_blank"
              rel="noreferrer"
              {...p}
            />
          ),
          table: (p) => (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm" {...p} />
            </div>
          ),
          th: (p) => (
            <th
              className="border-b border-zinc-200 px-2 py-1.5 font-semibold dark:border-zinc-700"
              {...p}
            />
          ),
          td: (p) => (
            <td className="border-b border-zinc-100 px-2 py-1.5 dark:border-zinc-800" {...p} />
          ),
          hr: () => <hr className="border-zinc-200 dark:border-zinc-800" />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
