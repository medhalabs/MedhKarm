from datetime import UTC, datetime

import pytest

from app.features.blueprints.author import BlueprintAuthor
from app.features.blueprints.catalog import DOCS
from app.features.blueprints.exceptions import BlueprintNotFoundError, BlueprintNotReadyError
from app.features.blueprints.memory_repository import InMemoryBlueprintRepository
from app.features.blueprints.schemas import BlueprintStatus, NewBlueprint
from app.features.blueprints.service import REVISE_JOB, WRITE_JOB, BlueprintService, title_of
from app.features.blueprints.writer import BlueprintWriter, describe
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.models.exceptions import ModelCallError
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.runs.schemas import Run, RunStatus, StartRun
from app.features.starters.schemas import StackChoice
from app.workers.approved_plans import ApprovedPlans

COMPANY, OTHER = "company-a", "company-b"
BRIEF = StartRun(
    request="A web app for my coffee shop to take orders\nWith UPI payments",
    stack=StackChoice(payments="razorpay"),
)


class Runs:
    def __init__(self) -> None:
        self.started: list[tuple[StartRun, str | None]] = []
        self.fail = False

    async def start(self, body: StartRun, company_id: str | None = None) -> Run:
        if self.fail:
            raise RuntimeError("queue down")
        self.started.append((body, company_id))
        now = datetime.now(UTC)
        return Run(
            id="run-1",
            company_id=company_id,
            request=body.request,
            test_command="",
            status=RunStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )


def make() -> tuple[BlueprintService, InMemoryBlueprintRepository, InMemoryJobQueue, Runs]:
    repo, jobs, runs = InMemoryBlueprintRepository(), InMemoryJobQueue(), Runs()
    return BlueprintService(repo, jobs, runs), repo, jobs, runs


def lekha(*texts: str) -> BlueprintWriter:
    return BlueprintWriter(ScriptedLLMProvider([LLMResponse(content=t) for t in texts]))


async def written(service: BlueprintService, repo: InMemoryBlueprintRepository) -> str:
    """A blueprint whose documents are all written."""
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    await BlueprintAuthor(repo, lekha(*[f"# {d.title}\nbody" for d in DOCS])).write(blueprint.id)
    return blueprint.id


def test_titles_come_from_the_first_line() -> None:
    assert title_of("\n  A coffee shop app \nmore") == "A coffee shop app"
    assert len(title_of("x" * 300)) <= 70


async def test_asking_for_the_plan_saves_the_brief_and_queues_lekha() -> None:
    service, _, jobs, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    assert blueprint.status == BlueprintStatus.WRITING
    assert blueprint.title == "A web app for my coffee shop to take orders"
    job = await jobs.get(1)
    assert job and job.kind == WRITE_JOB and job.payload == {"blueprint_id": blueprint.id}


async def test_other_companies_cannot_see_it() -> None:
    service, _, _, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    with pytest.raises(BlueprintNotFoundError):
        await service.owned(blueprint.id, OTHER)
    assert await service.list(OTHER) == []
    assert [b.id for b in await service.list(COMPANY)] == [blueprint.id]


async def test_lekha_writes_every_document_in_order_and_the_plan_is_ready() -> None:
    service, repo, _, _ = make()
    blueprint_id = await written(service, repo)
    done = await service.get(blueprint_id)
    assert done.status == BlueprintStatus.READY
    assert [d.path for d in done.docs] == [d.path for d in DOCS]
    assert done.progress == ""


async def test_a_retry_keeps_what_was_already_written() -> None:
    service, repo, _, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    first = BlueprintAuthor(repo, lekha("# Product brief\nok", "# Roadmap\nok"))
    with pytest.raises(AssertionError):  # the script ran out: the third call fails
        await first.write(blueprint.id)
    assert [d.id for d in (await service.get(blueprint.id)).docs] == ["brief", "roadmap"]

    rest = lekha(*[f"# {d.title}\nbody" for d in DOCS[2:]])
    await BlueprintAuthor(repo, rest).write(blueprint.id)
    assert len((await service.get(blueprint.id)).docs) == len(DOCS)


async def test_giving_up_tells_the_founder_and_a_retry_asks_again() -> None:
    service, repo, jobs, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    await BlueprintAuthor(repo, lekha()).give_up(blueprint.id, "model down" + "!" * 400)
    failed = await service.get(blueprint.id)
    assert failed.status == BlueprintStatus.FAILED
    assert failed.error.startswith("Lekha couldn't finish: model down")
    assert len(failed.error) < 400

    again = await service.retry(blueprint.id, COMPANY)
    assert again.status == BlueprintStatus.WRITING and again.error == ""
    assert (await jobs.get(2)) is not None
    with pytest.raises(BlueprintNotReadyError):
        await service.retry(blueprint.id, COMPANY)


async def test_a_comment_rewrites_only_the_documents_it_touches() -> None:
    service, repo, jobs, _ = make()
    blueprint_id = await written(service, repo)

    commented = await service.comment(blueprint_id, COMPANY, "Add a tip option at checkout")
    assert commented.status == BlueprintStatus.REVISING
    job = await jobs.get(2)
    assert job and job.kind == REVISE_JOB

    pick = LLMResponse(
        tool_calls=[
            ToolCall(id="1", name="rewrite_docs", arguments={"docs": ["costs", "brief", "nope"]})
        ]
    )
    llm = ScriptedLLMProvider(
        [pick, LLMResponse(content="# Product brief\nwith tips"), LLMResponse(content="costs")]
    )
    await BlueprintAuthor(repo, BlueprintWriter(llm)).revise(blueprint_id)

    done = await service.get(blueprint_id)
    assert done.status == BlueprintStatus.READY and done.revision == 1
    assert {d.id: d.content for d in done.docs}["brief"] == "# Product brief\nwith tips"
    assert {d.id: d.content for d in done.docs}["costs"].startswith("# Costs and risks")
    assert {d.id: d.content for d in done.docs}["roadmap"] == "# Roadmap\nbody"  # untouched
    assert [c.author for c in done.comments] == ["founder", "lekha"]
    assert "product brief, costs and risks" in done.comments[-1].text
    prompt = llm.calls[1][-1]["content"]  # the rewrite sees the comment and the old text
    assert "Add a tip option at checkout" in prompt and "body" in prompt


async def test_an_unclear_comment_rewrites_everything_rather_than_nothing() -> None:
    service, repo, _, _ = make()
    blueprint_id = await written(service, repo)
    await service.comment(blueprint_id, COMPANY, "hmm")
    llm = ScriptedLLMProvider([LLMResponse(content="no tool call")])
    docs = (await service.get(blueprint_id)).docs
    assert await BlueprintWriter(llm).affected(docs, "hmm") == [d.id for d in DOCS]


async def test_comments_only_while_the_plan_is_ready() -> None:
    service, _, _, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))
    with pytest.raises(BlueprintNotReadyError):
        await service.comment(blueprint.id, COMPANY, "too early")
    with pytest.raises(BlueprintNotReadyError):
        await service.approve(blueprint.id, COMPANY)


async def test_approving_starts_the_build_with_the_same_brief() -> None:
    service, repo, _, runs = make()
    blueprint_id = await written(service, repo)

    approved = await service.approve(blueprint_id, COMPANY)

    assert approved.status == BlueprintStatus.APPROVED and approved.run_id == "run-1"
    assert runs.started == [(BRIEF, COMPANY)]
    with pytest.raises(BlueprintNotReadyError):  # not twice
        await service.approve(blueprint_id, COMPANY)
    plan = await service.for_run("run-1")
    assert plan and [d.id for d in plan.docs][:2] == ["brief", "roadmap"]
    assert await service.for_run("another-run") is None


async def test_a_failed_start_leaves_the_plan_ready_to_approve_again() -> None:
    service, repo, _, runs = make()
    blueprint_id = await written(service, repo)
    runs.fail = True
    with pytest.raises(RuntimeError):
        await service.approve(blueprint_id, COMPANY)
    assert (await service.get(blueprint_id)).status == BlueprintStatus.READY
    runs.fail = False
    assert (await service.approve(blueprint_id, COMPANY)).run_id == "run-1"


async def test_the_build_gets_the_documents_and_an_index() -> None:
    service, repo, _, _ = make()
    blueprint_id = await written(service, repo)
    await service.approve(blueprint_id, COMPANY)

    plan = await ApprovedPlans(service).for_run("run-1")

    assert plan is not None
    assert plan.files["docs/03-architecture.md"] == "# Architecture\nbody"
    assert "[Architecture](03-architecture.md)" in plan.files["docs/README.md"]
    assert "docs/README.md" not in plan.titles  # the index isn't a plan document
    assert await ApprovedPlans(service).for_run("no-run") is None


def test_the_brief_describes_the_request_and_the_founders_choices() -> None:
    text = describe(BRIEF)
    assert "coffee shop" in text and "payments: razorpay" in text and "A new project" in text


async def test_a_model_failure_raises_so_the_job_retries() -> None:
    service, repo, _, _ = make()
    blueprint = await service.create(COMPANY, NewBlueprint(brief=BRIEF))

    class Down(ScriptedLLMProvider):
        async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
            raise ModelCallError("503")

    with pytest.raises(ModelCallError):
        await BlueprintAuthor(repo, BlueprintWriter(Down([]))).write(blueprint.id)
    assert (await service.get(blueprint.id)).status == BlueprintStatus.WRITING


def test_documents_are_told_the_stack_the_team_really_builds_on() -> None:
    text = describe(BRIEF, "Stack: frontend: nextjs, database: supabase")
    assert "must not propose another" in text and "database: supabase" in text


async def test_the_stack_reaches_every_document_prompt() -> None:
    llm = ScriptedLLMProvider([LLMResponse(content="# Product brief\nx")])
    writer = BlueprintWriter(llm, stack=lambda brief: "Stack: nextjs + supabase")
    await writer.write(BRIEF, DOCS[0], [])
    assert "Stack: nextjs + supabase" in llm.calls[0][-1]["content"]


def test_the_default_stack_for_a_new_project_comes_from_the_starters() -> None:
    from app.features.starters.service import StarterService
    from app.workers.approved_plans import StackText

    text = StackText(StarterService())(BRIEF)
    assert "nextjs" in text and "razorpay" in text
    existing = StartRun(request="Add export", repo={"url": "https://github.com/me/shop"})
    assert StackText(StarterService())(existing) == ""
