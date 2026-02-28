from game.services.validation import matches_rule, normalize_word


def test_normalize_word_nfc_and_lower_and_strip():
    # contains surrounding spaces and uppercase and composed letters
    raw = "  Ābols "
    n = normalize_word(raw)
    assert n == "ābols"


def test_matches_rule_starts_with():
    assert matches_rule("ābols", {"type": "starts_with", "value": "ā"})
    assert not matches_rule("ābols", {"type": "starts_with", "value": "b"})


def test_matches_rule_contains_diacritic():
    assert matches_rule("šokolāde", {"type": "contains_diacritic"})
    assert not matches_rule("skola", {"type": "contains_diacritic"})
