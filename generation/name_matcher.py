"""
Universal name matching utilities for instructor name resolution.

This module provides consistent name matching across all data sources:
- Faculty directory matching
- Rate My Professors matching
- Instructor merging from grade data

The matcher handles common edge cases:
- Name abbreviations (Bob vs Robert)
- Hyphenated names (Smith-Jones vs Smith)
- Accents and diacritics (García vs Garcia)
- Punctuation (O'Brien vs OBrien)
- Middle names and initials

Threshold Guidelines:
- 80+ = Conservative (fewer matches, fewer false positives) - RECOMMENDED for RMP
- 70-79 = Moderate (balanced)
- 60-69 = Permissive (more matches, more false positives)

The default threshold of 80 is intentionally conservative to prevent incorrect
Rate My Professors matches, which could damage professor reputations.
"""

import re
import unicodedata
from dataclasses import dataclass
from logging import getLogger
from typing import Any

from nameparser import HumanName
from rapidfuzz import fuzz

logger = getLogger(__name__)


@dataclass
class MatchResult:
    """Result of a name matching operation."""

    matched_item: Any | None
    """The matched item (string, dict, or other object), or None if no match."""

    confidence: float
    """Confidence score 0-100, where 100 is perfect match."""

    matched_name: str | None = None
    """The canonical name that was matched, if applicable."""

    @property
    def is_match(self) -> bool:
        """Whether a match was found."""
        return self.matched_item is not None


def normalize_name_component(name: str) -> str:
    """
    Normalize a name component for matching.

    Handles:
    - Case normalization (uppercase)
    - Accent removal (García → GARCIA)
    - Punctuation removal (O'Brien → OBRIEN, Smith-Jones → SMITHJONES)
    - Whitespace normalization

    Args:
        name: Name component to normalize

    Returns:
        Normalized name component
    """
    if not name:
        return ""

    # Convert to uppercase
    normalized = name.upper().strip()

    # Remove accents and diacritics
    # NFD = Canonical Decomposition (separates base char from accent)
    # Then filter out combining marks (category Mn)
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(char) != "Mn"
    )

    # Remove common punctuation in names
    # Apostrophes: O'Brien → OBRIEN
    # Hyphens: Smith-Jones → SMITHJONES
    # Periods: Jr. → JR
    normalized = re.sub(r"['\-\.]", "", normalized)

    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def parse_name(full_name: str) -> tuple[str, str]:
    """
    Parse a full name into first and last name components.

    Uses HumanName parser and applies normalization.

    Args:
        full_name: Full name string (e.g., "John Smith", "Smith, John", "Dr. John Smith")

    Returns:
        Tuple of (normalized_first_name, normalized_last_name)
    """
    parsed = HumanName(full_name)
    first = normalize_name_component(parsed.first)
    last = normalize_name_component(parsed.last)
    return first, last


def calculate_name_match_score(
    query_first: str,
    query_last: str,
    candidate_first: str,
    candidate_last: str,
    require_exact_last: bool = True,
) -> float:
    """
    Calculate match score between two parsed names.

    Args:
        query_first: Query first name (already normalized)
        query_last: Query last name (already normalized)
        candidate_first: Candidate first name (already normalized)
        candidate_last: Candidate last name (already normalized)
        require_exact_last: If True, requires exact last name match (returns 0 if no match)

    Returns:
        Match score 0-100, where 100 is perfect match
    """
    # Last name matching
    if require_exact_last:
        # Exact match required for last name
        if query_last != candidate_last:
            return 0.0
        last_score = 100.0
    else:
        # Fuzzy match for last name too
        last_score = fuzz.token_set_ratio(query_last, candidate_last)
        if last_score < 80:  # Minimum threshold for last name
            return 0.0

    # First name fuzzy matching
    # token_set_ratio handles:
    # - Partial matches (Bob vs Robert)
    # - Token reordering (John Michael vs Michael John)
    # - Extra tokens (John vs John A.)
    first_score = fuzz.token_set_ratio(query_first, candidate_first)

    # Weighted average: last name is more important
    # 70% first name, 30% last name
    final_score = (first_score * 0.7) + (last_score * 0.3)

    return final_score


def find_best_name_match(
    query_name: str,
    candidates: list[str],
    threshold: float = 80.0,
    require_exact_last: bool = True,
) -> MatchResult:
    """
    Find the best matching name from a list of candidate names.

    Args:
        query_name: Name to match
        candidates: List of candidate names
        threshold: Minimum confidence score (0-100) required for a match
        require_exact_last: If True, requires exact last name match

    Returns:
        MatchResult with the best matching candidate name
    """
    query_first, query_last = parse_name(query_name)

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        candidate_first, candidate_last = parse_name(candidate)

        score = calculate_name_match_score(
            query_first, query_last, candidate_first, candidate_last, require_exact_last
        )

        if score > best_score:
            best_score = score
            best_match = candidate

    # Only return match if it meets threshold
    if best_match is None or best_score < threshold:
        logger.debug(
            f"No match found for '{query_name}' (best score: {best_score:.2f}, threshold: {threshold})"
        )
        return MatchResult(matched_item=None, confidence=best_score)

    logger.debug(
        f"Matched '{query_name}' to '{best_match}' with confidence {best_score:.2f}"
    )
    return MatchResult(
        matched_item=best_match, confidence=best_score, matched_name=best_match
    )


def find_best_structured_match(
    query_name: str,
    candidates: list[dict],
    first_name_key: str = "firstName",
    last_name_key: str = "lastName",
    threshold: float = 80.0,
    require_exact_last: bool = True,
) -> MatchResult:
    """
    Find the best matching item from a list of structured candidates (e.g., RMP results).

    Args:
        query_name: Name to match
        candidates: List of candidate dictionaries with first/last name fields
        first_name_key: Key for first name in candidate dict
        last_name_key: Key for last name in candidate dict
        threshold: Minimum confidence score (0-100) required for a match
        require_exact_last: If True, requires exact last name match

    Returns:
        MatchResult with the best matching candidate dictionary
    """
    query_first, query_last = parse_name(query_name)

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        # Extract and normalize first/last names from structured data
        candidate_first = normalize_name_component(candidate.get(first_name_key, ""))
        candidate_last = normalize_name_component(candidate.get(last_name_key, ""))

        score = calculate_name_match_score(
            query_first, query_last, candidate_first, candidate_last, require_exact_last
        )

        if score > best_score:
            best_score = score
            best_match = candidate

    # Only return match if it meets threshold
    if best_match is None or best_score < threshold:
        logger.debug(
            f"No structured match found for '{query_name}' (best score: {best_score:.2f}, threshold: {threshold})"
        )
        return MatchResult(matched_item=None, confidence=best_score)

    matched_name = (
        f"{best_match.get(first_name_key, '')} {best_match.get(last_name_key, '')}"
    )
    logger.debug(
        f"Matched '{query_name}' to structured item '{matched_name}' with confidence {best_score:.2f}"
    )
    return MatchResult(
        matched_item=best_match, confidence=best_score, matched_name=matched_name
    )