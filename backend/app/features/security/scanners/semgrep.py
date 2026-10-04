"""Dangerous code patterns with Semgrep, using our own offline rules (sandbox-image/semgrep.yml,
baked into the sandbox image at RULES). Only the changed code files are scanned."""

import json
import shlex
from pathlib import PurePosixPath
from typing import Any

from app.features.sandbox.interfaces import Sandbox
from app.features.security.schemas import Finding, ScanResult, Severity

RULES = "/opt/medhkarm/semgrep.yml"
CODE = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
SEVERITY = {"ERROR": Severity.HIGH, "WARNING": Severity.MEDIUM, "INFO": Severity.LOW}
TIMEOUT = 180


def parse_semgrep(output: str) -> list[Finding]:
    """Semgrep's --json report as findings (unknown shapes give none)."""
    try:
        data: Any = json.loads(output[output.find("{") :])
    except (json.JSONDecodeError, ValueError):
        return []
    findings = []
    for result in data.get("results", []) if isinstance(data, dict) else []:
        extra = result.get("extra", {})
        rule = str(result.get("check_id", "semgrep")).rsplit(".", 1)[-1]
        findings.append(
            Finding(
                tool="semgrep",
                rule=rule,
                severity=SEVERITY.get(str(extra.get("severity", "")).upper(), Severity.MEDIUM),
                path=str(result.get("path", "")),
                line=int(result.get("start", {}).get("line", 0) or 0),
                message=str(extra.get("message", rule)).strip()[:300],
                fix=str(extra.get("metadata", {}).get("fix", ""))[:300],
            )
        )
    return findings


class SemgrepScanner:
    name = "semgrep"

    async def scan(self, sandbox: Sandbox, changed: list[str]) -> ScanResult:
        files = [p for p in changed if PurePosixPath(p).suffix in CODE]
        if not files:
            return ScanResult()
        check = await sandbox.run(f"command -v semgrep && test -f {RULES}")
        if not check.ok:
            return ScanResult(
                notes=["Semgrep or its rules aren't in this sandbox: code not scanned"]
            )
        quoted = " ".join(shlex.quote(f) for f in files)
        result = await sandbox.run(
            f"semgrep scan --config {RULES} --json --metrics=off --quiet "
            f"--disable-version-check {quoted} 2>/dev/null",
            timeout_seconds=TIMEOUT,
        )
        if not result.output.strip():
            return ScanResult(notes=[f"Semgrep gave no report (exit {result.exit_code})"])
        return ScanResult(findings=parse_semgrep(result.output))
