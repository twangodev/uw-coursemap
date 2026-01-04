"""Data utilities for search service."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize a text string by lowercasing, removing accents, punctuation, and extra whitespace.
    """
    if not text:
        return ""
    # Normalize Unicode characters to ASCII
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Remove punctuation and extra whitespace, then lowercase
    text = re.sub(r"[^\w\s]", "", text)
    text = text.lower().strip()
    return text