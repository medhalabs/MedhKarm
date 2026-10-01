"""Detects which files an engine created or modified, by hashing the workspace before and after."""

from app.features.sandbox.interfaces import Sandbox

HASH_COMMAND = (
    "find . -type f -not -path '*/.*' -not -path '*/__pycache__/*' -exec sha1sum {} + "
    "2>/dev/null | sed 's|  ./|  |'"
)


async def snapshot(sandbox: Sandbox) -> dict[str, str]:
    """Map of workspace-relative path → content hash."""
    result = await sandbox.run(HASH_COMMAND)
    files: dict[str, str] = {}
    for line in result.output.splitlines():
        digest, _, path = line.partition("  ")
        if digest and path:
            files[path] = digest
    return files


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Files that are new or whose content changed (deleted files are not listed)."""
    return sorted(path for path, digest in after.items() if before.get(path) != digest)
