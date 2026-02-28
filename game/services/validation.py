import unicodedata


def normalize_word(text: str) -> str:
    """
    Normalize a word for storage and comparison.
    - Strips whitespace
    - Unicode normalize to NFC
    - Lowercase (case-insensitive comparison)
    - Does NOT remove diacritics (é, ñ, etc. are preserved)
    """
    text = text.strip()
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    return text


def matches_rule(normalized_word: str, rule: dict) -> bool:
    """
    Determine if a normalized word matches the given rule dict.
    Supported rule types:
      - starts_with: {'type':'starts_with','value':'a'}
      - ends_with: {'type':'ends_with','value':'s'}
      - contains: {'type':'contains','value':'ie'}
      - contains_double: {'type':'contains_double','value':'ll'}
      - contains_diacritic: {'type':'contains_diacritic'}

    Expects `normalized_word` already NFC-normalized and lowercased.
    """
    if not rule or "type" not in rule:
        return False
    typ = rule.get("type")
    val = rule.get("value") or ""

    if typ == "starts_with":
        return normalized_word.startswith(val)
    if typ == "ends_with":
        return normalized_word.endswith(val)
    if typ == "contains":
        return val in normalized_word
    if typ == "contains_double":
        # check for the double substring
        return val in normalized_word
    if typ == "contains_diacritic":
        # Latvian diacritic letters (lowercase)
        diacritics = set("āčēģīķļņšūž")
        return any(ch in diacritics for ch in normalized_word)

    return False
