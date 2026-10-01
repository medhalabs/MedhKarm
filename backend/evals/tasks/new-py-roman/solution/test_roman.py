from roman import from_roman, to_roman


def test_basic():
    assert to_roman(1994) == "MCMXCIV"
    assert from_roman("MCMXCIV") == 1994
