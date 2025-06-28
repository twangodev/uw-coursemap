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
    Get buildings with person counts and instructor counts based on meeting coordinates
    
    Args:
        meetings_data: List of meeting dictionaries with location.coordinates, current_enrollment, and instructors
    
    Returns:
        GeoJSON FeatureCollection with buildings containing person_count and instructor_count properties
    """
    from collections import defaultdict
    
    # Count persons and instructors by coordinate
    coordinate_data = defaultdict(lambda: {'persons': 0, 'instructors': 0})
    
    for meeting in meetings_data:
        location = meeting.get('location')
        if not location:
            continue
            
        coordinates = location.get('coordinates', [])
        
        # Skip if coordinates are null or invalid
        if not coordinates or len(coordinates) != 2 or coordinates[0] is None or coordinates[1] is None:
            continue
        
        # Get enrollment and instructor count for this meeting
        current_enrollment = meeting.get('current_enrollment', 0)
        if current_enrollment is None:
            current_enrollment = 0
            
        instructors = meeting.get('instructors', [])
        instructor_count = len(instructors) if instructors else 0
            
        lat, lon = coordinates[0], coordinates[1]
        coord_key = (lon, lat)  # lon, lat for consistency with our building lookup
        
        coordinate_data[coord_key]['persons'] += current_enrollment
        coordinate_data[coord_key]['instructors'] += instructor_count
    
    if not coordinate_data:
        # No valid coordinates found, return empty buildings
        return geojson.FeatureCollection([])
    
    # Find buildings at these coordinates
    coordinates_list = list(coordinate_data.keys())
    buildings_geojson = find_buildings_containing_points(coordinates_list)
    
    if not buildings_geojson.features:
        return buildings_geojson
    
    # Create mapping from building to person and instructor counts
    building_data = {}
    
    # For each building found, count persons and instructors at coordinates it contains
    for i, feature in enumerate(buildings_geojson.features):
        total_persons = 0
        total_instructors = 0
        
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
            
            # Count persons and instructors at coordinates contained in this building
            for coord, data in coordinate_data.items():
                point = Point(coord[0], coord[1])
                if building_geom.contains(point):
                    total_persons += data['persons']
                    total_instructors += data['instructors']
        
        building_data[i] = {'persons': total_persons, 'instructors': total_instructors}
    
    # Add person and instructor counts to building properties and expand geometry
    for i, feature in enumerate(buildings_geojson.features):
        data = building_data.get(i, {'persons': 0, 'instructors': 0})
        
        # Add counts to feature properties
        if 'properties' not in feature:
            feature['properties'] = {}
        feature['properties']['person_count'] = data['persons']
        feature['properties']['instructor_count'] = data['instructors']
        
        # Expand the building geometry by approximately 1 meter
        # Using a small buffer in degrees (roughly 1 meter = ~0.000009 degrees at this latitude)
        if 'geometry' in feature:
            from shapely.geometry import shape
            geom = shape(feature['geometry'])
            
            # Buffer by ~1 meter (0.000009 degrees ≈ 1 meter at ~43° latitude)
            buffered_geom = geom.buffer(0.000018)
            
            # Convert back to GeoJSON geometry
            feature['geometry'] = buffered_geom.__geo_interface__
    
    return buildings_geojson

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
# Load meetings and get buildings with person and instructor counts
# meetings = load_meetings_from_url("https://raw.githubusercontent.com/twangodev/uw-coursemap-data/refs/heads/main/meetings/11-17-25.json")
# buildings_with_counts = get_buildings_with_meeting_counts(meetings)
#
# The result contains buildings with person and instructor counts
# Each building feature will have:
# - geometry: Building polygon/multipolygon (expanded by ~1 meter)
# - properties: Building attributes including:
#   - 'person_count': Total enrollment (current_enrollment) across all meetings
#   - 'instructor_count': Total unique instructor count across all meetings
#
# Single coordinate lookup:
# result = find_building_at_coordinate(-89.417758, 43.077681)