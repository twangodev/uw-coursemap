"""
Sanitization utilities for generating safe filenames and identifiers.
"""

from typing import Union
from logging import getLogger
from anyascii import anyascii
from pathvalidate import validate_filename, ValidationError

logger = getLogger(__name__)


def sanitize_entry(entry: str) -> Union[str, None]:
    """Sanitize a string for use as a filename. Replaces / and spaces with underscores."""
    result = entry.replace("/", "_").replace(" ", "_")
    try:
        validate_filename(result)
    except ValidationError as e:
        logger.debug(f"Invalid filename '{result}': {e}. Not writing file.")
        return None
    return result


def sanitize_instructor_id(name: str) -> Union[str, None]:
    """Convert instructor name to uppercase URL-safe ID. e.g., "O'Brien Jr." → "OBRIEN_JR" """
    if not name:
        return None

    result = anyascii(name)
    result = result.replace("/", "_").replace(" ", "_").replace("'", "").replace(".", "").upper()

    try:
        validate_filename(result)
    except ValidationError as e:
        logger.debug(f"Invalid instructor ID '{result}': {e}. Skipping.")
        return None

    return result
