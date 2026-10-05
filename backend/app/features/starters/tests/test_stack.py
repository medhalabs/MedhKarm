"""The stack: the founder's choice wins, then the request's words, then our defaults."""

from app.features.starters.catalog import FileCatalog
from app.features.starters.schemas import StackChoice
from app.features.starters.stack import resolve_stack

MODULES = FileCatalog().modules()


def resolve(request: str, **choice: object):  # type: ignore[no-untyped-def]
    return resolve_stack(request, StackChoice.model_validate(choice), MODULES)


def test_the_team_picks_when_nobody_says() -> None:
    stack = resolve("Build a website for my bakery with online orders")

    assert (stack.frontend, stack.api, stack.database, stack.hosting, stack.payments) == (
        "nextjs",
        "nextjs",
        "supabase",
        "vercel",
        "razorpay",
    )
    assert set(stack.sources.values()) == {"team"}
    assert (stack.starter, stack.layout) == ("nextjs", "single")


def test_the_request_and_then_the_founder_decide() -> None:
    from_request = resolve("A booking app with a Python API on AWS, paid with Stripe")
    assert (from_request.api, from_request.hosting, from_request.payments) == (
        "python",
        "aws",
        "stripe",
    )
    assert from_request.sources["api"] == "request"

    founder = resolve("A booking app with a Python API", api="Next.js ", payments="razorpay")
    assert (founder.api, founder.sources["api"]) == ("nextjs", "founder")  # their name, ours
    assert founder.sources["payments"] == "founder"


def test_a_python_api_with_a_frontend_is_split_and_gets_no_nextjs_modules() -> None:
    stack = resolve("A clinic website with patient login and reminders", api="python")

    assert (stack.starter, stack.layout, stack.database, stack.hosting) == (
        "fastapi",
        "split",
        "sqlite",
        "docker",
    )
    assert stack.modules == []
    assert any("only for the Next.js API" in note for note in stack.custom)


def test_stacks_without_a_starter_are_still_followed() -> None:
    stack = resolve("An inventory web app", api="java", payments="cashfree", database="mongodb")

    assert stack.starter is None
    brief = stack.brief()
    assert "No ready-made starter for nextjs + java" in brief
    assert "cashfree" in brief and "(founder's choice)" in brief


def test_scripts_and_libraries_get_no_starter_unless_asked() -> None:
    assert resolve("Write a CLI script that renames photos by date").starter is None
    assert resolve("A parser library for cron expressions").starter is None
    assert resolve("A package delivery website").starter == "nextjs"
    assert resolve("A CLI script", starter=True).starter == "nextjs"
    assert resolve("A shop website", starter=False).starter is None


def test_modules_come_from_the_request_with_what_they_need() -> None:
    stack = resolve(
        "A gym website: members sign up, pay monthly fees, and I see an admin dashboard"
    )
    assert stack.modules == ["auth", "dashboards", "payments"]

    chosen = resolve("A gym website", modules=["dashboards", "unknown"])
    assert chosen.modules == ["auth", "dashboards"]  # the dashboard needs sign-in

    no_payments = resolve("A shop website with checkout", payments="none")
    assert "payments" not in no_payments.modules

    custom_provider = resolve("A shop website with checkout", payments="paypal")
    assert "payments" not in custom_provider.modules
    assert any("paypal" in note for note in custom_provider.custom)


def test_notes_reach_the_brief() -> None:
    stack = resolve("A shop website", payments="cashfree", notes="Docs: https://docs.cashfree.com")
    assert "https://docs.cashfree.com" in stack.brief()


def test_technologies_listed_as_page_content_dont_pick_the_stack() -> None:
    """A landing page that lists the company's own tech (live spec, Oct 5, 2026)."""
    spec = (
        "Create a premium landing page for an AI Technology Office.\n"
        "### Tech we use\n**Backend:** Python, FastAPI, Node.js\n"
        "**Frontend:** Next.js, React\n**Data:** PostgreSQL\n**Infrastructure:** Docker, AWS"
    )
    stack = resolve(spec)

    assert (stack.api, stack.database, stack.hosting) == ("nextjs", "supabase", "vercel")
    assert (stack.starter, stack.layout) == ("nextjs", "single")
    assert set(stack.sources.values()) == {"team"}


def test_asked_for_technologies_still_count() -> None:
    assert resolve("Build it using Python and deploy it to AWS").api == "python"
    assert resolve("Build it using Python and deploy it to AWS").hosting == "aws"
    assert resolve("A shop built with Next.js, stored in Postgres").database == "postgres"
    assert resolve("An inventory API only, written in Java").frontend == "none"
    assert resolve("A page that sits within python docs").api == "nextjs"  # "within" isn't "in"


def test_a_long_specs_copy_doesnt_add_modules() -> None:
    spec = (
        "Create a premium landing page for an AI office.\n\n### Services\n"
        + "We build analytics dashboards, admin portals and member accounts for users. " * 20
    )
    assert resolve(spec).modules == []
    short = "A gym website where members log in and see an admin dashboard"
    assert resolve(short).modules == ["auth", "dashboards"]
