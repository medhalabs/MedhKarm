import json

from app.features.sandbox.providers.memory_provider import InMemorySandbox
from app.features.sandbox.schemas import CommandResult
from app.features.security.scanners.dependencies import (
    DependencyScanner,
    parse_npm_audit,
    parse_pip_audit,
)
from app.features.security.scanners.secrets import SecretsScanner, find_secrets
from app.features.security.scanners.semgrep import SemgrepScanner, parse_semgrep
from app.features.security.schemas import Severity
from app.features.security.service import SecurityReview

GITHUB = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"


def sandbox(files: dict[str, str], answer: str = "", ok: bool = True) -> InMemorySandbox:
    box = InMemorySandbox("sb", lambda c, f: CommandResult(exit_code=0 if ok else 1, output=answer))
    box.files.update(files)
    return box


def test_finds_real_looking_secrets_and_ignores_placeholders() -> None:
    text = "\n".join(
        [
            f'TOKEN = "{GITHUB}"',
            'api_key = "your_api_key_here_12345"',
            'stripe_secret = "Zq8rT2vX9mK4pL7wN3bY6cJ1"',
            'password = "aaaaaaaaaaaaaaaaaaaa"',  # low entropy
            "-----BEGIN RSA PRIVATE KEY-----",
        ]
    )

    found = {(f.rule, f.line, f.severity) for f in find_secrets("app.py", text)}

    assert found == {
        ("github-token", 1, Severity.CRITICAL),
        ("hardcoded-secret", 3, Severity.HIGH),
        ("private-key", 5, Severity.CRITICAL),
    }


async def test_secrets_scanner_flags_env_files_and_reads_changed_files_only() -> None:
    box = sandbox({"config.py": f'KEY = "{GITHUB}"', "old.py": f'KEY = "{GITHUB}"', ".env": "A=1"})

    result = await SecretsScanner().scan(box, ["config.py", ".env"])

    assert sorted((f.path, f.rule) for f in result.findings) == [
        (".env", "secret-file"),
        ("config.py", "github-token"),
    ]


def test_semgrep_report() -> None:
    report = {
        "results": [
            {
                "check_id": "opt.medhkarm.py-shell-true",
                "path": "run.py",
                "start": {"line": 7},
                "extra": {
                    "severity": "ERROR",
                    "message": "shell injection",
                    "metadata": {"fix": "use a list"},
                },
            },
            {
                "check_id": "x.py-weak-hash",
                "path": "h.py",
                "start": {"line": 2},
                "extra": {"severity": "WARNING", "message": "md5"},
            },
        ]
    }

    findings = parse_semgrep("noise\n" + json.dumps(report))

    assert [(f.rule, f.severity, f.line, f.fix) for f in findings] == [
        ("py-shell-true", Severity.HIGH, 7, "use a list"),
        ("py-weak-hash", Severity.MEDIUM, 2, ""),
    ]
    assert parse_semgrep("not json") == []


async def test_semgrep_skips_non_code_and_missing_tools() -> None:
    assert (await SemgrepScanner().scan(sandbox({}), ["README.md"])).findings == []
    missing = await SemgrepScanner().scan(sandbox({}, ok=False), ["app.py"])
    assert missing.notes == ["Semgrep or its rules aren't in this sandbox: code not scanned"]


def test_dependency_reports() -> None:
    pip = {
        "dependencies": [
            {
                "name": "jinja2",
                "version": "2.10",
                "vulns": [{"id": "GHSA-1", "fix_versions": ["2.11.3"]}],
            },
            {"name": "abc", "version": "1.0", "vulns": [{"id": "PYSEC-2", "fix_versions": []}]},
            {"name": "ok", "version": "1.0", "vulns": []},
        ]
    }
    npm = {"vulnerabilities": {"lodash": {"severity": "critical", "fixAvailable": True}}}

    py = parse_pip_audit(json.dumps(pip), "requirements.txt")
    js = parse_npm_audit(json.dumps(npm), "package-lock.json")

    assert [(f.rule, f.severity, f.fix) for f in py] == [
        ("GHSA-1", Severity.HIGH, "Upgrade to 2.11.3 or later."),
        ("PYSEC-2", Severity.MEDIUM, ""),
    ]
    assert [(f.rule, f.severity) for f in js] == [("npm:lodash", Severity.CRITICAL)]


async def test_dependencies_are_checked_only_when_a_manifest_changed() -> None:
    commands: list[str] = []

    def shell(command: str, files: dict[str, str]) -> CommandResult:
        commands.append(command)
        return CommandResult(exit_code=0, output='{"dependencies": []}')

    box = InMemorySandbox("sb", shell)

    await DependencyScanner().scan(box, ["app.py"])
    assert commands == []
    await DependencyScanner().scan(box, ["requirements.txt"])
    assert any(c.startswith("pip-audit -r requirements.txt") for c in commands)


async def test_a_broken_scanner_becomes_a_note() -> None:
    class Broken:
        name = "broken"

        async def scan(self, sandbox: InMemorySandbox, changed: list[str]) -> None:
            raise RuntimeError("boom")

    report = await SecurityReview([Broken(), SecretsScanner()]).review(  # type: ignore[list-item]
        sandbox({"a.py": f'K = "{GITHUB}"'}), ["a.py"]
    )

    assert report.notes == ["broken failed: RuntimeError"]
    assert len(report.blocking) == 1
