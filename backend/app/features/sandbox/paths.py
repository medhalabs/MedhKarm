from pathlib import PurePosixPath

from app.features.sandbox.exceptions import UnsafePathError


def safe_relative_path(path: str) -> str:
    """Normalise a workspace-relative path and refuse anything that escapes the workspace."""
    candidate = PurePosixPath(path.strip())
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise UnsafePathError(f"Path must stay inside the workspace: {path!r}")
    return str(candidate)
