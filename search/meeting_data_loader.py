"""
Meeting data loading module.
Handles fetching meeting data from URLs and other sources.
"""

import urllib.request
import json
from typing import List, Dict


class MeetingDataLoader:
    """Handles loading meeting data from various sources."""
    
    @staticmethod
    def load_from_url(url: str) -> List[Dict]:
        """
        Load meetings data from a URL.
        
        Args:
            url: URL to fetch meeting data from
            
        Returns:
            List of meeting dictionaries, empty list on error
        """
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode())
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
def load_meetings_from_url(url: str) -> List[Dict]:
    """Load meetings data from a URL (backward compatibility)."""
    return MeetingDataLoader.load_from_url(url)