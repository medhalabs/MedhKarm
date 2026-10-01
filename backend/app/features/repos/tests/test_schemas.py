import pytest
from pydantic import ValidationError

from app.features.repos.schemas import CodebaseMap, RepoSource


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/medhalabs/shop",
        "https://github.com/medhalabs/shop.git",
        "https://github.com/medhalabs/shop/",
        " https://github.com/medha-labs/shop.api ",
    ],
)
def test_github_addresses_are_accepted(url: str) -> None:
    source = RepoSource(url=url)
    assert source.owner in ("medhalabs", "medha-labs")
    assert source.name in ("shop", "shop.api")


@pytest.mark.parametrize(
    "url",
    [
        "git@github.com:medhalabs/shop.git",  # ssh: we clone over https with a token
        "http://github.com/medhalabs/shop",
        "https://gitlab.com/medhalabs/shop",
        "https://github.com/medhalabs",
        "https://github.com/medhalabs/shop; rm -rf /",
        "file:///etc",
    ],
)
def test_anything_else_is_refused(url: str) -> None:
    with pytest.raises(ValidationError):
        RepoSource(url=url)


def test_branch_names_are_checked() -> None:
    assert RepoSource(url="https://github.com/a/b", branch=" feature/login ").branch == (
        "feature/login"
    )
    assert RepoSource(url="https://github.com/a/b", branch="").branch is None
    for bad in ("-x", "a..b", "main; ls", "$(id)"):
        with pytest.raises(ValidationError):
            RepoSource(url="https://github.com/a/b", branch=bad)


def test_brief_is_capped() -> None:
    codebase = CodebaseMap(file_count=2000, tree=[f"src/file_{i}.py" for i in range(2000)])
    brief = codebase.brief(limit=1000)
    assert len(brief) <= 1000
    assert brief.endswith("(map cut short)")
    assert CodebaseMap().brief() == ""
