"""The inbox gathers what needs the founder: their runs at the gate, the PM's questions,
blocked items, and the team's latest replies."""

from datetime import UTC, datetime

from app.features.inbox.service import InboxService
from app.features.messages.schemas import Message, ThreadKind
from app.features.projects.schemas import (
    BacklogItem,
    ItemStatus,
    Project,
    ProjectDetail,
    ProjectStatus,
)
from app.features.runs.schemas import Run, RunStatus

NOW = datetime(2026, 10, 5, tzinfo=UTC)


def run(run_id: str, status: RunStatus, gate: dict[str, object] | None = None) -> Run:
    return Run(
        id=run_id,
        company_id="c1",
        request=f"Build {run_id}",
        test_command="",
        status=status,
        gate=gate,
        created_at=NOW,
        updated_at=NOW,
    )


class Runs:
    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Run]:
        return [
            run(
                "r1",
                RunStatus.WAITING_FOR_APPROVAL,
                {"reasons": ["It changes package.json."], "preview_url": "https://p.vercel.app"},
            ),
            run("r2", RunStatus.RUNNING),
        ]


PROJECT = Project(
    id="p1",
    company_id="c1",
    name="Tip splitter",
    goal="Split bills",
    status=ProjectStatus.ACTIVE,
    autopilot=False,
    daily_limit=2,
    questions=["Round to 2 decimals?"],
    created_at=NOW,
    updated_at=NOW,
)


class Projects:
    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Project]:
        return [PROJECT]

    async def get(self, project_id: str) -> ProjectDetail:
        item = BacklogItem(
            id="i1",
            project_id="p1",
            position=1,
            title="Uneven split",
            status=ItemStatus.BLOCKED,
            note="You cancelled it. Retry or skip it.",
            created_at=NOW,
            updated_at=NOW,
        )
        return ProjectDetail(**PROJECT.model_dump(), items=[item])


class Messages:
    async def recent(self, company_id: str, limit: int = 20) -> list[Message]:
        def message(author: str, body: str) -> Message:
            return Message(
                id=1,
                company_id="c1",
                thread=ThreadKind.RUN,
                thread_id="r1",
                author=author,
                name=author,
                to="x",
                body=body,
                created_at=NOW,
            )

        return [message("cto", "On it."), message("founder", "Hurry?")]


async def test_the_inbox_has_what_needs_the_founder() -> None:
    inbox = await InboxService(Runs(), Projects(), Messages()).for_company("c1")

    assert [a.run_id for a in inbox.approvals] == ["r1"]
    assert inbox.approvals[0].reasons == ["It changes package.json."]
    assert inbox.approvals[0].preview_url == "https://p.vercel.app"
    assert inbox.questions[0].questions == ["Round to 2 decimals?"]
    assert [(b.title, b.note) for b in inbox.blocked] == [
        ("Uneven split", "You cancelled it. Retry or skip it.")
    ]
    assert [m.body for m in inbox.replies] == ["On it."]  # the team's, not the founder's own
    assert inbox.count == 3


async def test_a_plan_waiting_for_approval_is_in_the_inbox_and_counted() -> None:
    from app.features.blueprints.schemas import BlueprintStatus, BlueprintSummary

    def plan(blueprint_id: str, status: BlueprintStatus) -> BlueprintSummary:
        return BlueprintSummary(
            id=blueprint_id, title="Coffee shop app", status=status, created_at=NOW, updated_at=NOW
        )

    class Plans:
        async def list(self, company_id: str) -> list[BlueprintSummary]:
            return [
                plan("b1", BlueprintStatus.READY),
                plan("b2", BlueprintStatus.WRITING),  # not ready yet
                plan("b3", BlueprintStatus.APPROVED),  # already building
            ]

    inbox = await InboxService(Runs(), Projects(), Messages(), Plans()).for_company("c1")

    assert [(p.blueprint_id, p.title) for p in inbox.plans] == [("b1", "Coffee shop app")]
    assert inbox.count == 4
