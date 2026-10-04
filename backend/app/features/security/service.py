"""The security engineer's review: every scanner over the files a run changed. A scanner that
breaks becomes a note, never a failed run."""

import logging

from app.features.sandbox.interfaces import Sandbox
from app.features.security.interfaces import Scanner
from app.features.security.scanners.dependencies import DependencyScanner
from app.features.security.scanners.secrets import SecretsScanner
from app.features.security.scanners.semgrep import SemgrepScanner
from app.features.security.schemas import SecurityReport

logger = logging.getLogger(__name__)


def default_scanners() -> list[Scanner]:
    return [SecretsScanner(), SemgrepScanner(), DependencyScanner()]


class SecurityReview:
    def __init__(self, scanners: list[Scanner] | None = None) -> None:
        self._scanners = default_scanners() if scanners is None else scanners

    async def review(self, sandbox: Sandbox, changed: list[str]) -> SecurityReport:
        report = SecurityReport(scanned_files=len(changed))
        for scanner in self._scanners:
            try:
                result = await scanner.scan(sandbox, changed)
            except Exception as error:
                logger.exception("Security scanner %s failed", scanner.name)
                report.notes.append(f"{scanner.name} failed: {type(error).__name__}")
                continue
            report.findings.extend(result.findings)
            report.notes.extend(result.notes)
        return report
