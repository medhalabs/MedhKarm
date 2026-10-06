from datetime import UTC, datetime
from typing import Any

from app.features.events.schemas import Actor, Event, EventType
from app.features.signoffs.schemas import State
from app.features.signoffs.service import build

NAMES = {"cto": "Kabir", "qa": "Tara", "security": "Vikram", "devops": "Neel", "docs": "Lekha"}


def events(*items: tuple[Actor, EventType, str, dict[str, Any]]) -> list[Event]:
    return [
        Event(
            id=i,
            run_id="r",
            actor=actor,
            type=type_,
            summary=summary,
            data=data,
            occurred_at=datetime.now(UTC),
        )
        for i, (actor, type_, summary, data) in enumerate(items, start=1)
    ]


def by_role(log: list[Event]) -> dict[str, Any]:
    return {s.role: s for s in build(log, NAMES)}


def test_a_run_that_hasnt_started_is_all_waiting_or_skipped() -> None:
    cards = by_role([])
    assert [c.role for c in build([], NAMES)] == [
        "developer",
        "cto",
        "qa",
        "security",
        "devops",
        "docs",
        "founder",
    ]
    waiting = {r for r, c in cards.items() if c.state == State.WAITING}
    assert waiting == {"developer", "cto", "qa", "security", "devops", "docs", "founder"}
    assert cards["cto"].name == "Kabir" and cards["developer"].name == "Developers"


def test_a_clean_release_is_signed_off_by_everyone() -> None:
    cards = by_role(
        events(
            (
                Actor.DEVELOPER,
                EventType.WORK_FINISHED,
                "Isha: menu",
                {"task_id": "t1", "member": "Isha"},
            ),
            (
                Actor.DEVELOPER,
                EventType.WORK_FINISHED,
                "Arjun: cart",
                {"task_id": "t2", "member": "Arjun"},
            ),
            (
                Actor.CTO,
                EventType.REVIEW_FINISHED,
                "Approved menu",
                {"task_id": "t1", "decision": "approve"},
            ),
            (
                Actor.CTO,
                EventType.REVIEW_FINISHED,
                "Approved cart",
                {"task_id": "t2", "decision": "approve"},
            ),
            (Actor.QA, EventType.CHECK_FINISHED, "Checks passed (tests, lint)", {"passed": True}),
            (
                Actor.QA,
                EventType.CHECK_FINISHED,
                "Browser test passed (a.spec.ts)",
                {"passed": True, "browser": True},
            ),
            (
                Actor.SECURITY,
                EventType.SECURITY_FINISHED,
                "No security problems found",
                {"blocking": 0, "warnings": 0},
            ),
            (
                Actor.DOCS,
                EventType.DOCS_UPDATED,
                "Lekha added to the changelog: Tips",
                {"entry": "- Tips\n- Menu"},
            ),
            (
                Actor.DEVOPS,
                EventType.DEPLOY_FINISHED,
                "Preview ready: https://p.vercel.app",
                {"url": "https://p.vercel.app"},
            ),
            (Actor.FOUNDER, EventType.APPROVAL_DECIDED, "Approved the release", {"approved": True}),
        )
    )
    assert {r: c.state for r, c in cards.items()} == {r: State.OK for r in cards}
    assert cards["developer"].headline == "Built 2 tasks (Arjun, Isha)"
    assert cards["cto"].headline == "Reviewed 2 tasks, all approved"
    assert cards["qa"].headline == "Checks passed (tests, lint) · Browser test passed (a.spec.ts)"
    assert (
        cards["devops"].url == "https://p.vercel.app"
        and cards["devops"].headline == "Preview ready"
    )
    assert cards["docs"].details == ["- Tips", "- Menu"]
    assert cards["founder"].headline == "You approved the release"


def test_sent_back_work_and_open_comments_are_shown_honestly() -> None:
    cards = by_role(
        events(
            (
                Actor.CTO,
                EventType.REVIEW_FINISHED,
                "Sent back",
                {"task_id": "t1", "decision": "revise"},
            ),
            (
                Actor.CTO,
                EventType.REVIEW_FINISHED,
                "Moved on from “Cart”",
                {"task_id": "t1", "decision": "approve", "accepted_with_issues": True},
            ),
        )
    )
    assert cards["cto"].state == State.WARN
    assert cards["cto"].headline == (
        "Reviewed 1 task, sent 1 back for changes; moved on from 1 with open comments"
    )


def test_only_the_latest_check_counts_and_a_failure_is_a_failure() -> None:
    cards = by_role(
        events(
            (
                Actor.QA,
                EventType.CHECK_FINISHED,
                "Checks failed: sent to Isha to fix",
                {"passed": False},
            ),
            (Actor.QA, EventType.CHECK_FINISHED, "Checks passed (tests)", {"passed": True}),
            (
                Actor.QA,
                EventType.CHECK_FINISHED,
                "Browser test failed: sent to Arjun to fix",
                {"passed": False, "browser": True},
            ),
        )
    )
    assert cards["qa"].state == State.FAIL
    assert cards["qa"].headline == "Browser test failed: sent to Arjun to fix"


def test_security_warnings_and_blocks() -> None:
    warn = by_role(
        events(
            (
                Actor.SECURITY,
                EventType.SECURITY_FINISHED,
                "No blocking problems; 2 warnings for you",
                {"blocking": 0, "warnings": 2},
            )
        )
    )
    block = by_role(
        events(
            (
                Actor.SECURITY,
                EventType.SECURITY_FINISHED,
                "Stopped the release: 1 security problem still there",
                {"blocking": 1, "warnings": 0},
            )
        )
    )
    assert warn["security"].state == State.WARN and block["security"].state == State.FAIL


def test_a_failed_preview_and_a_rejection_are_failures() -> None:
    cards = by_role(
        events(
            (Actor.DEVOPS, EventType.DEPLOY_FINISHED, "The preview didn't build: ERROR", {}),
            (
                Actor.DEVOPS,
                EventType.CHANGES_DELIVERED,
                "Opened a pull request: https://github.com/me/shop/pull/3",
                {"pull_request_url": "https://github.com/me/shop/pull/3"},
            ),
            (
                Actor.FOUNDER,
                EventType.APPROVAL_DECIDED,
                "Did not approve the release: too slow",
                {"approved": False},
            ),
        )
    )
    assert cards["devops"].state == State.FAIL
    assert cards["devops"].url == "https://github.com/me/shop/pull/3"
    assert cards["founder"].state == State.FAIL


def test_the_approval_rules_can_sign_off_for_the_founder() -> None:
    cards = by_role(
        events(
            (
                Actor.SYSTEM,
                EventType.APPROVAL_DECIDED,
                "Approved by your rules",
                {"approved": True, "by": "rules"},
            )
        )
    )
    assert cards["founder"].headline == "Approved by your rules"


def test_steps_a_run_never_reached_are_skipped_once_it_is_at_the_gate_or_over() -> None:
    at_gate = by_role(events((Actor.CTO, EventType.APPROVAL_REQUESTED, "Waiting", {})))
    assert at_gate["security"].state == State.SKIPPED
    assert at_gate["docs"].headline == "No docs folder in this project to update"
    assert at_gate["devops"].headline == "No preview was set up for this run"
    over = by_role(events((Actor.SYSTEM, EventType.RUN_FINISHED, "Stopped", {})))
    assert over["security"].state == State.SKIPPED
