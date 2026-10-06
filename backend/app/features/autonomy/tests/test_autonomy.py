"""The autonomy dial: plain settings become approval rules, per company and per project."""

import pytest

from app.core.errors import NotFoundError
from app.features.approvals.schemas import Action
from app.features.approvals.service import evaluate
from app.features.autonomy.exceptions import NoProjectSettingsError
from app.features.autonomy.memory_repository import InMemoryAutonomyRepository
from app.features.autonomy.policy import build_policy, describe
from app.features.autonomy.schemas import AutonomySettings, Level, Scope
from app.features.autonomy.service import AutonomyService
from app.features.teams.loader import load_templates

BASE = load_templates()["software"].approval
CLEAN = {
    "files_changed": ["app/page.tsx", "app/menu.tsx"],
    "files_count": 2,
    "tokens": 40_000,
    "tasks_count": 2,
    "tasks_with_issues": 0,
    "tests_passed": True,
    "security_warnings": 0,
    "preview_failed": False,
}


def verdict(settings: AutonomySettings, **facts: object):  # type: ignore[no-untyped-def]
    return evaluate(build_policy(BASE, settings), {**CLEAN, **facts})


def test_the_default_settings_behave_exactly_like_the_team_template() -> None:
    for facts in (
        {},
        {"files_changed": ["package.json"]},
        {"files_count": 40},
        {"security_warnings": 2},
    ):
        mine = verdict(AutonomySettings(), **facts)
        theirs = evaluate(BASE, {**CLEAN, **facts})
        assert (mine.action, mine.rule_ids) == (theirs.action, theirs.rule_ids)
    assert verdict(AutonomySettings()).action == Action.ASK


def test_small_clean_changes_go_on_their_own_but_risky_ones_still_ask() -> None:
    small = AutonomySettings(level=Level.SMALL, small_files=3)
    assert verdict(small).action == Action.APPROVE
    assert verdict(small, files_count=4, files_changed=["a", "b", "c", "d"]).action == Action.ASK
    assert verdict(small, tasks_with_issues=1).action == Action.ASK
    assert verdict(small, files_changed=["package.json"]).action == Action.ASK  # a risky file
    assert verdict(small, security_warnings=1).action == Action.ASK


def test_on_its_own_after_checks_still_stops_for_what_the_founder_kept_switched_on() -> None:
    checks = AutonomySettings(level=Level.CHECKS)
    assert verdict(checks, files_count=30).action == Action.ASK  # 15+ files: still asks
    assert verdict(checks, files_count=30).rule_ids == ["large_change"]
    assert verdict(checks, files_changed=[".env.local"]).action == Action.ASK
    assert verdict(checks).action == Action.APPROVE
    assert verdict(checks).rule_ids == ["checks_pass"]


def test_switching_a_question_off_and_changing_its_limit() -> None:
    relaxed = AutonomySettings(
        level=Level.CHECKS, ask_large_change=False, ask_expensive=True, max_tokens=100_000
    )
    assert verdict(relaxed, files_count=30).action == Action.APPROVE  # no longer asked
    expensive = verdict(relaxed, tokens=150_000)
    assert expensive.action == Action.ASK
    assert expensive.reasons == ["It used more than 100,000 model tokens."]
    stricter = AutonomySettings(large_files=5)
    assert verdict(stricter, files_count=6).reasons == ["It changes more than 5 files."]


def test_files_the_team_must_never_change_stop_a_release_without_asking() -> None:
    settings = AutonomySettings(level=Level.CHECKS, never_touch=["payments/*", "*.sql"])
    stopped = verdict(settings, files_changed=["app/page.tsx", "payments/razorpay.ts"])
    assert stopped.action == Action.REJECT
    assert stopped.reasons == ["You told the team never to change payments/*."]
    assert verdict(settings, files_changed=["db/schema.sql"]).action == Action.REJECT
    assert verdict(settings).action == Action.APPROVE


def test_never_touch_patterns_are_cleaned_and_unsafe_ones_refused() -> None:
    assert AutonomySettings(never_touch=[" payments/* ", "", "payments/*"]).never_touch == [
        "payments/*"
    ]
    for bad in ("/etc/passwd", "../outside", "x" * 101):
        with pytest.raises(ValueError):
            AutonomySettings(never_touch=[bad])
    with pytest.raises(ValueError):
        AutonomySettings(small_files=0)


def test_the_settings_read_back_as_plain_sentences() -> None:
    assert describe(AutonomySettings()) == [
        "Every release waits for your approval.",
        "After a release it publishes to the internet.",
    ]
    text = " ".join(
        describe(
            AutonomySettings(
                level=Level.SMALL, ask_expensive=False, never_touch=["a/*", "b/*"], go_live=False
            )
        )
    )
    assert "Small, clean changes (3 files or fewer" in text
    assert "It still stops to ask you when" in text and "more than 15 files" in text
    assert "1,000,000" not in text  # switched off
    assert "never" not in text.lower() or "changes a/* or b/*" in text
    assert "doesn't publish" in text


class Projects:
    """Run r1 belongs to project p1 (the company's); p9 is somebody else's."""

    async def project_of(self, run_id: str) -> str | None:
        return {"r1": "p1"}.get(run_id)

    async def owned(self, project_id: str, company_id: str) -> None:
        if (project_id, company_id) != ("p1", "c1"):
            raise NotFoundError(f"No project {project_id}")


def service() -> tuple[AutonomyService, InMemoryAutonomyRepository]:
    repo = InMemoryAutonomyRepository()
    return AutonomyService(repo, BASE, Projects(), Projects()), repo


async def test_a_company_that_set_nothing_gets_the_templates_rules() -> None:
    s, _ = service()
    policy, go_live = await s.for_run("c1", "r1")
    assert policy is BASE and go_live is True
    assert (await s.for_run(None, "r1"))[0] is BASE  # no company (evals)
    view = await s.view("c1")
    assert (view.scope, view.own, view.settings.level) == (Scope.COMPANY, False, Level.EVERY)


async def test_a_project_uses_its_own_settings_else_the_companys() -> None:
    s, _ = service()
    await s.save("c1", None, AutonomySettings(level=Level.CHECKS))
    inherited = await s.view("c1", "p1")
    assert (inherited.scope, inherited.own, inherited.settings.level) == (
        Scope.PROJECT,
        False,
        Level.CHECKS,
    )
    policy, _ = await s.for_run("c1", "r1")
    assert evaluate(policy, CLEAN).action == Action.APPROVE  # the company's

    await s.save("c1", "p1", AutonomySettings(level=Level.EVERY, go_live=False))
    policy, go_live = await s.for_run("c1", "r1")
    assert evaluate(policy, CLEAN).action == Action.ASK and go_live is False  # the project's
    other_run = await s.for_run("c1", "r2")  # a run with no project: the company's
    assert evaluate(other_run[0], CLEAN).action == Action.APPROVE

    back = await s.reset("c1", "p1")
    assert (back.own, back.settings.level) == (False, Level.CHECKS)


async def test_only_your_own_projects_and_only_projects_can_be_reset() -> None:
    s, _ = service()
    with pytest.raises(NotFoundError):
        await s.view("c1", "p9")
    with pytest.raises(NotFoundError):
        await s.save("c2", "p1", AutonomySettings())
    with pytest.raises(NoProjectSettingsError):
        await s.reset("c1", None)


async def test_companies_dont_see_each_others_settings() -> None:
    s, _ = service()
    await s.save("c1", None, AutonomySettings(level=Level.CHECKS))
    assert (await s.view("c2")).settings.level == Level.EVERY
    assert (await s.for_run("c2", "r1"))[0] is BASE
