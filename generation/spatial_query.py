"""
Spatial query module for building and coordinate operations.
Handles point-in-polygon queries and building lookups.
"""

import geojson
from shapely.geometry import Point
from typing import List, Tuple, Dict, Set
from building_loader import buildings_gdf


class SpatialQueryEngine:
    """Handles spatial queries for buildings and coordinates."""

    def __init__(self, buildings_data=None):
        self.buildings_gdf = buildings_data if buildings_data is not None else buildings_gdf
        self._point_cache: Dict[Tuple[float, float], Set[int]] = {}

    def _find_buildings_for_coordinates_tuple(self, coordinates_tuple: Tuple[Tuple[float, float], ...]) -> str:
        """
        Cached helper method for finding buildings containing coordinates.
        Takes a tuple of coordinates for hashability.
        """
        coordinates = list(coordinates_tuple)
        # Convert coordinates to Shapely Points
        points = [Point(lon, lat) for lon, lat in coordinates]

        matching_indices = set()

        # Use spatial index for fast lookups with caching
        for point in points:
            point_coord = (point.x, point.y)
            
            # Check cache first
            if point_coord in self._point_cache:
                matching_indices.update(self._point_cache[point_coord])
            else:
                # Get candidates using spatial index (fast bounding box check)
                possible_matches_index = list(self.buildings_gdf.sindex.intersection(point.bounds))
                
                # Precise containment check for candidates
                point_matches = set()
                for idx in possible_matches_index:
                    if self.buildings_gdf.geometry.iloc[idx].contains(point):
                        point_matches.add(idx)
                
                # Cache the result for this point
                self._point_cache[point_coord] = point_matches
                matching_indices.update(point_matches)

        geojson_result = self._convert_buildings_to_geojson(matching_indices)
        return geojson.dumps(geojson_result)

    def find_buildings_containing_points(self, coordinates: List[Tuple[float, float]]) -> geojson.FeatureCollection:
        """
        Find all buildings that contain any of the given coordinates using spatial indexing.

        Args:
            coordinates: List of (longitude, latitude) tuples

        Returns:
            GeoJSON FeatureCollection with matching buildings
        """
        # Convert to tuple for hashability and use cached method
        coordinates_tuple = tuple(coordinates)
        geojson_str = self._find_buildings_for_coordinates_tuple(coordinates_tuple)
        return geojson.loads(geojson_str)

    def find_building_at_coordinate(self, longitude: float, latitude: float) -> geojson.FeatureCollection:
        """
        Find buildings containing a single coordinate.

        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate

        Returns:
            GeoJSON FeatureCollection with matching buildings
        """
        return self.find_buildings_containing_points([(longitude, latitude)])

    def _convert_buildings_to_geojson(self, building_indices: set) -> geojson.FeatureCollection:
        """
        Convert building indices to GeoJSON FeatureCollection.

        Args:
            building_indices: Set of building DataFrame indices

        Returns:
            GeoJSON FeatureCollection
        """
        if not building_indices:
            return geojson.FeatureCollection([])

        matching_buildings = self.buildings_gdf.iloc[list(building_indices)].copy()

        # Handle timestamp/datetime columns that cause JSON serialization issues
        for col in matching_buildings.columns:
            if 'datetime' in str(matching_buildings[col].dtype):
                matching_buildings[col] = matching_buildings[col].astype(str)

        # Convert back to GeoJSON format
        return geojson.loads(matching_buildings.to_json(drop_id=True))


_spatial_engine = SpatialQueryEngine()
find_buildings_containing_points = _spatial_engine.find_buildings_containing_points
find_building_at_coordinate = _spatial_engine.find_building_at_coordinate