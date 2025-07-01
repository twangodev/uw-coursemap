import json
import random
import math
from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
import heapq
import numpy as np
from rtree import index


class TripGenerator:
    def __init__(self, geojson_path: str):
        """Initialize the trip generator with traffic data from GeoJSON file."""
        self.geojson_path = geojson_path
        self.traffic_data = None
        self.segments = []
        self.segment_adjacency = defaultdict(set)  # segment_id -> set of connected segment_ids
        self.load_traffic_data()
        self.build_road_network()
    
    def load_traffic_data(self):
        """Load and process the traffic GeoJSON data."""
        try:
            with open(self.geojson_path, 'r') as f:
                self.traffic_data = json.load(f)
            
            # Extract segments with their properties
            for feature in self.traffic_data['features']:
                props = feature['properties']
                geometry = feature['geometry']
                
                # Convert traffic count to integer, default to 0 if null
                awt_count = props.get('AWT_Count', 0) or 0
                if isinstance(awt_count, str):
                    try:
                        awt_count = int(awt_count)
                    except ValueError:
                        awt_count = 0
                
                segment = {
                    'id': props.get('OBJECTID'),
                    'mslink': props.get('mslink'),
                    'name': props.get('segment_na', ''),
                    'traffic_count': awt_count,
                    'station': props.get('STATION'),
                    'source': props.get('SOURCE'),
                    'year': props.get('AWT_Yr'),
                    'length': props.get('ShapeSTLength', 0),
                    'geometry': geometry,
                    'coordinates': geometry['coordinates'] if geometry['type'] == 'LineString' else []
                }
                self.segments.append(segment)
            
            print(f"Loaded {len(self.segments)} traffic segments")
            
        except Exception as e:
            print(f"Error loading traffic data: {e}")
            raise
    
    def build_road_network(self):
        """Build segment adjacency list based on endpoint clustering."""
        print("Building road network...")
        
        # Step 1: Group segments by their endpoints (within 1ft = 0.3m)
        endpoint_clusters = self.cluster_endpoints()
        
        # Step 2: Build adjacency list - segments are connected if they share endpoint clusters
        self.build_segment_adjacency(endpoint_clusters)
        
        print(f"Built network with {len(self.segments)} segments and {len(self.segment_adjacency)} connections")
        self.validate_segment_connectivity()
    
    def cluster_endpoints(self) -> Dict[int, List[int]]:
        """Group segments by their endpoints using RTree spatial index. Returns cluster_id -> [segment_ids]."""
        endpoints = []  # [(coord, segment_id), ...]
        
        # Extract all endpoints
        for segment in self.segments:
            if segment['coordinates'] and len(segment['coordinates']) >= 2:
                start_coord = tuple(segment['coordinates'][0])
                end_coord = tuple(segment['coordinates'][-1])
                endpoints.append((start_coord, segment['id']))
                endpoints.append((end_coord, segment['id']))
        
        print(f"Clustering {len(endpoints)} endpoints using RTree...")
        
        # Build RTree spatial index
        idx = index.Index()
        for i, (coord, seg_id) in enumerate(endpoints):
            lon, lat = coord
            # Insert point as tiny bounding box: (minx, miny, maxx, maxy)
            idx.insert(i, (lon, lat, lon, lat))
        
        # Cluster endpoints within 1ft = 0.3m
        clusters = {}  # cluster_id -> [segment_ids]
        processed = set()
        cluster_id = 0
        
        # Convert 0.3m to degrees (approximate)
        radius_degrees = 0.3 / 111319.9  # ~2.7e-6 degrees
        
        for i, (coord, seg_id) in enumerate(endpoints):
            if i in processed:
                continue
            
            lon, lat = coord
            
            # Find all endpoints within clustering radius using RTree
            cluster_segments = {seg_id}
            processed.add(i)
            
            # Query RTree for nearby points
            bbox = (lon - radius_degrees, lat - radius_degrees, 
                   lon + radius_degrees, lat + radius_degrees)
            
            for j in idx.intersection(bbox):
                if j in processed or j == i:
                    continue
                
                other_coord, other_seg_id = endpoints[j]
                
                # Double-check with precise distance (RTree uses bounding box)
                if TripGenerator.fast_distance(coord, other_coord) <= 0.3:  # 1ft
                    cluster_segments.add(other_seg_id)
                    processed.add(j)
            
            # Only create cluster if multiple segments connect
            if len(cluster_segments) > 1:
                clusters[cluster_id] = list(cluster_segments)
                cluster_id += 1
        
        print(f"Found {len(clusters)} endpoint clusters (intersections)")
        return clusters
    
    def build_segment_adjacency(self, endpoint_clusters: Dict[int, List[int]]):
        """Build adjacency list: segment -> connected segments."""
        for cluster_segments in endpoint_clusters.values():
            # Each segment in cluster is connected to all others
            for seg_id in cluster_segments:
                for other_seg_id in cluster_segments:
                    if seg_id != other_seg_id:
                        self.segment_adjacency[seg_id].add(other_seg_id)
    
    def validate_segment_connectivity(self):
        """Report connectivity statistics."""
        connected_segments = len(self.segment_adjacency)
        total_segments = len(self.segments)
        
        if connected_segments > 0:
            avg_connections = sum(len(connections) for connections in self.segment_adjacency.values()) / connected_segments
            max_connections = max(len(connections) for connections in self.segment_adjacency.values())
            
            # Show some examples
            print("Sample connections:")
            for seg_id, connections in list(self.segment_adjacency.items())[:3]:
                segment_name = next((s['name'] for s in self.segments if s['id'] == seg_id), f"ID:{seg_id}")
                print(f"  {segment_name} connects to {len(connections)} segments")
        else:
            avg_connections = max_connections = 0
        
        print(f"Segment connectivity: {connected_segments}/{total_segments} connected, "
              f"avg {avg_connections:.1f} connections, max {max_connections}")
        
        # Check if low connectivity might be the issue
        if connected_segments < total_segments * 0.5:
            print("WARNING: Less than 50% of segments are connected - this may cause routing issues")
    
    
    @staticmethod
    def fast_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Fast approximate distance for short distances - much faster than haversine."""
        lon1, lat1 = point1
        lon2, lat2 = point2
        
        # For short distances, simple Euclidean with lat/lon scaling is fine
        # Approximate conversion: 1 degree ≈ 111,319.9 meters
        dlat = (lat2 - lat1) * 111319.9
        dlon = (lon2 - lon1) * 111319.9 * math.cos(math.radians((lat1 + lat2) / 2))
        
        return math.sqrt(dlat * dlat + dlon * dlon)
    
    @staticmethod
    def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate the distance between two lat/lon points in meters using haversine formula."""
        if point1 == point2:
            return 0.0
            
        lon1, lat1 = point1  # GeoJSON uses [lon, lat]
        lon2, lat2 = point2
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula - optimized
        a = (math.sin(delta_lat * 0.5) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon * 0.5) ** 2)
        
        return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def get_segments_near_center(self, center: Tuple[float, float], radius_meters: float) -> List[Dict]:
        """Get all segments within a specified radius of the center point using RTree."""
        # Build RTree index for segments if not already built
        if not hasattr(self, '_segment_rtree'):
            self._build_segment_rtree()
        
        center_lon, center_lat = center
        radius_degrees = radius_meters / 111319.9  # Convert to degrees
        
        # Query RTree for segments in bounding box
        bbox = (center_lon - radius_degrees, center_lat - radius_degrees,
                center_lon + radius_degrees, center_lat + radius_degrees)
        
        nearby_segments = []
        candidate_indices = list(self._segment_rtree.intersection(bbox))
        
        for seg_idx in candidate_indices:
            segment = self.segments[seg_idx]
            if not segment['coordinates']:
                continue
            
            # Check precise distance to segment
            min_distance = float('inf')
            for coord in segment['coordinates']:
                distance = TripGenerator.fast_distance(center, coord)
                min_distance = min(min_distance, distance)
                if min_distance <= radius_meters:  # Early exit if close enough
                    break
            
            if min_distance <= radius_meters:
                segment_copy = segment.copy()
                segment_copy['distance_to_center'] = min_distance
                nearby_segments.append(segment_copy)
        
        return sorted(nearby_segments, key=lambda x: x['distance_to_center'])
    
    def _build_segment_rtree(self):
        """Build RTree spatial index for segments (called once, cached)."""
        print("Building segment RTree index...")
        self._segment_rtree = index.Index()
        
        for i, segment in enumerate(self.segments):
            if not segment['coordinates']:
                continue
            
            # Calculate bounding box for segment
            lons = [coord[0] for coord in segment['coordinates']]
            lats = [coord[1] for coord in segment['coordinates']]
            
            bbox = (min(lons), min(lats), max(lons), max(lats))
            self._segment_rtree.insert(i, bbox)
        
        print(f"Built RTree index for {len(self.segments)} segments")
    
    def find_route_between_segments(self, start_segment_id: int, end_segment_id: int) -> Optional[List[int]]:
        """Find route between two segments using BFS on segment adjacency graph."""
        if start_segment_id == end_segment_id:
            return [start_segment_id]
        
        if start_segment_id not in self.segment_adjacency:
            return None
        
        # BFS to find path
        queue = deque([(start_segment_id, [start_segment_id])])
        visited = {start_segment_id}
        
        while queue:
            current_seg, path = queue.popleft()
            
            for next_seg in self.segment_adjacency[current_seg]:
                if next_seg == end_segment_id:
                    return path + [next_seg]
                
                if next_seg not in visited:
                    visited.add(next_seg)
                    queue.append((next_seg, path + [next_seg]))
        
        return None  # No path found
    
    def get_route_coordinates(self, segment_path: List[int]) -> List[Tuple[float, float]]:
        """Convert segment path to coordinate sequence, ensuring segments connect properly."""
        if not segment_path:
            return []
        
        # Get segment objects
        segment_dict = {seg['id']: seg for seg in self.segments}
        route_coords = []
        
        for i, seg_id in enumerate(segment_path):
            segment = segment_dict.get(seg_id)
            if not segment or not segment['coordinates']:
                print(f"Warning: Segment {seg_id} not found or has no coordinates")
                continue
            
            seg_coords = segment['coordinates'].copy()
            
            if i == 0:
                # First segment - add all coordinates
                route_coords.extend(seg_coords)
            else:
                # Need to connect to previous segment properly
                if route_coords:
                    last_coord = route_coords[-1]
                    
                    # Simple approach: check endpoints, choose direction, use full segments
                    dist_to_start = TripGenerator.fast_distance(last_coord, seg_coords[0])
                    dist_to_end = TripGenerator.fast_distance(last_coord, seg_coords[-1])
                    
                    # Choose direction based on which endpoint is closer
                    if dist_to_end < dist_to_start:
                        seg_coords = seg_coords[::-1]
                        connection_dist = dist_to_end
                    else:
                        connection_dist = dist_to_start
                    
                    # Only skip first coordinate if it's very close (< 3m) to avoid duplication
                    if connection_dist < 3:
                        route_coords.extend(seg_coords[1:])
                    else:
                        route_coords.extend(seg_coords)
                else:
                    route_coords.extend(seg_coords)
        
        return route_coords
    
    
    def generate_trips(self, center: Tuple[float, float], radius_meters: float, 
                      num_trips: int, time_period_hours: int = 1) -> List[Dict]:
        """Generate random trips based on traffic data around a center point."""
        nearby_segments = self.get_segments_near_center(center, radius_meters)
        
        if not nearby_segments:
            print(f"No segments found within {radius_meters}m of center {center}")
            return []
        
        print(f"Found {len(nearby_segments)} segments within {radius_meters}m")
        
        # Check if we have any connected segments for routing
        connected_nearby = [seg for seg in nearby_segments if seg['id'] in self.segment_adjacency]
        if not connected_nearby:
            print("Warning: No connected segments found - using all segments")
            connected_nearby = nearby_segments
        
        # Create weighted list - ignore AWT counts for segments within 5 miles of center
        weighted_segments = []
        five_miles_meters = 5 * 1609.34  # 5 miles in meters
        
        for segment in connected_nearby:
            # Check if segment is within 5 miles of center
            if segment.get('distance_to_center', 0) <= five_miles_meters:
                # Within 5 miles - use equal weighting (ignore AWT counts)
                weighted_segments.append(segment)
            else:
                # Beyond 5 miles - use traffic count as weight
                weight = max(1, segment['traffic_count'])
                # Normalize by time period (traffic count is typically daily)
                hourly_weight = weight / 24 * time_period_hours
                weighted_segments.extend([segment] * max(1, int(hourly_weight / 100)))  # Scale down for reasonable list size
        
        if not weighted_segments:
            weighted_segments = connected_nearby  # Fallback to unweighted
        
        trips = []
        
        for i in range(num_trips):
            # Select origin and destination segments
            origin_segment = random.choice(weighted_segments)
            destination_segment = random.choice(weighted_segments)
            
            # Get random points along the selected segments
            origin_coords = TripGenerator.get_random_point_on_segment(origin_segment)
            destination_coords = TripGenerator.get_random_point_on_segment(destination_segment)
            
            # Find actual route between segments
            segment_path = self.find_route_between_segments(origin_segment['id'], destination_segment['id'])
            
            if segment_path and len(segment_path) > 1:
                route_coords = self.get_route_coordinates(segment_path)
                # Adjust start and end to actual trip points
                if route_coords:
                    route_coords[0] = origin_coords
                    route_coords[-1] = destination_coords
            else:
                # Fallback to direct line if no route found
                route_coords = [origin_coords, destination_coords]
                segment_path = [origin_segment['id'], destination_segment['id']]
                print(f"Warning: No route found for trip {i + 1} (from seg {origin_segment['id']} to {destination_segment['id']}), using direct line")
            
            # Calculate trip distance along route
            trip_distance = TripGenerator.calculate_route_distance(route_coords)
            
            trip = {
                'trip_id': i + 1,
                'origin': {
                    'coordinates': origin_coords,
                    'segment_name': origin_segment['name'],
                    'segment_id': origin_segment['id'],
                    'traffic_count': origin_segment['traffic_count']
                },
                'destination': {
                    'coordinates': destination_coords,
                    'segment_name': destination_segment['name'],
                    'segment_id': destination_segment['id'],
                    'traffic_count': destination_segment['traffic_count']
                },
                'route_coordinates': route_coords,
                'segment_path': segment_path,
                'distance_meters': trip_distance,
                'route_segments': len(segment_path),
                'generated_at': f"Within {radius_meters}m of {center}"
            }
            
            trips.append(trip)
        
        return trips
    
    @staticmethod
    def get_random_point_on_segment(segment: Dict) -> Tuple[float, float]:
        """Get a random point along a line segment."""
        coordinates = segment['coordinates']
        if len(coordinates) < 2:
            return coordinates[0] if coordinates else (0, 0)
        
        # Choose a random segment if LineString has multiple segments
        if len(coordinates) > 2:
            seg_idx = random.randint(0, len(coordinates) - 2)
            start_point = coordinates[seg_idx]
            end_point = coordinates[seg_idx + 1]
        else:
            start_point = coordinates[0]
            end_point = coordinates[1]
        
        # Linear interpolation along the segment
        t = random.random()
        lon = start_point[0] + t * (end_point[0] - start_point[0])
        lat = start_point[1] + t * (end_point[1] - start_point[1])
        
        return lon, lat
    
    @staticmethod
    def calculate_route_distance(route_coords: List[Tuple[float, float]]) -> float:
        """Calculate total distance along a route."""
        if len(route_coords) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(route_coords) - 1):
            total_distance += TripGenerator.calculate_distance(route_coords[i], route_coords[i + 1])
        
        return total_distance
    
    @staticmethod
    def export_trips_geojson(trips: List[Dict], output_path: str):
        """Export trips as GeoJSON file."""
        features = []
        
        for trip in trips:
            # Create LineString from the actual route coordinates
            line_feature = {
                "type": "Feature",
                "properties": {
                    "trip_id": trip['trip_id'],
                    "origin_segment": trip['origin']['segment_name'],
                    "destination_segment": trip['destination']['segment_name'],
                    "distance_meters": trip['distance_meters'],
                    "route_segments": trip['route_segments'],
                    "segment_path": trip['segment_path'],
                    "origin_traffic_count": trip['origin']['traffic_count'],
                    "destination_traffic_count": trip['destination']['traffic_count']
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": trip['route_coordinates']
                }
            }
            features.append(line_feature)
        
        geojson_output = {
            "type": "FeatureCollection",
            "features": features
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson_output, f, indent=2)
        
        print(f"Exported {len(trips)} trips to {output_path}")
    
    
    @staticmethod
    def print_summary(trips: List[Dict]):
        """Print a summary of generated trips."""
        if not trips:
            print("No trips generated.")
            return
        
        print(f"\nTrip Generation Summary:")
        print(f"Total trips: {len(trips)}")
        
        distances = [trip['distance_meters'] for trip in trips]
        print(f"Distance range: {min(distances):.0f}m - {max(distances):.0f}m")
        print(f"Average distance: {np.mean(distances):.0f}m")
        
        # Count unique segments used
        origin_segments = set(trip['origin']['segment_id'] for trip in trips)
        dest_segments = set(trip['destination']['segment_id'] for trip in trips)
        all_segments = origin_segments.union(dest_segments)
        print(f"Unique segments used: {len(all_segments)}")
        
        # Show some example trips
        print(f"\nSample trips:")
        for i, trip in enumerate(trips[:3]):
            route_info = f"{trip['route_segments']} segments, {trip['distance_meters']:.0f}m"
            print(f"  Trip {trip['trip_id']}: {trip['origin']['segment_name']} -> {trip['destination']['segment_name']} ({route_info})")


def main():
    """Example usage of the TripGenerator."""
    # Initialize the trip generator
    generator = TripGenerator('traffic.geojson')
    
    # Define a center point (longitude, latitude) - example coordinates for Madison, WI area
    center_point = (-89.40902500577803, 43.073265957414826)  # Approximate center of the traffic data
    radius_meters = 8000
    num_trips = 500
    
    print(f"Generating {num_trips} trips within {radius_meters}m of {center_point}")
    
    
    # Generate trips
    trips = generator.generate_trips(
        center=center_point,
        radius_meters=radius_meters,
        num_trips=num_trips,
        time_period_hours=1
    )
    
    # Print summary
    TripGenerator.print_summary(trips)
    
    # Export to GeoJSON
    TripGenerator.export_trips_geojson(trips, 'generated_trips.geojson')
    
    
    return trips


if __name__ == "__main__":
    main()