"""Parser and applier for the `apply_patch` format that OpenAI models (gpt-oss, Codex) are
trained to write:

    *** Begin Patch
    *** Add File: path/new.py
    +line one
    *** Update File: path/old.py
    *** Move to: path/renamed.py          (optional)
    @@ def some_function():               (optional anchor: jump to this line first)
     context line
    -removed line
    +added line
    *** Delete File: path/gone.py
    *** End Patch

Pure functions only; running a patch against a sandbox lives in tools.py.
"""

from dataclasses import dataclass, field
from typing import Literal

BEGIN, END = "*** Begin Patch", "*** End Patch"
ADD, UPDATE, DELETE, MOVE = (
    "*** Add File: ",
    "*** Update File: ",
    "*** Delete File: ",
    "*** Move to: ",
)
END_OF_FILE = "*** End of File"


class PatchError(ValueError):
    """The patch is malformed or doesn't match the file. The message goes back to the model."""


@dataclass
class Hunk:
    anchor: str | None = None  # text after "@@", if any
    lines: list[str] = field(default_factory=list)  # each starts with " ", "-" or "+"


@dataclass
class FileOp:
    kind: Literal["add", "update", "delete"]
    path: str
    move_to: str | None = None
    content: str = ""  # for add
    hunks: list[Hunk] = field(default_factory=list)  # for update


def extract_patch(text: str) -> str:
    """The patch between Begin/End markers, dropping shell wrappers like `apply_patch <<'EOF'`."""
    start, end = text.find(BEGIN), text.rfind(END)
    if start == -1 or end == -1 or end < start:
        raise PatchError(f"Patch must start with '{BEGIN}' and end with '{END}'.")
    return text[start : end + len(END)]


def parse_patch(text: str) -> list[FileOp]:
    lines = extract_patch(text).splitlines()
    ops: list[FileOp] = []
    for line in lines:
        if line.strip() in (BEGIN, END):
            continue  # models repeat markers, or send several patches in one; skip them all
        if line.startswith(ADD):
            ops.append(FileOp("add", line[len(ADD) :].strip()))
        elif line.startswith(DELETE):
            ops.append(FileOp("delete", line[len(DELETE) :].strip()))
        elif line.startswith(UPDATE):
            ops.append(FileOp("update", line[len(UPDATE) :].strip()))
        elif not ops:
            raise PatchError(f"Expected a file header, got: {line!r}")
        else:
            _add_body_line(ops[-1], line)
    if not ops:
        raise PatchError("Patch contains no file operations.")
    return ops


def _add_body_line(op: FileOp, line: str) -> None:
    if op.kind == "add":
        if not line.startswith("+"):
            raise PatchError(f"Lines of an added file must start with '+': {line!r}")
        op.content += line[1:] + "\n"
    elif op.kind == "update":
        if line.startswith(MOVE):
            op.move_to = line[len(MOVE) :].strip()
        elif line.startswith("@@"):
            op.hunks.append(Hunk(anchor=line[2:].strip() or None))
        elif line.strip() == END_OF_FILE:
            return
        else:
            if not op.hunks:
                op.hunks.append(Hunk())
            if line == "":
                line = " "  # a blank context line whose leading space got stripped
            if line[0] not in " -+":
                raise PatchError(f"Hunk lines must start with ' ', '-' or '+': {line!r}")
            op.hunks[-1].lines.append(line)
    else:
        raise PatchError(f"'Delete File' takes no body lines: {line!r}")


def apply_hunks(original: str, hunks: list[Hunk], path: str) -> str:
    """Apply hunks in order. Each hunk's context and removed lines must appear in the file."""
    lines = original.splitlines()
    cursor = 0
    for number, hunk in enumerate(hunks, start=1):
        if hunk.anchor:
            found = _find(lines, [hunk.anchor], cursor)
            if found is not None:
                cursor = found
        old = [line[1:] for line in hunk.lines if line[0] in " -"]
        new = [line[1:] for line in hunk.lines if line[0] in " +"]
        if not old:  # pure insertion: append at the anchor or end of file
            insert_at = cursor + 1 if hunk.anchor else len(lines)
            lines[insert_at:insert_at] = new
            cursor = insert_at + len(new)
            continue
        at = _find(lines, old, cursor)
        if at is None:
            at = _find(lines, old, 0)  # hunks out of order: search from the top
        if at is None:
            preview = "\n".join(old[:5])
            raise PatchError(
                f"Hunk {number} for {path} doesn't match the file. Expected these lines:\n{preview}"
                "\nRead the file and try again with exact context."
            )
        lines[at : at + len(old)] = new
        cursor = at + len(new)
    return "\n".join(lines) + ("\n" if lines else "")


def _find(lines: list[str], block: list[str], start: int) -> int | None:
    """Where `block` appears at or after `start`; exact match first, then ignoring end spaces."""
    for strip in (False, True):
        target = [_norm(b, strip) for b in block]
        for i in range(start, len(lines) - len(block) + 1):
            if [_norm(x, strip) for x in lines[i : i + len(block)]] == target:
                return i
    return None


def _norm(line: str, strip: bool) -> str:
    return line.rstrip() if strip else line
