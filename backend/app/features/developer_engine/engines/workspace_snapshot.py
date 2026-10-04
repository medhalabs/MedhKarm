"""Detects which files an engine created or modified, by hashing the workspace before and after."""

from app.features.sandbox.interfaces import Sandbox

# The project's own files: dependencies and caches (node_modules, venv, __pycache__, hidden
# folders) are skipped, so installing a package doesn't "change" thousands of files.
HASH_COMMAND = (
    "find . \\( -name node_modules -o -name __pycache__ -o -name venv -o -name '.?*' \\)"
    " -prune -o -type f -exec sha1sum {} + 2>/dev/null | sed 's|  ./|  |'"
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
