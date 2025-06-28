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
        matching_buildings = buildings_gdf.iloc[list(matching_indices)]
        # Convert back to GeoJSON format
        return geojson.loads(matching_buildings.to_json())
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

# Example usage:
# Single coordinate lookup:
result = find_building_at_coordinate(-89.417758, 43.077681)
print(result)