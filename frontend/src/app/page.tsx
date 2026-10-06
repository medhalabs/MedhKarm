import type { Metadata } from "next";
import Link from "next/link";

import { getWaitlistCount, WaitlistForm } from "@/features/waitlist";

export const metadata: Metadata = {
  title: "MedhKarm: your AI software team",
  description:
    "Tell your CTO what you want built. A documentation lead writes the plan, an AI team builds and tests it, and you approve before anything goes live. A free community beta for builders in India.",
};

const STEPS = [
  {
    title: "Tell your CTO",
    text: "Say what you want in your own words. Kabir asks only what he needs and suggests the technology, with the cost in rupees.",
  },
  {
    title: "Read the plan",
    text: "Lekha writes the roadmap, architecture, costs and screens. You comment and approve before any code is written.",
  },
  {
    title: "Watch it get built",
    text: "Developers build, the CTO reviews, QA tests in a real browser, security scans. You can watch the whole team in an animated office.",
  },
  {
    title: "See the demo, then approve",
    text: "A video of the app working and a preview link, with a sign-off from everyone who checked it. Nothing goes live without your yes.",
  },
  {
    title: "Ask for changes any time",
    text: "Small tweaks are built right away; bigger ones get a plan first. The documents stay up to date.",
  },
];

const POINTS = [
  {
    title: "You own the paperwork",
    text: "The plan and the changelog live in your own repository. If you ever leave, you keep everything.",
  },
  {
    title: "Checked before you see it",
    text: "Tests, a browser test, a security scan and a review run on every change. You decide how much it may do alone.",
  },
  {
    title: "Built for India",
    text: "Rupee costs, Razorpay and UPI ready, and updates by email and WhatsApp.",
  },
  {
    title: "Your keys, your models",
    text: "Use our models, or bring your own keys, or even local models. No lock-in.",
  },
];

export default async function Home() {
  const waiting = await getWaitlistCount();
  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5">
        <span className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white">
            M
          </span>
          <span className="text-sm font-semibold tracking-tight">MedhKarm</span>
        </span>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/login" className="text-zinc-600 hover:underline dark:text-zinc-400">
            Sign in
          </Link>
        </nav>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-col gap-16 px-4 pb-20">
        <section className="grid items-center gap-10 pt-8 md:grid-cols-[1.2fr_1fr]">
          <div>
            <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase dark:text-indigo-300">
              Free community beta
            </p>
            <h1 className="mt-2 text-4xl leading-tight font-semibold tracking-tight md:text-5xl">
              A whole software team, in a chat.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
              You&apos;re the CEO. Tell your CTO what you want built. An AI team plans it, builds
              it, tests it and shows you a demo, and asks before anything goes live.
            </p>
            <p className="mt-3 text-sm text-zinc-500">
              For solo founders, creators and small businesses in India.
            </p>
          </div>
          <div id="join" className="card p-6">
            <h2 className="text-lg font-semibold">Join the waitlist</h2>
            <p className="mt-1 mb-4 text-sm text-zinc-600 dark:text-zinc-400">
              {waiting > 0 ? `${waiting} builder${waiting === 1 ? " is" : "s are"} waiting. ` : ""}
              We&apos;re inviting the first builders in small groups.
            </p>
            <WaitlistForm source="home" />
          </div>
        </section>

        <section aria-label="How it works">
          <h2 className="text-2xl font-semibold tracking-tight">How it works</h2>
          <ol className="mt-6 grid gap-4 md:grid-cols-5">
            {STEPS.map((step, i) => (
              <li key={step.title} className="card p-4">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                  {i + 1}
                </span>
                <h3 className="mt-3 text-sm font-semibold">{step.title}</h3>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section aria-label="Why MedhKarm">
          <h2 className="text-2xl font-semibold tracking-tight">Not just an app that appears</h2>
          <p className="mt-2 max-w-2xl text-zinc-600 dark:text-zinc-400">
            Most tools hand you code and leave. MedhKarm runs the project the way a good software
            company would: a plan you approve, work that is checked, proof you can watch, and
            changes that follow the same careful path.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {POINTS.map((point) => (
              <div key={point.title} className="card p-5">
                <h3 className="text-sm font-semibold">{point.title}</h3>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{point.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="card flex flex-col items-start gap-3 p-8">
          <h2 className="text-2xl font-semibold tracking-tight">Be one of the first builders</h2>
          <p className="max-w-xl text-zinc-600 dark:text-zinc-400">
            It&apos;s free while we build it with the community. Tell us what you&apos;d like to
            make, and we&apos;ll write when your invite is ready.
          </p>
          <a href="#join" className="btn-primary">
            Join the waitlist
          </a>
        </section>
      </main>

      <footer className="mx-auto w-full max-w-5xl px-4 py-8 text-xs text-zinc-500">
        MedhKarm · a free community beta ·{" "}
        <Link href="/login" className="underline">
          Sign in
        </Link>
      </footer>
    </div>
  );
}
