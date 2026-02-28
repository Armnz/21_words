import unicodedata

from django.db.models import Q


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


def rule_to_q(rule: dict) -> Q:
    """
    Convert a rule dict into a Django Q object that can be used to filter
    `Word` objects by their `word` field. This allows counting matches in SQL.
    Returns an empty Q() that matches nothing if the rule is invalid.
    """
    if not rule or "type" not in rule:
        return Q(pk__in=[])  # matches nothing

    typ = rule.get("type")
    val = rule.get("value") or ""
    if isinstance(val, str):
        val = normalize_word(val)

    if typ == "starts_with":
        return Q(word__startswith=val)
    if typ == "ends_with":
        return Q(word__endswith=val)
    if typ == "contains":
        return Q(word__contains=val)
    if typ == "contains_double":
        return Q(word__contains=val)
    if typ == "contains_diacritic":
        diacritics = list("āčēģīķļņšūž")
        q = Q(pk__in=[])
        for ch in diacritics:
            q = q | Q(word__contains=ch)
        return q

    return Q(pk__in=[])
