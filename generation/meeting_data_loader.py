"""
Meeting data loading module.
Handles fetching meeting data from URLs and other sources.
"""

import json
from typing import List, Dict, Optional

import requests
import requests_cache


class MeetingDataLoader:
    """Handles loading meeting data from various sources."""

    # Initialize requests-cache session
    _session = requests_cache.CachedSession(
        cache_name='meeting_cache',
        backend='memory',
        expire_after=None,  # Respect Cache-Control headers
        allowable_codes=[200, 404]  # Cache successful responses and 404s
    )

    @classmethod
    def load_from_url(cls, url: str) -> Optional[List[Dict]]:
        """
        Load meetings data from a URL with Cache-Control header respect.

        Args:
            url: URL to fetch meeting data from

        Returns:
            List of meeting dictionaries, None if 404 or other HTTP error
        """

        try:
            headers = {
                'User-Agent': 'UW-CourseMap/1.0 (https://uwcourses.com)'
            }
            response = cls._session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            print(f"HTTP error loading meetings from {url}: {e}")
            return []
        except Exception as e:
            print(f"Error loading meetings from {url}: {e}")
            return []

    @staticmethod
    def load_from_file(file_path: str) -> List[Dict]:
        """
        Load meetings data from a local file.

        Args:
            file_path: Path to the JSON file

        Returns:
            List of meeting dictionaries, empty list on error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading meetings from {file_path}: {e}")
            return []


# Backward compatibility function
def load_meetings_from_url(url: str) -> Optional[List[Dict]]:
    """Load meetings data from a URL (backward compatibility)."""
    return MeetingDataLoader.load_from_url(url)