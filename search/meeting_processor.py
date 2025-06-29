"""
Meeting data processing module.
Handles validation, filtering, and time-chunking of meeting data.
"""

import math
from collections import defaultdict
from typing import List, Dict, Tuple, Any, Optional


class MeetingProcessor:
    """Processes meeting data for time-chunking and validation."""
    
    def __init__(self, chunk_duration_minutes: int = 5):
        self.chunk_duration_ms = chunk_duration_minutes * 60 * 1000
        self.chunk_duration_minutes = chunk_duration_minutes
    
    def validate_and_filter_meetings(self, meetings_data: List[Dict]) -> List[Dict]:
        """
        Filter meetings to only those with valid coordinates and timing data.
        
        Args:
            meetings_data: Raw meeting data
            
        Returns:
            List of validated meetings with required fields
        """
        valid_meetings = []
        
        for meeting in meetings_data:
            location = meeting.get('location')
            if not location:
                continue
                
            coordinates = location.get('coordinates', [])
            if not coordinates or len(coordinates) != 2 or coordinates[0] is None or coordinates[1] is None:
                continue
                
            start_time = meeting.get('start_time')
            end_time = meeting.get('end_time')
            if start_time is None or end_time is None:
                continue
                
            valid_meetings.append(meeting)
        
        return valid_meetings
    
    def calculate_time_range(self, meetings: List[Dict]) -> Tuple[int, int, int]:
        """
        Calculate the global time range and number of chunks needed.
        
        Args:
            meetings: List of validated meetings
            
        Returns:
            Tuple of (start_time, end_time, total_chunks)
        """
        if not meetings:
            return 0, 0, 0
        
        all_start_times = [m['start_time'] for m in meetings]
        all_end_times = [m['end_time'] for m in meetings]
        global_start = min(all_start_times)
        global_end = max(all_end_times)
        
        total_chunks = math.ceil((global_end - global_start) / self.chunk_duration_ms)
        
        return global_start, global_end, total_chunks
    
    def extract_meeting_data(self, meeting: Dict) -> Tuple[int, int, Tuple[float, float]]:
        """
        Extract enrollment, instructor count, and coordinates from a meeting.
        
        Args:
            meeting: Meeting dictionary
            
        Returns:
            Tuple of (enrollment, instructor_count, (lon, lat))
        """
        # Get enrollment
        current_enrollment = meeting.get('current_enrollment', 0)
        if current_enrollment is None:
            current_enrollment = 0
        
        # Get instructor count
        instructors = meeting.get('instructors', [])
        instructor_count = len(instructors) if instructors else 0
        
        # Get coordinates
        coordinates = meeting.get('location', {}).get('coordinates', [])
        lat, lon = coordinates[0], coordinates[1]
        coord_key = (lon, lat)
        
        return current_enrollment, instructor_count, coord_key
    
    def calculate_time_chunks(self, start_time: int, end_time: int, global_start: int, total_chunks: int) -> Tuple[int, int]:
        """
        Calculate which time chunks a meeting spans.
        
        Args:
            start_time: Meeting start time (ms)
            end_time: Meeting end time (ms)
            global_start: Global start time (ms)
            total_chunks: Total number of chunks
            
        Returns:
            Tuple of (start_chunk, end_chunk) indices
        """
        start_chunk = int((start_time - global_start) // self.chunk_duration_ms)
        end_chunk = int((end_time - global_start) // self.chunk_duration_ms)
        
        # Ensure chunks are within bounds
        start_chunk = max(0, min(start_chunk, total_chunks - 1))
        end_chunk = max(0, min(end_chunk, total_chunks - 1))
        
        return start_chunk, end_chunk
    
    def process_meetings_to_coordinate_data(self, meetings: List[Dict]) -> Tuple[Dict, int, int, int]:
        """
        Process meetings into time-chunked coordinate data.
        
        Args:
            meetings: List of validated meetings
            
        Returns:
            Tuple of (coordinate_time_data, global_start, global_end, total_chunks)
        """
        global_start, global_end, total_chunks = self.calculate_time_range(meetings)
        
        if total_chunks == 0:
            return {}, 0, 0, 0
        
        # Store data by coordinate and time chunk
        coordinate_time_data = defaultdict(lambda: {
            'persons': [0] * total_chunks, 
            'instructors': [0] * total_chunks
        })
        
        for meeting in meetings:
            enrollment, instructor_count, coord_key = self.extract_meeting_data(meeting)
            start_time = meeting.get('start_time')
            end_time = meeting.get('end_time')
            
            start_chunk, end_chunk = self.calculate_time_chunks(
                start_time, end_time, global_start, total_chunks
            )
            
            # Add counts to all chunks that this meeting spans
            for chunk_idx in range(start_chunk, end_chunk + 1):
                coordinate_time_data[coord_key]['persons'][chunk_idx] += enrollment
                coordinate_time_data[coord_key]['instructors'][chunk_idx] += instructor_count
        
        return coordinate_time_data, global_start, global_end, total_chunks