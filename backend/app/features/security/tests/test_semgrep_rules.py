"""Our Semgrep rules, run for real in the sandbox image. Needs Docker and medhkarm-sandbox:2;
run with `uv run pytest -m integration app/features/security`."""

import pytest

from app.core.config import get_settings
from app.features.sandbox.providers.docker_provider import DockerSandboxProvider
from app.features.security.scanners.semgrep import SemgrepScanner

pytestmark = pytest.mark.integration

BAD = """import subprocess, yaml
def run(cmd, data, cur, name):
    subprocess.run(cmd, shell=True)
    yaml.load(data)
    cur.execute(f"SELECT * FROM t WHERE name = '{name}'")
"""
GOOD = """import subprocess, yaml
def run(args, data, cur, name):
    subprocess.run(["ls", args])
    yaml.safe_load(data)
    cur.execute("SELECT * FROM t WHERE name = ?", (name,))
"""


async def test_rules_catch_bad_code_and_leave_safe_code_alone() -> None:
    provider = DockerSandboxProvider(get_settings().sandbox_image)
    sandbox = await provider.create()
    try:
        await sandbox.write_file("bad.py", BAD)
        await sandbox.write_file("good.py", GOOD)

        result = await SemgrepScanner().scan(sandbox, ["bad.py", "good.py"])
    finally:
        await provider.destroy(sandbox.id)

    assert sorted((f.path, f.rule) for f in result.findings) == [
        ("bad.py", "py-shell-true"),
        ("bad.py", "py-sql-built-from-strings"),
        ("bad.py", "py-yaml-unsafe-load"),
    ]
    assert all(f.blocking for f in result.findings)
