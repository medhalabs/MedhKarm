VALUES = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]


def to_roman(n: int) -> str:
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 3999:
        raise ValueError("n must be an int from 1 to 3999")
    out = []
    for value, symbol in VALUES:
        count, n = divmod(n, value)
        out.append(symbol * count)
    return "".join(out)


_LOOKUP = {to_roman(n): n for n in range(1, 4000)}


def from_roman(s: str) -> int:
    if s not in _LOOKUP:
        raise ValueError(f"Invalid Roman numeral: {s!r}")
    return _LOOKUP[s]
