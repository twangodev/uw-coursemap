import geojson
import geopandas as gpd
import os
from shapely.geometry import Point
from typing import List, Tuple

def load_and_filter_buildings():
    """
    Load OSM GeoJSON data and filter to only building features with spatial indexing
    Returns: GeoDataFrame with only buildings, pre-indexed for fast spatial queries
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(current_dir, 'osm.geojson')
    
    # Load all data into GeoDataFrame
    gdf = gpd.read_file(geojson_path)
    
    # Filter to only building features (exclude Points and non-building features)
    building_gdf = gdf[
        (gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])) & 
        (gdf['building'].notna()) &
        (gdf['building'] != '')
    ].copy()
    
    # Reset index after filtering
    building_gdf.reset_index(drop=True, inplace=True)
    
    return building_gdf

def find_buildings_containing_points(coordinates: List[Tuple[float, float]]) -> geojson.FeatureCollection:
    """
    Find all buildings that contain any of the given coordinates using spatial indexing
    coordinates: List of (longitude, latitude) tuples
    Returns: GeoJSON FeatureCollection with matching buildings
    """
    # Convert coordinates to Shapely Points
    points = [Point(lon, lat) for lon, lat in coordinates]
    
    matching_indices = set()
    
    # Use spatial index for fast lookups
    for point in points:
        # Get candidates using spatial index (fast bounding box check)
        possible_matches_index = list(buildings_gdf.sindex.intersection(point.bounds))
        
        # Precise containment check for candidates
        for idx in possible_matches_index:
            if buildings_gdf.geometry.iloc[idx].contains(point):
                matching_indices.add(idx)
    
    # Get matching features
    if matching_indices:
        matching_buildings = buildings_gdf.iloc[list(matching_indices)].copy()
        
        # Handle timestamp/datetime columns that cause JSON serialization issues
        for col in matching_buildings.columns:
            if 'datetime' in str(matching_buildings[col].dtype):
                matching_buildings[col] = matching_buildings[col].astype(str)
        
        # Convert back to GeoJSON format
        return geojson.loads(matching_buildings.to_json(drop_id=True))
    else:
        return geojson.FeatureCollection([])

def find_building_at_coordinate(longitude: float, latitude: float) -> geojson.FeatureCollection:
    """
    Convenience function to find buildings containing a single coordinate
    """
    return find_buildings_containing_points([(longitude, latitude)])

def get_building_stats():
    """
    Get statistics about the loaded building data
    """
    return {
        'total_buildings': len(buildings_gdf),
        'building_types': buildings_gdf['building'].value_counts().to_dict(),
        'geometry_types': buildings_gdf.geometry.type.value_counts().to_dict()
    }

# Initialize the building data with spatial indexing when module is imported
print("Loading and indexing building data...")
buildings_gdf = load_and_filter_buildings()
print("Spatial index created for fast lookups!")

def get_buildings_with_meeting_counts(meetings_data):
    """
    Get buildings with person and instructor counts in 5-minute time chunks
    
    Args:
        meetings_data: List of meeting dictionaries with location.coordinates, current_enrollment, instructors, start_time, end_time
    
    Returns:
        GeoJSON FeatureCollection with buildings containing time-chunked person and instructor arrays
    """
    from collections import defaultdict
    import math
    
    # Find the time range for all meetings
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
    
    if not valid_meetings:
        return geojson.FeatureCollection([])
    
    # Find global time range
    all_start_times = [m['start_time'] for m in valid_meetings]
    all_end_times = [m['end_time'] for m in valid_meetings]
    global_start = min(all_start_times)
    global_end = max(all_end_times)
    
    # Calculate 5-minute chunks (300,000 milliseconds = 5 minutes)
    chunk_duration = 5 * 60 * 1000  # 5 minutes in milliseconds
    total_chunks = math.ceil((global_end - global_start) / chunk_duration)
    
    # Store data by coordinate and time chunk
    coordinate_time_data = defaultdict(lambda: {'persons': [0] * total_chunks, 'instructors': [0] * total_chunks})
    
    for meeting in valid_meetings:
        location = meeting.get('location')
        coordinates = location.get('coordinates', [])
        
        # Get meeting details
        current_enrollment = meeting.get('current_enrollment', 0)
        if current_enrollment is None:
            current_enrollment = 0
            
        instructors = meeting.get('instructors', [])
        instructor_count = len(instructors) if instructors else 0
        
        start_time = meeting.get('start_time')
        end_time = meeting.get('end_time')
        
        lat, lon = coordinates[0], coordinates[1]
        coord_key = (lon, lat)
        
        # Calculate which time chunks this meeting spans
        start_chunk = int((start_time - global_start) // chunk_duration)
        end_chunk = int((end_time - global_start) // chunk_duration)
        
        # Ensure chunks are within bounds
        start_chunk = max(0, min(start_chunk, total_chunks - 1))
        end_chunk = max(0, min(end_chunk, total_chunks - 1))
        
        # Add counts to all chunks that this meeting spans
        for chunk_idx in range(start_chunk, end_chunk + 1):
            coordinate_time_data[coord_key]['persons'][chunk_idx] += current_enrollment
            coordinate_time_data[coord_key]['instructors'][chunk_idx] += instructor_count
    
    if not coordinate_time_data:
        # No valid coordinates found, return empty buildings with metadata
        return geojson.FeatureCollection([]), {
            'total_chunks': 0,
            'chunk_duration_minutes': 5,
            'start_time': None,
            'end_time': None
        }
    
    # Find buildings at these coordinates
    coordinates_list = list(coordinate_time_data.keys())
    buildings_geojson = find_buildings_containing_points(coordinates_list)
    
    if not buildings_geojson.features:
        return buildings_geojson, {
            'total_chunks': total_chunks,
            'chunk_duration_minutes': 5,
            'start_time': global_start,
            'end_time': global_end
        }
    
    # Create mapping from building to time-chunked data
    building_time_data = {}
    
    # For each building found, aggregate time-chunked data from coordinates it contains
    for i, feature in enumerate(buildings_geojson.features):
        building_persons = [0] * total_chunks
        building_instructors = [0] * total_chunks
        
        # Get the building geometry by finding it in our buildings_gdf
        building_id = feature.get('properties', {}).get('@id', '')
        
        # Find this building in our original dataset
        building_row = None
        for idx, row in buildings_gdf.iterrows():
            if row.get('@id', '') == building_id:
                building_row = row
                break
        
        if building_row is not None:
            building_geom = building_row.geometry
            
            # Aggregate time-chunked data from coordinates contained in this building
            for coord, time_data in coordinate_time_data.items():
                point = Point(coord[0], coord[1])
                if building_geom.contains(point):
                    # Add each time chunk
                    for chunk_idx in range(total_chunks):
                        building_persons[chunk_idx] += time_data['persons'][chunk_idx]
                        building_instructors[chunk_idx] += time_data['instructors'][chunk_idx]
        
        building_time_data[i] = {
            'persons': building_persons,
            'instructors': building_instructors
        }
    
    # Add time-chunked person and instructor arrays to building properties and expand geometry
    for i, feature in enumerate(buildings_geojson.features):
        time_data = building_time_data.get(i, {
            'persons': [0] * total_chunks, 
            'instructors': [0] * total_chunks
        })
        
        # Clean up properties - remove null/empty values and keep only essential fields
        original_props = feature.get('properties', {})
        cleaned_props = {}
        
        # Keep only essential properties that have values
        essential_fields = ['building', 'name', '@id', 'addr:street', 'addr:housenumber']
        for field in essential_fields:
            value = original_props.get(field)
            if value is not None and value != '' and value != 'None':
                cleaned_props[field] = value
        
        # Add our computed time-chunked arrays
        cleaned_props['person_counts'] = time_data['persons']
        cleaned_props['instructor_counts'] = time_data['instructors']
        
        feature['properties'] = cleaned_props
        
        # Expand the building geometry by approximately 1 meter
        # Using a small buffer in degrees (roughly 1 meter = ~0.000009 degrees at this latitude)
        if 'geometry' in feature:
            from shapely.geometry import shape
            geom = shape(feature['geometry'])
            
            # Buffer by ~1 meter (0.000009 degrees ≈ 1 meter at ~43° latitude)
            buffered_geom = geom.buffer(0.000018)
            
            # Convert back to GeoJSON geometry
            feature['geometry'] = buffered_geom.__geo_interface__
    
    # Calculate campus-wide totals for each time chunk
    total_persons_by_chunk = [0] * total_chunks
    total_instructors_by_chunk = [0] * total_chunks
    max_persons = 0
    
    for feature in buildings_geojson.features:
        person_counts = feature['properties'].get('person_counts', [])
        instructor_counts = feature['properties'].get('instructor_counts', [])
        
        # Track max persons across all chunks
        if person_counts:
            max_persons = max(max_persons, max(person_counts))
        
        # Aggregate totals for each chunk
        for chunk_idx in range(min(len(person_counts), total_chunks)):
            total_persons_by_chunk[chunk_idx] += person_counts[chunk_idx]
        
        for chunk_idx in range(min(len(instructor_counts), total_chunks)):
            total_instructors_by_chunk[chunk_idx] += instructor_counts[chunk_idx]
    
    # Return buildings with comprehensive metadata about time chunks
    metadata = {
        'total_chunks': total_chunks,
        'chunk_duration_minutes': 5,
        'start_time': global_start,
        'end_time': global_end,
        'max_persons': max_persons,
        'total_persons': total_persons_by_chunk,
        'total_instructors': total_instructors_by_chunk
    }
    
    return buildings_geojson, metadata

def load_meetings_from_url(url):
    """
    Load meetings data from a URL
    """
    import urllib.request
    import json
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error loading meetings from {url}: {e}")
        return []

# Example usage:
# Load meetings and get buildings with time-chunked person and instructor counts
# meetings = load_meetings_from_url("https://raw.githubusercontent.com/twangodev/uw-coursemap-data/refs/heads/main/meetings/11-17-25.json")
# buildings_with_counts, time_metadata = get_buildings_with_meeting_counts(meetings)
#
# The result contains buildings with time-chunked arrays (5-minute intervals)
# Each building feature will have:
# - geometry: Building polygon/multipolygon (expanded by ~1 meter)
# - properties: Cleaned building attributes (null fields removed) including:
#   - 'building': Building type (e.g., 'university')
#   - 'name': Building name (if available)
#   - '@id': OSM identifier
#   - 'addr:street', 'addr:housenumber': Address info (if available)
#   - 'person_counts': Array of enrollment counts for each 5-minute chunk
#   - 'instructor_counts': Array of instructor counts for each 5-minute chunk
#
# time_metadata contains:
#   - 'total_chunks': Number of 5-minute intervals
#   - 'chunk_duration_minutes': 5
#   - 'start_time': First meeting start time (milliseconds)
#   - 'end_time': Last meeting end time (milliseconds)
#   - 'max_persons': Maximum persons in any building at any time
#   - 'total_persons': Array of campus-wide person totals for each chunk
#   - 'total_instructors': Array of campus-wide instructor totals for each chunk
#
# Frontend usage: building.person_counts[timeIndex] for any 5-minute window
#
# Single coordinate lookup:
# result = find_building_at_coordinate(-89.417758, 43.077681)