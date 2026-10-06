"""The documents of a blueprint, in the order Lekha writes them."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class DocSpec:
    id: str
    title: str
    path: str
    asks: str  # what this document must contain
    author: str = "docs"  # who writes it: Lekha ("docs") or Anaya ("design")
    format: Literal["markdown", "html"] = "markdown"  # html: the screen mockups


# Typical 2026 prices the costs document may use. They change: the document says "about" and
# tells the founder to check current pricing.
COST_FACTS = (
    "Use these typical prices, say 'about', and tell the founder to check current pricing: "
    "Vercel's free Hobby plan costs ₹0 (the paid plan is about $20 per member a month); "
    "Supabase's free plan costs ₹0 for a small project (the paid plan is about $25 a month); "
    "Resend email is free up to about 3,000 emails a month; a domain is about ₹800-1,500 a "
    "year. Razorpay has no monthly fee and takes about 2% of each payment: show it as 'about "
    "2% of each payment', never as a monthly cost, and never add it to the monthly total. "
    "Give the monthly total for the fixed costs only, as a range."
)

MOCKUP_ASKS = (
    "One self-contained HTML page that draws the first version's key screens (three or four, "
    "from the screens document) side by side as simple wireframes, each in a phone-sized frame "
    "with the screen's name above it. Use real content for this project (actual item names, "
    "prices in rupees, button labels), never lorem ipsum. Plain HTML and CSS in one <style> "
    "block: NO JavaScript, no external fonts, images, links or scripts. Soft colours, readable "
    "text, rounded buttons, a clear main action on each screen. Start with <!doctype html>."
)

DOCS: tuple[DocSpec, ...] = (
    DocSpec(
        "brief",
        "Product brief",
        "docs/01-product-brief.md",
        "The goal in two sentences; who uses it and what they do; the must-have features for "
        "the first release as a short list; what is NOT in the first release; assumptions you "
        "made where the founder didn't say.",
    ),
    DocSpec(
        "roadmap",
        "Roadmap",
        "docs/02-roadmap.md",
        "Three to five milestones, each a working slice the founder can try, in the order to "
        "build them. Milestone 1 is the smallest useful version and is what the team builds "
        "first; later milestones are added later as changes. For each: what the founder will "
        "be able to do, and 'done when' checks.",
    ),
    DocSpec(
        "screens",
        "Screens and journeys",
        "docs/03-screens.md",
        "The two to four journeys people take (who they are, what they want, the steps), then "
        "every screen the first version needs: its name, what is on it, what the person can do "
        "there and where it leads. Mobile first; say where a desktop differs. Only what "
        "milestone 1 needs.",
        author="design",
    ),
    DocSpec(
        "mockups",
        "Screen mockups",
        "docs/04-mockups.html",
        MOCKUP_ASKS,
        author="design",
        format="html",
    ),
    DocSpec(
        "architecture",
        "Architecture",
        "docs/05-architecture.md",
        "The stack, and why each choice fits this project in one sentence; how the parts fit "
        "together, with one mermaid diagram (```mermaid); where the app runs; how sign-in and "
        "payments work if the project has them.",
    ),
    DocSpec(
        "data",
        "Data and API",
        "docs/06-data-and-api.md",
        "The tables (name, columns, what each is for) and the endpoints or pages (method, path, "
        "what it does). Only what milestone 1 needs, plus a short 'later' list.",
    ),
    DocSpec(
        "structure",
        "File structure",
        "docs/07-structure.md",
        "The project's folder and file tree in a code block, with one line on what each folder "
        "is for and where new features go.",
    ),
    DocSpec(
        "tests",
        "Test plan",
        "docs/08-test-plan.md",
        "What will be tested for milestone 1: the checks that must pass, the main user "
        "journeys tested in a browser, and what is checked by hand at the demo.",
    ),
    DocSpec(
        "costs",
        "Costs and risks",
        "docs/09-costs-and-risks.md",
        "Monthly running costs in Indian rupees (₹) for the stack's hosting, database, email "
        "and domain, for a small business, saying which are free at the start; the one-time "
        "costs; the top five risks with what to do about each. " + COST_FACTS,
    ),
)
# A change to an existing, live project: three short documents in the project's own
# docs/changes/ folder, so the original plan and the founder's own docs stay untouched.
CHANGE_DOCS: tuple[DocSpec, ...] = (
    DocSpec(
        "change",
        "Change brief",
        "{folder}/01-change-brief.md",
        "What the founder wants changed and why, in two sentences; who it affects; what is NOT "
        "part of this change; assumptions you made where the founder didn't say.",
    ),
    DocSpec(
        "impact",
        "Plan and impact",
        "{folder}/02-plan-and-impact.md",
        "Which parts of the app change (screens, pages, data, endpoints) and how, in plain "
        "words; any new data or settings; the order to build it in; 'done when' checks. This is "
        "a change to a project that already works: describe only what changes. You have not seen "
        "its code: name parts by what they do ('the checkout page', 'the orders table'), and "
        "never invent file names, folders or function names.",
    ),
    DocSpec(
        "checks",
        "Checks and risks",
        "{folder}/03-checks-and-risks.md",
        "What will be tested; what could break in the live app and what to do about each; the "
        "extra running cost in ₹ if any, or 'no extra cost'. " + COST_FACTS,
    ),
)
ALL_DOCS = (*DOCS, *CHANGE_DOCS)
BY_ID = {d.id: d for d in ALL_DOCS}


def docset(is_change: bool) -> tuple[DocSpec, ...]:
    """The documents to write: a full plan for a new project, three for a change."""
    return CHANGE_DOCS if is_change else DOCS


def change_folder(created: datetime, title: str) -> str:
    """Where a change's documents live: docs/changes/2026-10-06-add-a-tip-option."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].strip("-") or "change"
    return f"docs/changes/{created:%Y-%m-%d}-{slug}"


README_PATH = "docs/README.md"
