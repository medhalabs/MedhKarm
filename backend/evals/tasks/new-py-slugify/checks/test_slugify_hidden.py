import pytest

from slugify import slugify


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello, World!", "hello-world"),
        ("  Multiple   spaces ", "multiple-spaces"),
        ("", ""),
        ("---", ""),
        ("Python 3.13 is out", "python-3-13-is-out"),
        ("Café au lait", "caf-au-lait"),
        ("already-a-slug", "already-a-slug"),
    ],
)
def test_slugify(text, expected):
    assert slugify(text) == expected
