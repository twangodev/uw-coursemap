import math
from collections import defaultdict
from functools import lru_cache
from logging import getLogger
from typing import Dict, List, Tuple, Any

import geojson
import geopandas as gpd
from shapely.geometry import Point

logger = getLogger(__name__)


class BuildingLoader:
    """Loads and manages OSM building data."""
    
    def __init__(self, geojson_path: str):
        self.geojson_path = geojson_path
        self._buildings_gdf = None
    
    def load_buildings(self) -> gpd.GeoDataFrame:
        """Load and filter GeoDataFrame to only buildings with spatial index."""
        if self._buildings_gdf is not None:
            return self._buildings_gdf
            
        logger.info(f"Loading buildings from {self.geojson_path}")
        
        # Load the full GeoJSON
        gdf = gpd.read_file(self.geojson_path)
        
        # Filter to only building features (Polygon/MultiPolygon with building property)
        building_mask = (
            (gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])) &
            (gdf['building'].notna()) &
            (gdf['building'] != '') &
            (gdf['building'] != 'no')
        )
        
        self._buildings_gdf = gdf[building_mask].copy()
        
        # Create spatial index for fast queries
        self._buildings_gdf.sindex
        
        logger.info(f"Loaded {len(self._buildings_gdf)} buildings with spatial index")
        return self._buildings_gdf
    
    def get_building_stats(self) -> Dict[str, Any]:
        """Return statistics about loaded buildings."""
        if self._buildings_gdf is None:
            self.load_buildings()
            
        return {
            "total_buildings": len(self._buildings_gdf),
            "geometry_types": self._buildings_gdf.geometry.geom_type.value_counts().to_dict()
        }


class MeetingProcessor:
    """Processes meeting data into time-chunked coordinate data."""
    
    def __init__(self, chunk_duration_minutes: int = 5):
        self.chunk_duration_minutes = chunk_duration_minutes
        self.chunk_duration_ms = chunk_duration_minutes * 60 * 1000
    
    def validate_and_filter_meetings(self, meetings_data: List) -> List:
        """Filter meetings with valid coordinates and timing data."""
        valid_meetings = []
        
        for meeting in meetings_data:
            # Check for required fields
            if not meeting.location or not meeting.location.coordinates:
                continue
            if not meeting.start_time or not meeting.end_time:
                continue
            if not meeting.current_enrollment:
                continue
                
            # Validate coordinates
            coords = meeting.location.coordinates
            if len(coords) != 2:
                continue
            
            longitude, latitude = coords
            if longitude is None or latitude is None:
                continue
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                continue
                
            valid_meetings.append(meeting)
        
        logger.info(f"Filtered to {len(valid_meetings)} valid meetings from {len(meetings_data)} total")
        return valid_meetings
    
    def calculate_time_range(self, meetings: List) -> Tuple[int, int, int]:
        """Calculate global time range and total chunks."""
        if not meetings:
            return 0, 0, 0
            
        start_times = [m.start_time for m in meetings]
        end_times = [m.end_time for m in meetings]
        
        global_start = min(start_times)
        global_end = max(end_times)
        
        total_duration_ms = global_end - global_start
        total_chunks = math.ceil(total_duration_ms / self.chunk_duration_ms)
        
        return global_start, global_end, total_chunks
    
    def process_meetings_to_coordinate_data(self, meetings: List) -> Tuple[Dict, int, int, int]:
        """Process meetings into coordinate time data structure."""
        valid_meetings = self.validate_and_filter_meetings(meetings)
        
        if not valid_meetings:
            return {}, 0, 0, 0
            
        global_start, global_end, total_chunks = self.calculate_time_range(valid_meetings)
        
        # Initialize coordinate time data
        coordinate_time_data = defaultdict(lambda: {
            'persons': [0] * total_chunks,
            'instructors': [0] * total_chunks
        })
        
        # Process each meeting
        for meeting in valid_meetings:
            longitude, latitude = meeting.location.coordinates
            coord_key = (longitude, latitude)
            
            # Calculate time chunk indices for this meeting
            start_chunk = max(0, (meeting.start_time - global_start) // self.chunk_duration_ms)
            end_chunk = min(total_chunks - 1, (meeting.end_time - global_start) // self.chunk_duration_ms)
            
            # Add enrollment to each time chunk this meeting spans
            for chunk_idx in range(int(start_chunk), int(end_chunk) + 1):
                coordinate_time_data[coord_key]['persons'][chunk_idx] += meeting.current_enrollment
                
                # Count unique instructors (simplified - count all instructors)
                if meeting.instructors:
                    coordinate_time_data[coord_key]['instructors'][chunk_idx] += len(meeting.instructors)
        
        # Convert defaultdict to regular dict
        coordinate_time_data = dict(coordinate_time_data)
        
        logger.info(f"Processed {len(valid_meetings)} meetings into {len(coordinate_time_data)} coordinate points")
        return coordinate_time_data, global_start, global_end, total_chunks


class SpatialQueryEngine:
    """Performs spatial queries to find buildings containing coordinates."""
    
    def __init__(self, buildings_gdf: gpd.GeoDataFrame):
        self.buildings_gdf = buildings_gdf
    
    @lru_cache(maxsize=512)
    def _find_buildings_for_coordinates_tuple(self, coordinates_tuple) -> str:
        """Cached spatial query for a coordinate tuple."""
        longitude, latitude = coordinates_tuple
        point = Point(longitude, latitude)
        
        # Use spatial index for fast lookup
        possible_matches_index = list(self.buildings_gdf.sindex.intersection(point.bounds))
        possible_matches = self.buildings_gdf.iloc[possible_matches_index]
        
        # Check which buildings actually contain the point
        containing_buildings = possible_matches[possible_matches.contains(point)]
        
        # Return index of first matching building (if any)
        if len(containing_buildings) > 0:
            return str(containing_buildings.index[0])
        return ""
    
    def find_buildings_containing_points(self, coordinates: List[Tuple[float, float]]) -> geojson.FeatureCollection:
        """Find all buildings containing any of the given coordinates."""
        building_indices = set()
        
        for coord in coordinates:
            building_idx = self._find_buildings_for_coordinates_tuple(coord)
            if building_idx:
                building_indices.add(int(building_idx))
        
        # Get matching buildings
        matching_buildings = self.buildings_gdf.loc[list(building_indices)]
        
        # Convert to GeoJSON
        return geojson.loads(matching_buildings.to_json())


class BuildingAggregator:
    """Aggregates coordinate-level data to building level."""
    
    def __init__(self, spatial_query_engine: SpatialQueryEngine):
        self.spatial_query_engine = spatial_query_engine
    
    def aggregate_coordinate_data_to_buildings(
        self, 
        buildings_geojson: geojson.FeatureCollection,
        coordinate_time_data: Dict,
        total_chunks: int
    ) -> Dict[int, Dict[str, List[int]]]:
        """Aggregate coordinate data to building level."""
        building_time_data = defaultdict(lambda: {
            'persons': [0] * total_chunks,
            'instructors': [0] * total_chunks
        })
        
        # Map coordinate data to buildings
        for coord_key, time_data in coordinate_time_data.items():
            building_idx = self.spatial_query_engine._find_buildings_for_coordinates_tuple(coord_key)
            if building_idx:
                building_idx = int(building_idx)
                
                # Add to building totals
                for chunk_idx in range(total_chunks):
                    building_time_data[building_idx]['persons'][chunk_idx] += time_data['persons'][chunk_idx]
                    building_time_data[building_idx]['instructors'][chunk_idx] += time_data['instructors'][chunk_idx]
        
        return dict(building_time_data)
    
    def clean_and_enhance_building_properties(self, buildings_geojson, building_time_data, total_chunks):
        """Add person_counts and instructor_counts to building properties."""
        for feature in buildings_geojson['features']:
            # Get building index from the feature
            building_idx = feature['id']  # Assuming id is set to the DataFrame index
            
            if building_idx in building_time_data:
                feature['properties']['person_counts'] = building_time_data[building_idx]['persons']
                feature['properties']['instructor_counts'] = building_time_data[building_idx]['instructors']
            else:
                # No data for this building
                feature['properties']['person_counts'] = [0] * total_chunks
                feature['properties']['instructor_counts'] = [0] * total_chunks
            
            # Buffer geometry slightly for better visualization (approximately 1 meter)
            # Note: This is approximate and works for campus-scale visualization
            buffer_degrees = 0.00001  # ~1 meter at typical latitudes
            
            # Simplified buffering - just store the original geometry
            # In a full implementation, you might want to apply actual buffering
    
    def calculate_campus_totals(self, buildings_geojson, total_chunks) -> Tuple[List[int], List[int], int]:
        """Calculate campus-wide totals across all buildings."""
        total_persons_by_chunk = [0] * total_chunks
        total_instructors_by_chunk = [0] * total_chunks
        max_persons = 0
        
        for feature in buildings_geojson['features']:
            person_counts = feature['properties'].get('person_counts', [])
            instructor_counts = feature['properties'].get('instructor_counts', [])
            
            for chunk_idx in range(min(total_chunks, len(person_counts))):
                total_persons_by_chunk[chunk_idx] += person_counts[chunk_idx]
                total_instructors_by_chunk[chunk_idx] += instructor_counts[chunk_idx]
                max_persons = max(max_persons, person_counts[chunk_idx])
        
        return total_persons_by_chunk, total_instructors_by_chunk, max_persons


def generate_building_highlight_geojson(meetings: List, osm_geojson_path: str) -> geojson.FeatureCollection:
    """
    Generate building highlight GeoJSON from a list of meetings.
    
    Args:
        meetings: List of Meeting objects with location, timing, and enrollment data
        osm_geojson_path: Path to the OSM GeoJSON file
    
    Returns:
        GeoJSON FeatureCollection with building highlights and metadata
    """
    if not meetings:
        return geojson.FeatureCollection([])
    
    # Initialize components
    building_loader = BuildingLoader(osm_geojson_path)
    buildings_gdf = building_loader.load_buildings()
    
    meeting_processor = MeetingProcessor(chunk_duration_minutes=5)
    coordinate_time_data, global_start, global_end, total_chunks = meeting_processor.process_meetings_to_coordinate_data(meetings)
    
    if not coordinate_time_data:
        return geojson.FeatureCollection([])
    
    spatial_query_engine = SpatialQueryEngine(buildings_gdf)
    
    # Find buildings containing meeting coordinates
    coordinates = list(coordinate_time_data.keys())
    buildings_geojson = spatial_query_engine.find_buildings_containing_points(coordinates)
    
    # Aggregate data to building level
    building_aggregator = BuildingAggregator(spatial_query_engine)
    building_time_data = building_aggregator.aggregate_coordinate_data_to_buildings(
        buildings_geojson, coordinate_time_data, total_chunks
    )
    
    # Enhance building properties
    building_aggregator.clean_and_enhance_building_properties(
        buildings_geojson, building_time_data, total_chunks
    )
    
    # Calculate campus totals
    total_persons_by_chunk, total_instructors_by_chunk, max_persons = building_aggregator.calculate_campus_totals(
        buildings_geojson, total_chunks
    )
    
    # Add metadata
    buildings_geojson['metadata'] = {
        'total_buildings': len(buildings_geojson['features']),
        'total_meetings': len(meetings),
        'max_persons': max_persons,
        'total_chunks': total_chunks,
        'chunk_duration_minutes': meeting_processor.chunk_duration_minutes,
        'start_time': global_start,
        'end_time': global_end,
        'total_persons': total_persons_by_chunk,
        'total_instructors': total_instructors_by_chunk
    }
    
    logger.info(f"Generated building highlight GeoJSON with {len(buildings_geojson['features'])} buildings")
    return buildings_geojson