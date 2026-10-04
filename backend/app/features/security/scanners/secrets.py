"""Leaked secrets in the changed files: API keys, tokens, private keys, committed .env files.
Pure Python over the files' text: offline, no tools needed in the sandbox."""

import math
import re
from pathlib import PurePosixPath

from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox
from app.features.security.schemas import Finding, ScanResult, Severity

MAX_BYTES = 200_000
FIX = "Remove it, rotate the key, and read it from an environment variable."

# (rule, pattern, what it is)
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "A private key",
    ),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "An AWS access key"),
    (
        "github-token",
        re.compile(
            r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b"
        ),
        "A GitHub token",
    ),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"), "An OpenAI-style API key"),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}\b"), "An Anthropic API key"),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "A Google API key"),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "A Slack token"),
    ("stripe-key", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{20,}\b"), "A live Stripe key"),
    ("razorpay-key", re.compile(r"\brzp_live_[0-9A-Za-z]{14,}\b"), "A live Razorpay key"),
]
ASSIGNED = re.compile(
    r"""(?ix)\b([a-z0-9_]*(?:api[_-]?key|secret|token|passw(?:or)?d|access[_-]?key)[a-z0-9_]*)
        \s*[:=]\s*["']([^"'\s]{16,})["']"""
)
PLACEHOLDER = re.compile(
    r"(?i)example|your[_-]|xxx|changeme|dummy|placeholder|fake|test|sample|<|\$\{"
)
SECRET_FILES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}


def entropy(text: str) -> float:
    """Shannon entropy per character: random keys score high, words and paths low."""
    counts = {c: text.count(c) for c in set(text)}
    return -sum(n / len(text) * math.log2(n / len(text)) for n in counts.values())


def find_secrets(path: str, text: str) -> list[Finding]:
    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        for rule, pattern, what in PATTERNS:
            match = pattern.search(line)
            if match and not PLACEHOLDER.search(match.group(0)):
                findings.append(
                    Finding(
                        tool="secrets",
                        rule=rule,
                        severity=Severity.CRITICAL,
                        path=path,
                        line=n,
                        message=f"{what} is written in the code.",
                        fix=FIX,
                    )
                )
        for match in ASSIGNED.finditer(line):
            name, value = match.group(1), match.group(2)
            if PLACEHOLDER.search(value) or entropy(value) < 3.5:
                continue
            if any(f.line == n for f in findings):
                continue
            findings.append(
                Finding(
                    tool="secrets",
                    rule="hardcoded-secret",
                    severity=Severity.HIGH,
                    path=path,
                    line=n,
                    message=f"`{name}` looks like a real secret written in the code.",
                    fix=FIX,
                )
            )
    return findings


class SecretsScanner:
    name = "secrets"

    async def scan(self, sandbox: Sandbox, changed: list[str]) -> ScanResult:
        findings: list[Finding] = []
        for path in changed:
            if PurePosixPath(path).name in SECRET_FILES:
                findings.append(
                    Finding(
                        tool="secrets",
                        rule="secret-file",
                        severity=Severity.CRITICAL,
                        path=path,
                        message="A secrets file would be committed.",
                        fix="Delete it from the work and keep it out with .gitignore.",
                    )
                )
                continue
            try:
                text = await sandbox.read_file(path)
            except SandboxError:  # deleted, binary or unreadable
                continue
            if len(text) <= MAX_BYTES:
                findings.extend(find_secrets(path, text))
        return ScanResult(findings=findings)
