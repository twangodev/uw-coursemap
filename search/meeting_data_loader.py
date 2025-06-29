"""
Meeting data loading module.
Handles fetching meeting data from URLs and other sources.
"""

import json
from typing import List, Dict, Optional

import requests
from cachetools import TTLCache


class MeetingDataLoader:
    """Handles loading meeting data from various sources."""
    
    _cache = TTLCache(maxsize=128, ttl=300)  # 5 minutes TTL, 128 max items
    
    @classmethod
    def load_from_url(cls, url: str) -> Optional[List[Dict]]:
        """
        Load meetings data from a URL with time-based caching.
        
        Args:
            url: URL to fetch meeting data from
            
        Returns:
            List of meeting dictionaries, None if 404 or other HTTP error
        """
        # Check cache first
        if url in cls._cache:
            return cls._cache[url]
        
        try:
            headers = {
                'User-Agent': 'UW-CourseMap/1.0 (https://uwcourses.com)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            cls._cache[url] = data
            return data
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                cls._cache[url] = None  # Cache 404s too
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