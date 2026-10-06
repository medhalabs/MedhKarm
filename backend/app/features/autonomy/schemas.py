"""How much the team does on its own: the founder's dial, in plain terms. It is turned into
the approval rules the release gate evaluates (policy.py)."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Level(StrEnum):
    EVERY = "every"  # every release waits for the founder (the default)
    SMALL = "small"  # small, clean changes go out on their own
    CHECKS = "checks"  # anything goes out on its own once every check passes


class AutonomySettings(BaseModel):
    level: Level = Level.EVERY
    small_files: int = Field(default=3, ge=1, le=15)  # "small" means this many files or fewer

    # Things that still ask the founder, whatever the level. On by default.
    ask_sensitive_files: bool = True  # secrets, dependencies, database, deployment settings
    ask_open_comments: bool = True  # the CTO accepted a task with review comments still open
    ask_security_warnings: bool = True
    ask_preview_failed: bool = True
    ask_large_change: bool = True
    large_files: int = Field(default=15, ge=3, le=200)
    ask_expensive: bool = True
    max_tokens: int = Field(default=1_000_000, ge=50_000, le=50_000_000)

    # Files the team must never change: a release that touches one is stopped without asking.
    never_touch: list[str] = Field(default_factory=list, max_length=20)

    go_live: bool = True  # publish to the internet after a release (when deploys are set up)

    @field_validator("never_touch")
    @classmethod
    def _patterns(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for raw in value:
            pattern = raw.strip()
            if not pattern:
                continue
            if len(pattern) > 100 or pattern.startswith("/") or ".." in pattern:
                raise ValueError(
                    f"{pattern!r}: use a path or pattern inside the project, e.g. payments/*"
                )
            if pattern not in cleaned:
                cleaned.append(pattern)
        return cleaned


class Scope(StrEnum):
    COMPANY = "company"  # the default for everything
    PROJECT = "project"  # one project's own settings


class AutonomyView(BaseModel):
    scope: Scope
    project_id: str | None = None
    own: bool  # False: a project showing the company's settings (it has none of its own)
    settings: AutonomySettings
    summary: list[str]  # what these settings mean, in plain sentences
