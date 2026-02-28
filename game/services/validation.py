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
