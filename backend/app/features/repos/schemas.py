"""A founder's existing project: where it lives, what the team learned about it, and how the
finished work went back to it."""

import re
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

# https://github.com/<owner>/<name>, optionally ending in .git or /
GITHUB_URL = re.compile(
    r"^https://github\.com/([A-Za-z0-9-]{1,39})/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?$"
)
REPO_NAME = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
BRANCH_NAME = re.compile(r"^(?!-)(?!.*\.\.)[A-Za-z0-9._/-]{1,200}$")


class RepoSource(BaseModel):
    """An existing GitHub repository to work on. GitHub only for now (JS/TS and Python)."""

    url: str = Field(max_length=300)
    branch: str | None = Field(default=None, max_length=200)  # None: the repo's default branch

    @field_validator("url")
    @classmethod
    def _github_https(cls, url: str) -> str:
        url = url.strip()
        if not GITHUB_URL.match(url):
            raise ValueError("Use the repository's GitHub address: https://github.com/owner/name")
        return url

    @field_validator("branch")
    @classmethod
    def _plain_branch(cls, branch: str | None) -> str | None:
        branch = (branch or "").strip() or None
        if branch and not BRANCH_NAME.match(branch):
            raise ValueError("Branch names use letters, digits, '.', '_', '-' and '/'")
        return branch

    @property
    def owner(self) -> str:
        return self._parts()[0]

    @property
    def name(self) -> str:
        return self._parts()[1]

    def _parts(self) -> tuple[str, str]:
        match = GITHUB_URL.match(self.url)
        assert match  # checked on creation
        return match.group(1), match.group(2)


class CodebaseMap(BaseModel):
    """What the team knows about a project before changing it. Built without a model call."""

    file_count: int = 0
    languages: dict[str, int] = Field(default_factory=dict)  # language -> number of files
    tree: list[str] = Field(default_factory=list)  # file paths, capped
    manifests: dict[str, str] = Field(default_factory=dict)  # file -> short summary
    outline: dict[str, list[str]] = Field(default_factory=dict)  # file -> top-level definitions
    readme: str = ""  # opening lines of the README
    graph: str = ""  # most connected code, from the code graph (CODE_GRAPH=true)
    setup_command: str = ""  # installs dependencies; run once before work starts
    test_command: str = ""  # detected; used when the founder gave none

    @property
    def empty(self) -> bool:
        return self.file_count == 0

    def brief(self, limit: int = 6000) -> str:
        """The map as text for the CTO and the developers, at most `limit` characters."""
        if self.empty:
            return ""
        langs = ", ".join(f"{lang} ({n})" for lang, n in self.languages.items()) or "unknown"
        parts = [f"Existing project: {self.file_count} files. Languages: {langs}."]
        if self.test_command:
            parts.append(f"Tests run with: {self.test_command}")
        if self.readme:
            parts.append("README (start):\n" + self.readme)
        if self.manifests:
            parts.append(
                "Project files:\n" + "\n".join(f"- {f}: {s}" for f, s in self.manifests.items())
            )
        if self.outline:
            parts.append(
                "Code outline (top-level definitions):\n"
                + "\n".join(f"- {f}: {', '.join(defs)}" for f, defs in self.outline.items())
            )
        if self.graph:
            parts.append(self.graph)
        parts.append("Files:\n" + "\n".join(self.tree))
        text = "\n\n".join(parts)
        return text if len(text) <= limit else text[: limit - 20].rstrip() + "\n… (map cut short)"


def repo_name_for(request: str, run_id: str) -> str:
    """A new repository's name from the request: 'roman-numerals-converter-3f9a2c'."""
    words = re.findall(r"[a-z0-9]+", request.lower())
    slug = "-".join(words)[:40].strip("-") or "project"
    return f"{slug}-{run_id[:6]}"


def check_repo_name(name: str | None) -> str | None:
    """GitHub's rules for a repository name; blank means none."""
    name = (name or "").strip() or None
    if name and (not REPO_NAME.match(name) or name in (".", "..")):
        raise ValueError("Repository names use letters, digits, '.', '_' and '-'")
    return name


class NewRepo(BaseModel):
    """Create a private repository for a new project when its work is released."""

    name: str | None = Field(default=None, max_length=100)  # None: from the request

    @field_validator("name")
    @classmethod
    def _github_name(cls, name: str | None) -> str | None:
        return check_repo_name(name)


class DeliveryStatus(StrEnum):
    OPENED = "opened"  # a pull request is open with the work
    CREATED = "created"  # a new repository holds the work (new projects)
    NO_CHANGES = "no_changes"  # nothing to deliver
    SKIPPED = "skipped"  # couldn't deliver (e.g. no GitHub token); the reason says why


class Delivery(BaseModel):
    """How released work went back to the founder's repository."""

    status: DeliveryStatus
    branch: str = ""
    commit: str = ""
    pull_request_url: str = ""
    repo_url: str = ""  # the repository the work went to (set for created ones)
    reason: str = ""
