"""The founder's stack choices, the stack a run uses, and the starter catalog."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Source = Literal["founder", "request", "team"]  # who decided: the form, the request's words, us
Layout = Literal["single", "split"]  # one project at the root, or web/ + api/
FIELDS = ("frontend", "api", "database", "hosting", "payments")


class StackChoice(BaseModel):
    """What the founder picked in the form. Anything left empty, the team decides (from the
    request's words first, then our defaults). Free text is fine: an unknown name is followed,
    with the founder's notes (links to its docs), instead of a ready-made part."""

    frontend: str | None = Field(default=None, max_length=40)  # "nextjs", "none", "vue", …
    api: str | None = Field(default=None, max_length=40)  # "nextjs", "python", "java", …
    database: str | None = Field(default=None, max_length=40)  # "supabase", "postgres", …
    hosting: str | None = Field(default=None, max_length=40)  # "vercel", "docker", "aws", …
    payments: str | None = Field(default=None, max_length=40)  # "razorpay", "stripe", "none", …
    modules: list[str] | None = None  # None: picked from the request
    starter: bool | None = None  # None: use a starter when the request is an app; False: never
    notes: str = Field(default="", max_length=3000)  # docs, links, anything about the stack

    @field_validator("frontend", "api", "database", "hosting", "payments")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        cleaned = (value or "").strip().lower()
        return None if cleaned in ("", "auto", "any", "team") else cleaned

    @property
    def empty(self) -> bool:
        return not any(getattr(self, f) for f in FIELDS) and self.modules is None


class Stack(BaseModel):
    """The stack a run builds on, every choice filled in, and who decided each one."""

    frontend: str
    api: str
    database: str
    hosting: str
    payments: str
    sources: dict[str, Source] = Field(default_factory=dict)
    starter: str | None = None  # "nextjs" | "fastapi" | None (no ready-made starter)
    layout: Layout | None = None
    modules: list[str] = Field(default_factory=list)
    custom: list[str] = Field(default_factory=list)  # choices the team builds without our parts
    rules: str = ""  # the starter's rules for developers
    notes: str = ""

    def table(self) -> str:
        rows = [f"| {f} | {getattr(self, f)} | {self.sources.get(f, 'team')} |" for f in FIELDS]
        return "\n".join(["| Part | Choice | Chosen by |", "| --- | --- | --- |", *rows])

    def brief(self) -> str:
        """For the CTO and the developers."""
        chosen = ", ".join(
            f"{f}: {getattr(self, f)}"
            + (" (founder's choice)" if self.sources.get(f) == "founder" else "")
            for f in FIELDS
        )
        lines = [f"Stack: {chosen}."]
        if self.starter:
            where = "web/ (Next.js) and api/ (Python)" if self.layout == "split" else "the root"
            lines.append(
                f"The project starts from our tested {self.starter} starter at {where}"
                + (f" with ready-made modules: {', '.join(self.modules)}" if self.modules else "")
                + ". Read AGENTS.md first; build on these parts instead of rewriting them."
            )
            if self.rules:
                lines.append("Rules for this project:\n" + self.rules.strip())
        for item in self.custom:
            lines.append(f"- {item}")
        if self.notes:
            lines.append("The founder's notes about the stack (follow them):\n" + self.notes)
        return "\n".join(lines)


class StarterSpec(BaseModel):
    name: str
    title: str
    description: str
    setup_command: str
    test_command: str
    rules: str = ""  # what every developer must follow, put in their brief


class ModuleSpec(BaseModel):
    name: str
    title: str
    description: str
    starters: list[str]
    requires: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    env: str = ""  # lines for .env.example ({{payments}} etc. filled in)
    guide: str = ""  # how to use it, for AGENTS.md


class HostingSpec(BaseModel):
    name: str
    hosts: list[str]
    dir: str  # extra files, relative to the starter's folder


class ScaffoldResult(BaseModel):
    """What the scaffold step put in the workspace."""

    starter: str
    layout: Layout
    modules: list[str]
    files: list[str]
    setup_command: str
    test_command: str
    setup_ok: bool
    setup_output: str = ""
