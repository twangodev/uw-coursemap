"""
Refactored map module with clean separation of concerns.
Main orchestrator for building and meeting data processing.
"""

from typing import List, Dict, Tuple

import geojson

from building_aggregator import BuildingAggregator
from building_loader import BuildingLoader
from meeting_processor import MeetingProcessor
from spatial_query import SpatialQueryEngine


class MapDataProcessor:
    """
    Main orchestrator for processing meeting data and generating building visualizations.

    NOTE: Person counts represent "course-seat enrollments" not unique students.
    Students taking multiple courses or enrolled in both lecture and discussion
    sections of the same course will be counted multiple times. Total campus
    numbers may exceed actual unique student count.
    """

    def __init__(self, chunk_duration_minutes: int = 5):
        self.building_loader = BuildingLoader()
        self.meeting_processor = MeetingProcessor(chunk_duration_minutes)
        self.spatial_engine = SpatialQueryEngine(self.building_loader.buildings)
        self.building_aggregator = BuildingAggregator(self.building_loader.buildings)

    def get_buildings(self, meetings_data: List[Dict]) -> Tuple[geojson.FeatureCollection, Dict]:
        """
        Get buildings with person and instructor counts in 5-minute time chunks.

        Args:
            meetings_data: List of meeting dictionaries with location.coordinates,
                          current_enrollment, instructors, start_time, end_time

        Returns:
            Tuple of (GeoJSON FeatureCollection with buildings, metadata dict)
        """
        # Step 1: Validate and filter meetings
        valid_meetings = self.meeting_processor.validate_and_filter_meetings(meetings_data)

        if not valid_meetings:
            return self._empty_response()

        # Step 2: Process meetings into time-chunked coordinate data
        coordinate_time_data, global_start, global_end, total_chunks = \
            self.meeting_processor.process_meetings_to_coordinate_data(valid_meetings)

        if not coordinate_time_data:
            return self._empty_response_with_metadata(total_chunks, global_start, global_end)

        # Step 3: Find buildings at meeting coordinates
        coordinates_list = list(coordinate_time_data.keys())
        buildings_geojson = self.spatial_engine.find_buildings_containing_points(coordinates_list)

        if not buildings_geojson.features:
            return self._empty_response_with_metadata(total_chunks, global_start, global_end)

        # Step 4: Aggregate coordinate data to building level
        building_time_data = self.building_aggregator.aggregate_coordinate_data_to_buildings(
            buildings_geojson, coordinate_time_data, total_chunks
        )

        # Step 5: Clean properties and add time-chunked data
        self.building_aggregator.clean_and_enhance_building_properties(
            buildings_geojson, building_time_data, total_chunks
        )

        # Step 6: Expand building geometries for visualization
        self.building_aggregator.expand_building_geometries(buildings_geojson)

        # Step 7: Calculate campus-wide totals
        total_persons_by_chunk, total_instructors_by_chunk, max_persons = \
            self.building_aggregator.calculate_campus_totals(buildings_geojson, total_chunks)

        # Step 8: Create comprehensive metadata
        metadata = self._create_metadata(
            total_chunks, global_start, global_end, max_persons,
            total_persons_by_chunk, total_instructors_by_chunk
        )

        return buildings_geojson, metadata

    def _empty_response(self) -> Tuple[geojson.FeatureCollection, Dict]:
        """Return empty response with minimal metadata."""
        return geojson.FeatureCollection([]), {
            'total_chunks': 0,
            'chunk_duration_minutes': self.meeting_processor.chunk_duration_minutes,
            'start_time': None,
            'end_time': None,
            'max_persons': 0,
            'total_persons': [],
            'total_instructors': []
        }

    def _empty_response_with_metadata(self, total_chunks: int, start_time: int, end_time: int) -> Tuple[geojson.FeatureCollection, Dict]:
        """Return empty response with timing metadata."""
        return geojson.FeatureCollection([]), {
            'total_chunks': total_chunks,
            'chunk_duration_minutes': self.meeting_processor.chunk_duration_minutes,
            'start_time': start_time,
            'end_time': end_time,
            'max_persons': 0,
            'total_persons': [0] * total_chunks,
            'total_instructors': [0] * total_chunks
        }

    def _create_metadata(
            self,
            total_chunks: int,
            start_time: int,
            end_time: int,
            max_persons: int,
            total_persons: List[int],
            total_instructors: List[int]
    ) -> Dict:
        """Create comprehensive metadata dictionary."""
        return {
            'total_chunks': total_chunks,
            'chunk_duration_minutes': self.meeting_processor.chunk_duration_minutes,
            'start_time': start_time,
            'end_time': end_time,
            'max_persons': max_persons,
            'total_persons': total_persons,
            'total_instructors': total_instructors
        }


# Global instance for app.py usage
_processor = MapDataProcessor()
get_buildings = _processor.get_buildings