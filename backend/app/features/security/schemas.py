"""What the security engineer (Vikram) finds in a release, and how serious it is."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "low"  # listed only
    MEDIUM = "medium"  # a warning: shown to the founder at the release gate
    HIGH = "high"  # blocks the release until fixed
    CRITICAL = "critical"  # blocks the release until fixed (e.g. a leaked secret)


BLOCKING = (Severity.HIGH, Severity.CRITICAL)


class Finding(BaseModel):
    tool: str  # "secrets", "semgrep", "pip-audit", "npm-audit"
    rule: str  # what was matched, e.g. "github-token" or a Semgrep rule id
    severity: Severity
    path: str = ""
    line: int = 0
    message: str  # one plain sentence
    fix: str = ""  # how to fix it, when known

    @property
    def blocking(self) -> bool:
        return self.severity in BLOCKING

    def line_text(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        fix = f" Fix: {self.fix}" if self.fix else ""
        return f"[{self.severity}] {where} {self.message}{fix}".replace("  ", " ")


class ScanResult(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)  # e.g. "semgrep isn't installed: skipped"


class SecurityReport(ScanResult):
    scanned_files: int = 0

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.blocking]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.MEDIUM]

    def brief(self, limit: int = 20) -> str:
        """The blocking findings as a task description for a developer."""
        lines = [f.line_text() for f in self.blocking[:limit]]
        more = len(self.blocking) - limit
        return "\n".join(
            [
                "The security engineer found these problems. Fix each one without breaking "
                "the tests; never commit secrets (read them from environment variables).",
                *(f"- {line}" for line in lines),
                *([f"- … and {more} more"] if more > 0 else []),
            ]
        )
