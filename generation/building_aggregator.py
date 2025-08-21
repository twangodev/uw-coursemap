"""
Building aggregation module.
Handles aggregating meeting data to buildings and calculating totals.
"""

import geojson
from shapely.geometry import Point, shape
from typing import Dict, List, Tuple, Any
from building_loader import buildings_gdf


class BuildingAggregator:
    """Aggregates time-chunked meeting data to building level."""

    ESSENTIAL_BUILDING_FIELDS = [
        "building",
        "name",
        "@id",
        "addr:street",
        "addr:housenumber",
    ]
    BUILDING_BUFFER_DEGREES = 0.000018  # ~1 meter at 43° latitude

    def __init__(self, buildings_data=None):
        self.buildings_gdf = (
            buildings_data if buildings_data is not None else buildings_gdf
        )
        self._id_to_geometry = {
            row.get("@id", ""): row.geometry
            for idx, row in self.buildings_gdf.iterrows()
            if row.get("@id")
        }

    def aggregate_coordinate_data_to_buildings(
        self,
        buildings_geojson: geojson.FeatureCollection,
        coordinate_time_data: Dict,
        total_chunks: int,
    ) -> Dict[int, Dict[str, List[int]]]:
        """
        Aggregate time-chunked coordinate data to building level.

        Args:
            buildings_geojson: GeoJSON of buildings found
            coordinate_time_data: Time-chunked data by coordinate
            total_chunks: Total number of time chunks

        Returns:
            Dictionary mapping building index to time-chunked data
        """
        building_time_data = {}

        for i, feature in enumerate(buildings_geojson.features):
            building_persons = [0] * total_chunks
            building_instructors = [0] * total_chunks

            building_geom = self._get_building_geometry(feature)

            if building_geom is not None:
                # Aggregate time-chunked data from coordinates contained in this building
                for coord, time_data in coordinate_time_data.items():
                    point = Point(coord[0], coord[1])
                    if building_geom.contains(point):
                        # Add each time chunk
                        for chunk_idx in range(total_chunks):
                            building_persons[chunk_idx] += time_data["persons"][
                                chunk_idx
                            ]
                            building_instructors[chunk_idx] += time_data["instructors"][
                                chunk_idx
                            ]

            building_time_data[i] = {
                "persons": building_persons,
                "instructors": building_instructors,
            }

        return building_time_data

    def clean_and_enhance_building_properties(
        self,
        buildings_geojson: geojson.FeatureCollection,
        building_time_data: Dict[int, Dict[str, List[int]]],
        total_chunks: int,
    ) -> None:
        """
        Clean building properties and add time-chunked data.

        Args:
            buildings_geojson: GeoJSON to modify in-place
            building_time_data: Time-chunked data by building index
            total_chunks: Total number of time chunks
        """
        for i, feature in enumerate(buildings_geojson.features):
            time_data = building_time_data.get(
                i, {"persons": [0] * total_chunks, "instructors": [0] * total_chunks}
            )

            # Clean up properties - remove null/empty values and keep only essential fields
            cleaned_props = self._clean_building_properties(
                feature.get("properties", {})
            )

            # Add our computed time-chunked arrays
            cleaned_props["person_counts"] = time_data["persons"]
            cleaned_props["instructor_counts"] = time_data["instructors"]

            feature["properties"] = cleaned_props

    def expand_building_geometries(
        self, buildings_geojson: geojson.FeatureCollection
    ) -> None:
        """
        Expand building geometries by a small buffer for visualization.

        Args:
            buildings_geojson: GeoJSON to modify in-place
        """
        for feature in buildings_geojson.features:
            if "geometry" in feature:
                geom = shape(feature["geometry"])
                buffered_geom = geom.buffer(self.BUILDING_BUFFER_DEGREES)
                feature["geometry"] = buffered_geom.__geo_interface__

    def calculate_campus_totals(
        self, buildings_geojson: geojson.FeatureCollection, total_chunks: int
    ) -> Tuple[List[int], List[int], int]:
        """
        Calculate campus-wide totals for each time chunk.

        Args:
            buildings_geojson: GeoJSON with building data
            total_chunks: Total number of time chunks

        Returns:
            Tuple of (total_persons_by_chunk, total_instructors_by_chunk, max_persons)
        """
        total_persons_by_chunk = [0] * total_chunks
        total_instructors_by_chunk = [0] * total_chunks
        max_persons = 0

        for feature in buildings_geojson.features:
            person_counts = feature["properties"].get("person_counts", [])
            instructor_counts = feature["properties"].get("instructor_counts", [])

            # Track max persons across all chunks
            if person_counts:
                max_persons = max(max_persons, max(person_counts))

            # Aggregate totals for each chunk
            for chunk_idx in range(min(len(person_counts), total_chunks)):
                total_persons_by_chunk[chunk_idx] += person_counts[chunk_idx]

            for chunk_idx in range(min(len(instructor_counts), total_chunks)):
                total_instructors_by_chunk[chunk_idx] += instructor_counts[chunk_idx]

        return total_persons_by_chunk, total_instructors_by_chunk, max_persons

    def _get_building_geometry(self, feature: Dict) -> Any:
        """Get the building geometry from the original buildings dataset."""
        building_id = feature.get("properties", {}).get("@id", "")
        return self._id_to_geometry.get(building_id)

    def _clean_building_properties(self, original_props: Dict) -> Dict:
        """Clean building properties, keeping only essential non-null fields."""
        cleaned_props = {}

        for field in self.ESSENTIAL_BUILDING_FIELDS:
            value = original_props.get(field)
            if value is not None and value != "" and value != "None":
                cleaned_props[field] = value

        return cleaned_props
