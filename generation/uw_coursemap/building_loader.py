"""
Building data loading and management module.
Handles loading OSM building data and creating spatial indexes.
"""

import geopandas as gpd
import os
from typing import Dict, Any


class BuildingLoader:
    """Manages loading and filtering of building data from OSM GeoJSON."""

    def __init__(self, geojson_path: str = None):
        if geojson_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            geojson_path = os.path.join(current_dir, "osm.geojson")

        self.geojson_path = geojson_path
        self._buildings_gdf = None

    def load_buildings(self) -> gpd.GeoDataFrame:
        """
        Load and filter OSM GeoJSON data to only building features.

        Returns:
            GeoDataFrame with only buildings, spatially indexed for fast queries
        """
        if self._buildings_gdf is not None:
            return self._buildings_gdf

        print("Loading building data...")
        gdf = gpd.read_file(self.geojson_path)

        # Filter to only building features (exclude Points and non-building features)
        building_gdf = gdf[
            (gdf.geometry.type.isin(["Polygon", "MultiPolygon"]))
            & (gdf["building"].notna())
            & (gdf["building"] != "")
        ].copy()

        # Reset index after filtering
        building_gdf.reset_index(drop=True, inplace=True)

        self._buildings_gdf = building_gdf
        print(f"Loaded {len(building_gdf)} buildings with spatial index")

        return self._buildings_gdf

    def get_building_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded building data."""
        if self._buildings_gdf is None:
            self.load_buildings()

        return {
            "total_buildings": len(self._buildings_gdf),
            "building_types": self._buildings_gdf["building"].value_counts().to_dict(),
            "geometry_types": self._buildings_gdf.geometry.type.value_counts().to_dict(),
        }

    @property
    def buildings(self) -> gpd.GeoDataFrame:
        """Get the buildings GeoDataFrame, loading if necessary."""
        if self._buildings_gdf is None:
            self.load_buildings()
        return self._buildings_gdf


_loader = BuildingLoader()
buildings_gdf = _loader.buildings
