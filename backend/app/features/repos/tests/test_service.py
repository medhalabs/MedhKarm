from app.features.repos.schemas import RepoSource
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import FakeHost, sandbox_with

SOURCE = RepoSource(url="https://github.com/medhalabs/notes", branch="dev")


async def test_checkout_clones_maps_and_installs_once() -> None:
    host, sandbox = FakeHost(), sandbox_with({})
    repos = RepoService(host)

    first = await repos.checkout(sandbox, SOURCE)
    again = await repos.checkout(sandbox, SOURCE)  # a retry after a crash

    assert host.clones == 1
    assert first.commit == again.commit == "abc123"
    assert first.map.test_command == "python -m pytest -q"
    assert "pip install -q -r requirements.txt" in sandbox.commands
    assert first.setup_ok


async def test_without_a_repository_only_maps_and_installs_nothing() -> None:
    sandbox = sandbox_with({"requirements.txt": "fastapi\n", "app.py": "x = 1\n"})

    checkout = await RepoService().checkout(sandbox, None)

    assert checkout.commit == "" and checkout.map.file_count == 2
    assert not any(c.startswith("pip install") for c in sandbox.commands)


async def test_deliver_names_the_branch_after_the_run_and_quotes_the_request() -> None:
    host = FakeHost()

    await RepoService(host).deliver(
        sandbox_with({}), SOURCE, "run42", "Add search\nwith filters", "Added /search."
    )

    [(branch, title, body)] = host.delivered
    assert (branch, title) == ("medhkarm/run42", "Add search")
    assert "Added /search." in body and "> Add search\n> with filters" in body
