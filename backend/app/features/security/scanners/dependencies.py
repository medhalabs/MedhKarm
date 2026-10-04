"""Known-vulnerable dependencies, only when the run changed a dependency file: pip-audit for
Python requirements, npm audit for Node projects with a lockfile. Both need the network."""

import json
import shlex
from pathlib import PurePosixPath
from typing import Any

from app.features.sandbox.interfaces import Sandbox
from app.features.security.schemas import Finding, ScanResult, Severity

TIMEOUT = 240
NPM_SEVERITY = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "moderate": Severity.MEDIUM,
    "low": Severity.LOW,
}


def parse_pip_audit(output: str, path: str) -> list[Finding]:
    try:
        data: Any = json.loads(output[output.find("{") :])
    except (json.JSONDecodeError, ValueError):
        return []
    findings = []
    for dep in data.get("dependencies", []) if isinstance(data, dict) else []:
        for vuln in dep.get("vulns", []):
            fixes = vuln.get("fix_versions") or []
            findings.append(
                Finding(
                    tool="pip-audit",
                    rule=str(vuln.get("id", "vulnerability")),
                    # a fixed version exists: upgrading is the fix, so don't release without it
                    severity=Severity.HIGH if fixes else Severity.MEDIUM,
                    path=path,
                    message=f"{dep.get('name')} {dep.get('version')} has a known "
                    f"vulnerability ({vuln.get('id')}).",
                    fix=f"Upgrade to {fixes[-1]} or later." if fixes else "",
                )
            )
    return findings


def parse_npm_audit(output: str, path: str) -> list[Finding]:
    try:
        data: Any = json.loads(output[output.find("{") :])
    except (json.JSONDecodeError, ValueError):
        return []
    findings = []
    vulns = data.get("vulnerabilities", {}) if isinstance(data, dict) else {}
    for name, vuln in vulns.items():
        severity = NPM_SEVERITY.get(str(vuln.get("severity", "")), Severity.MEDIUM)
        fix = vuln.get("fixAvailable")
        findings.append(
            Finding(
                tool="npm-audit",
                rule=f"npm:{name}",
                severity=severity,
                path=path,
                message=f"{name} has a known {vuln.get('severity', '')} vulnerability.",
                fix="Run `npm audit fix` or upgrade it." if fix else "",
            )
        )
    return findings


class DependencyScanner:
    name = "dependencies"

    async def scan(self, sandbox: Sandbox, changed: list[str]) -> ScanResult:
        result = ScanResult()
        for path in changed:
            name = PurePosixPath(path).name
            if name.startswith("requirements") and name.endswith(".txt"):
                await self._pip(sandbox, path, result)
            elif name in ("package.json", "package-lock.json"):
                folder = str(PurePosixPath(path).parent)
                if any(r.path.startswith(folder) for r in result.findings if r.tool == "npm-audit"):
                    continue
                await self._npm(sandbox, folder, result)
        return result

    async def _pip(self, sandbox: Sandbox, path: str, result: ScanResult) -> None:
        if not (await sandbox.run("command -v pip-audit")).ok:
            result.notes.append("pip-audit isn't in this sandbox: Python dependencies not checked")
            return
        out = await sandbox.run(
            f"pip-audit -r {shlex.quote(path)} --format json --progress-spinner off 2>/dev/null",
            timeout_seconds=TIMEOUT,
        )
        if not out.output.strip():
            result.notes.append(f"pip-audit couldn't check {path} (exit {out.exit_code})")
        result.findings.extend(parse_pip_audit(out.output, path))

    async def _npm(self, sandbox: Sandbox, folder: str, result: ScanResult) -> None:
        lock = f"{folder}/package-lock.json" if folder not in ("", ".") else "package-lock.json"
        if not (await sandbox.run(f"test -f {shlex.quote(lock)}")).ok:
            result.notes.append(f"No package-lock.json in {folder or '.'}: npm audit skipped")
            return
        out = await sandbox.run(
            f"cd {shlex.quote(folder or '.')} && npm audit --json 2>/dev/null",
            timeout_seconds=TIMEOUT,
        )
        result.findings.extend(parse_npm_audit(out.output, lock))
