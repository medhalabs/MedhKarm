"""Priya's nudge: kind, rare and honest. Only after a day, never after four."""

from datetime import UTC, datetime, timedelta

from app.features.inbox.nudge import nudge
from app.features.inbox.schemas import Approval, Blocked, Inbox, Plan, Questions

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
LINK = "https://app.in/admin/inbox"


def approval(hours: float, request: str = "Coffee shop orders\nwith UPI") -> Approval:
    return Approval(run_id="r1", request=request, waiting_since=NOW - timedelta(hours=hours))


def test_nothing_is_said_before_a_day_has_passed() -> None:
    assert nudge(Inbox(approvals=[approval(23)]), NOW, LINK) is None
    assert nudge(Inbox(), NOW, LINK) is None


def test_after_a_day_she_names_what_is_waiting_and_how_long() -> None:
    inbox = Inbox(
        approvals=[approval(26)],
        plans=[
            Plan(blueprint_id="b1", title="Tuition app", waiting_since=NOW - timedelta(hours=50))
        ],
        questions=[Questions(project_id="p", project_name="Habits", questions=["a?", "b?"])],
        blocked=[Blocked(project_id="p", project_name="Habits", item_id="i", title="t", note="n")],
    )

    update = nudge(inbox, NOW, LINK)

    assert update is not None
    assert update.subject == "Priya: 4 things are waiting for you"
    lines = update.text.splitlines()
    assert lines[0] == "Hi, it's Priya. 4 things are waiting for you:"
    assert lines[1] == "- A plan to read: Tuition app (waiting 2 days)"  # the longest wait first
    assert "- A release to approve: Coffee shop orders (waiting 1 day)" in lines
    assert "- 2 questions from Mira" in lines and "- 1 blocked item" in lines
    assert update.text.endswith(f"Open your inbox: {LINK}")
    assert "\n" not in update.short and update.short.startswith("Priya: 4 things")  # WhatsApp


def test_one_thing_reads_naturally() -> None:
    update = nudge(Inbox(approvals=[approval(30)]), NOW, "")
    assert update is not None
    assert update.subject == "Priya: 1 thing is waiting for you"
    assert "Open your inbox" not in update.text


def test_she_stops_after_four_days() -> None:
    assert nudge(Inbox(approvals=[approval(95)]), NOW, LINK) is not None
    assert nudge(Inbox(approvals=[approval(97)]), NOW, LINK) is None


def test_questions_and_blocked_work_alone_never_trigger_a_nudge() -> None:
    inbox = Inbox(questions=[Questions(project_id="p", project_name="H", questions=["a?"])])
    assert nudge(inbox, NOW, LINK) is None  # no timestamp to say how long: the standup has them
