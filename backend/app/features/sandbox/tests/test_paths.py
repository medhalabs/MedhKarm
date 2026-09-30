import pytest

from app.features.sandbox.exceptions import UnsafePathError
from app.features.sandbox.paths import safe_relative_path


@pytest.mark.parametrize(
    ("path", "expected"),
    [("app.py", "app.py"), ("src/app.py", "src/app.py"), ("./src/app.py", "src/app.py")],
)
def test_accepts_workspace_paths(path: str, expected: str) -> None:
    assert safe_relative_path(path) == expected


@pytest.mark.parametrize("path", ["/etc/passwd", "../secret", "src/../../x", "", "   "])
def test_rejects_paths_outside_workspace(path: str) -> None:
    with pytest.raises(UnsafePathError):
        safe_relative_path(path)
