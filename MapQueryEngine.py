# MapQueryEngine.py
# Part of the MapAI subsystem for D&D5e CoreAI integration
# Handles map queries, geographical functions, and provides map data to CoreAI

import os
import json
import logging
import time
from typing import Dict, List, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mapai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MapQueryEngine")


class MapQueryEngine:
    """
    Processes and responds to queries from CoreAI about the fantasy world map.
    Interfaces with Azgaar's Map Generator data to provide geographical information,
    locations, political entities, and other map-related data.
    """

    def __init__(self,
                 map_file_path: str = "C:\\DnD5e\\Mapping\\Test.map",
                 map_data_path: str = "C:\\MapAI\\MapData",
                 lazy_loading: bool = False):
        """
        Initialize the Map Query Engine.

        Args:
            map_file_path: Path to the Azgaar map file (.map format)
            map_data_path: Path to store cached map data
            lazy_loading: Whether to load components on demand (True) or at startup (False)
        """
        # Configure logging
        logger.info("Initializing Map Query Engine...")

        # Set core paths and configurations
        self.map_file_path = map_file_path
        self.map_data_path = map_data_path
        self.lazy_loading = lazy_loading

        # Initialize state
        self.map_data = None
        self.map_cache = {}
        self.last_query_time = 0
        self.query_history = []

        # Load map data if not using lazy loading
        if not lazy_loading:
            self._load_map_data()

        logger.info("Map Query Engine initialized successfully")

    def _load_map_data(self) -> None:
        """
        Load map data from Azgaar's map file.
        Handles both .map format and .json exports.
        """
        try:
            # Check file extension
            file_extension = os.path.splitext(self.map_file_path)[1].lower()

            if file_extension == '.map':
                logger.info(f"Loading map data from .map file: {self.map_file_path}")
                self.map_data = self._load_map_format()
            elif file_extension == '.json':
                logger.info(f"Loading map data from JSON export: {self.map_file_path}")
                self.map_data = self._load_json_format()
            else:
                logger.error(f"Unsupported map file format: {file_extension}")
                raise ValueError(f"Unsupported map file format: {file_extension}")

            # Log success
            if self.map_data:
                logger.info(f"Map data loaded successfully with {len(self.map_data.get('cells', []))} cells")
            else:
                logger.warning("Map data loaded but appears to be empty")

        except Exception as e:
            logger.error(f"Error loading map data: {e}")
            # Create empty map data structure as fallback
            self.map_data = self._create_empty_map_data()

    def _load_map_format(self) -> Dict[str, Any]:
        """
        Load and parse Azgaar's .map format file.
        """
        try:
            with open(self.map_file_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            return map_data
        except Exception as e:
            logger.error(f"Error parsing .map file: {e}")
            return self._create_empty_map_data()

    def _load_json_format(self) -> Dict[str, Any]:
        """
        Load and parse Azgaar's JSON export format.
        """
        try:
            with open(self.map_file_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            return map_data
        except Exception as e:
            logger.error(f"Error parsing JSON export file: {e}")
            return self._create_empty_map_data()

    def _create_empty_map_data(self) -> Dict[str, Any]:
        """
        Create an empty map data structure as fallback.
        """
        return {
            "info": {
                "name": "Empty Map",
                "description": "Fallback empty map",
                "version": "0.1",
                "created": time.time()
            },
            "cells": [],
            "burgs": [],
            "states": [],
            "provinces": [],
            "cultures": [],
            "religions": [],
            "markers": [],
            "rivers": []
        }

    def process_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query from CoreAI about the map.

        Args:
            query: Dictionary with query parameters

        Returns:
            Result of the query processing
        """
        # Log query
        logger.info(f"Processing map query: {query}")
        self.last_query_time = time.time()
        self.query_history.append({"time": self.last_query_time, "query": query})

        # Ensure map data is loaded (lazy loading)
        if self.map_data is None:
            self._load_map_data()

        # Get query type
        query_type = query.get('type', '').lower()

        # Define valid query types
        valid_query_types = {
            'location': self._process_location_query,
            'distance': self._process_distance_query,
            'path': self._process_path_query,
            'region': self._process_region_query,
            'political': self._process_political_query,
            'marker': self._process_marker_query,
            'terrain': self._process_terrain_query,
            'list': self._process_list_query
        }

        # Process query using appropriate method
        if query_type in valid_query_types:
            return valid_query_types[query_type](query)
        else:
            logger.warning(f"Unhandled query type: {query_type}")
            return {
                'status': 'error',
                'message': f"Unknown query type: {query_type}. Valid types are: {', '.join(valid_query_types.keys())}"
            }

    def _process_location_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process location-based queries (get details about a specific location).
        """
        location_id = query.get('location_id')
        location_name = query.get('name')

        # Check if we have a location ID or name
        if not location_id and not location_name:
            return {
                'status': 'error',
                'message': "Location query requires either location_id or name parameter"
            }

        # Search by ID if provided
        if location_id:
            location = self._find_location_by_id(location_id)
            if location:
                return {
                    'status': 'success',
                    'location': location
                }

        # Search by name if provided or ID search failed
        if location_name:
            locations = self._find_locations_by_name(location_name)
            if locations:
                return {
                    'status': 'success',
                    'locations': locations
                }

        # If we get here, we couldn't find the location
        search_term = location_id or location_name
        return {
            'status': 'error',
            'message': f"Could not find location: {search_term}"
        }

    def _process_distance_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process distance queries (distance between two locations).
        """
        from_id = query.get('from_id')
        to_id = query.get('to_id')
        from_name = query.get('from_name')
        to_name = query.get('to_name')

        # Check if we have enough information
        if not (from_id or from_name) or not (to_id or to_name):
            return {
                'status': 'error',
                'message': "Distance query requires both origin and destination (by ID or name)"
            }

        # Find the locations
        from_location = None
        to_location = None

        if from_id:
            from_location = self._find_location_by_id(from_id)
        elif from_name:
            locations = self._find_locations_by_name(from_name)
            if locations:
                from_location = locations[0]  # Use first match

        if to_id:
            to_location = self._find_location_by_id(to_id)
        elif to_name:
            locations = self._find_locations_by_name(to_name)
            if locations:
                to_location = locations[0]  # Use first match

        # Check if we found both locations
        if not from_location:
            return {
                'status': 'error',
                'message': f"Could not find origin location: {from_id or from_name}"
            }

        if not to_location:
            return {
                'status': 'error',
                'message': f"Could not find destination location: {to_id or to_name}"
            }

        # Calculate distance
        distance = self._calculate_distance(from_location, to_location)
        travel_time = self._estimate_travel_time(distance, query.get('travel_method', 'walking'))

        return {
            'status': 'success',
            'from': from_location,
            'to': to_location,
            'distance': distance,
            'unit': 'miles',
            'travel_time': travel_time
        }

    def _process_path_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process path queries (find path between locations).
        """
        from_id = query.get('from_id')
        to_id = query.get('to_id')
        from_name = query.get('from_name')
        to_name = query.get('to_name')
        travel_method = query.get('travel_method', 'walking')

        # Check if we have enough information
        if not (from_id or from_name) or not (to_id or to_name):
            return {
                'status': 'error',
                'message': "Path query requires both origin and destination (by ID or name)"
            }

        # Find the locations
        from_location = None
        to_location = None

        if from_id:
            from_location = self._find_location_by_id(from_id)
        elif from_name:
            locations = self._find_locations_by_name(from_name)
            if locations:
                from_location = locations[0]  # Use first match

        if to_id:
            to_location = self._find_location_by_id(to_id)
        elif to_name:
            locations = self._find_locations_by_name(to_name)
            if locations:
                to_location = locations[0]  # Use first match

        # Check if we found both locations
        if not from_location:
            return {
                'status': 'error',
                'message': f"Could not find origin location: {from_id or from_name}"
            }

        if not to_location:
            return {
                'status': 'error',
                'message': f"Could not find destination location: {to_id or to_name}"
            }

        # Calculate path
        path = self._find_path(from_location, to_location, travel_method)

        if not path:
            return {
                'status': 'error',
                'message': f"Could not find path from {from_location.get('name')} to {to_location.get('name')}"
            }

        # Calculate total distance and travel time
        total_distance = sum(segment.get('distance', 0) for segment in path)
        total_travel_time = self._estimate_travel_time(total_distance, travel_method)

        return {
            'status': 'success',
            'from': from_location,
            'to': to_location,
            'path': path,
            'total_distance': total_distance,
            'unit': 'miles',
            'travel_time': total_travel_time,
            'travel_method': travel_method
        }

    def _process_region_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process region queries (get information about a geographical region).
        """
        region_id = query.get('region_id')
        region_name = query.get('name')
        region_type = query.get('type', 'province')  # province, state, biome, etc.

        # Check if we have a region ID or name
        if not region_id and not region_name:
            return {
                'status': 'error',
                'message': "Region query requires either region_id or name parameter"
            }

        # Determine which collection to search based on region type
        collection_map = {
            'province': 'provinces',
            'state': 'states',
            'culture': 'cultures',
            'religion': 'religions',
            'biome': 'biomes'
        }

        collection = collection_map.get(region_type)
        if not collection or collection not in self.map_data:
            return {
                'status': 'error',
                'message': f"Invalid region type: {region_type}"
            }

        # Search by ID if provided
        if region_id:
            region = self._find_by_id(self.map_data[collection], region_id)
            if region:
                # Enhance with additional information
                region_details = self._get_region_details(region, region_type)
                return {
                    'status': 'success',
                    'region': region_details
                }

        # Search by name if provided or ID search failed
        if region_name:
            regions = self._find_by_name(self.map_data[collection], region_name)
            if regions:
                # Enhance with additional information
                regions_with_details = [self._get_region_details(r, region_type) for r in regions]
                return {
                    'status': 'success',
                    'regions': regions_with_details
                }

        # If we get here, we couldn't find the region
        search_term = region_id or region_name
        return {
            'status': 'error',
            'message': f"Could not find {region_type}: {search_term}"
        }

    def _process_political_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process political queries (get information about political entities).
        """
        entity_id = query.get('entity_id')
        entity_name = query.get('name')
        entity_type = query.get('type', 'state')  # state, culture, religion
        relation_to = query.get('relation_to')  # Get relations to another entity

        # Check if we have an entity ID or name
        if not entity_id and not entity_name:
            return {
                'status': 'error',
                'message': "Political query requires either entity_id or name parameter"
            }

        # Determine which collection to search based on entity type
        collection_map = {
            'state': 'states',
            'culture': 'cultures',
            'religion': 'religions'
        }

        collection = collection_map.get(entity_type)
        if not collection or collection not in self.map_data:
            return {
                'status': 'error',
                'message': f"Invalid political entity type: {entity_type}"
            }

        # Search by ID if provided
        entity = None
        if entity_id:
            entity = self._find_by_id(self.map_data[collection], entity_id)

        # Search by name if provided or ID search failed
        if not entity and entity_name:
            entities = self._find_by_name(self.map_data[collection], entity_name)
            if entities:
                entity = entities[0]  # Use first match

        # If we couldn't find the entity
        if not entity:
            search_term = entity_id or entity_name
            return {
                'status': 'error',
                'message': f"Could not find {entity_type}: {search_term}"
            }

        # Enhance with additional information
        entity_details = self._get_political_details(entity, entity_type)

        # If we want relations to another entity
        if relation_to:
            relation_entity = None
            if isinstance(relation_to, int):
                relation_entity = self._find_by_id(self.map_data[collection], relation_to)
            else:
                relation_entities = self._find_by_name(self.map_data[collection], relation_to)
                if relation_entities:
                    relation_entity = relation_entities[0]  # Use first match

            if relation_entity:
                relations = self._get_relations(entity, relation_entity, entity_type)
                entity_details['relations_to'] = relations

        return {
            'status': 'success',
            'entity': entity_details
        }

    def _process_marker_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process marker queries (get information about map markers).
        """
        marker_id = query.get('marker_id')
        marker_type = query.get('type')
        location_id = query.get('location_id')

        # Check if we have enough parameters
        if not marker_id and not marker_type and not location_id:
            return {
                'status': 'error',
                'message': "Marker query requires at least one of: marker_id, type, or location_id"
            }

        # Ensure markers exist in map data
        if 'markers' not in self.map_data or not self.map_data['markers']:
            return {
                'status': 'error',
                'message': "No markers found in map data"
            }

        # Search by ID if provided
        if marker_id:
            marker = self._find_by_id(self.map_data['markers'], marker_id)
            if marker:
                return {
                    'status': 'success',
                    'marker': marker
                }
            return {
                'status': 'error',
                'message': f"Could not find marker with ID: {marker_id}"
            }

        # Search by type if provided
        if marker_type:
            markers = [m for m in self.map_data['markers'] if m.get('type') == marker_type]
            if markers:
                return {
                    'status': 'success',
                    'markers': markers
                }
            return {
                'status': 'error',
                'message': f"No markers found of type: {marker_type}"
            }

        # Search by location if provided
        if location_id:
            markers = [m for m in self.map_data['markers'] if m.get('cell') == location_id]
            if markers:
                return {
                    'status': 'success',
                    'markers': markers
                }
            return {
                'status': 'error',
                'message': f"No markers found at location: {location_id}"
            }

    def _process_terrain_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process terrain queries (get information about terrain and biomes).
        """
        location_id = query.get('location_id')
        biome_type = query.get('biome')

        # Check if we have enough parameters
        if not location_id and not biome_type:
            return {
                'status': 'error',
                'message': "Terrain query requires at least one of: location_id or biome"
            }

        # Search by location ID if provided
        if location_id:
            cell = self._find_by_id(self.map_data['cells'], location_id)
            if cell:
                terrain_info = self._get_terrain_info(cell)
                return {
                    'status': 'success',
                    'terrain': terrain_info
                }
            return {
                'status': 'error',
                'message': f"Could not find location with ID: {location_id}"
            }

        # Search by biome type if provided
        if biome_type:
            cells = [c for c in self.map_data['cells'] if c.get('biome') == biome_type]
            if cells:
                return {
                    'status': 'success',
                    'locations': [self._get_cell_location(c) for c in cells]
                }
            return {
                'status': 'error',
                'message': f"No locations found with biome: {biome_type}"
            }

    def _process_list_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process list queries (get lists of entities).
        """
        entity_type = query.get('type', 'burgs')  # burgs, states, cultures, etc.
        limit = query.get('limit', 100)
        offset = query.get('offset', 0)
        filters = query.get('filters', {})

        # Valid entity types
        valid_types = [
            'burgs', 'states', 'provinces', 'cultures',
            'religions', 'rivers', 'markers'
        ]

        if entity_type not in valid_types:
            return {
                'status': 'error',
                'message': f"Invalid entity type: {entity_type}. Valid types: {', '.join(valid_types)}"
            }

        # Ensure entity type exists in map data
        if entity_type not in self.map_data or not self.map_data[entity_type]:
            return {
                'status': 'error',
                'message': f"No {entity_type} found in map data"
            }

        # Apply filters
        filtered_entities = self._apply_filters(self.map_data[entity_type], filters)

        # Apply pagination
        paginated_entities = filtered_entities[offset:offset + limit]

        return {
            'status': 'success',
            'total': len(filtered_entities),
            'limit': limit,
            'offset': offset,
            'entities': paginated_entities
        }

    def _find_location_by_id(self, location_id: int) -> Optional[Dict[str, Any]]:
        """
        Find a location by its ID.
        Searches in burgs and cells.
        """
        # Check burgs first (settlements)
        if 'burgs' in self.map_data:
            for burg in self.map_data['burgs']:
                if burg.get('i') == location_id:
                    return burg

        # Check cells (geographical locations)
        if 'cells' in self.map_data:
            for cell in self.map_data['cells']:
                if cell.get('i') == location_id:
                    return cell

        return None

    def _find_locations_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Find locations by name (full or partial match).
        Searches in burgs and cells with featureNames.
        """
        locations = []
        name_lower = name.lower()

        # Check burgs first (settlements)
        if 'burgs' in self.map_data:
            for burg in self.map_data['burgs']:
                if burg.get('name', '').lower().find(name_lower) >= 0:
                    locations.append(burg)

        # Check cells with feature names (geographical locations)
        if 'cells' in self.map_data:
            for cell in self.map_data['cells']:
                feature_name = cell.get('featureName', '')
                if feature_name and feature_name.lower().find(name_lower) >= 0:
                    locations.append(cell)

        return locations

    def _find_by_id(self, collection: List[Dict[str, Any]], entity_id: int) -> Optional[Dict[str, Any]]:
        """
        Find an entity by its ID in a collection.
        """
        for entity in collection:
            if entity.get('i') == entity_id:
                return entity
        return None

    def _find_by_name(self, collection: List[Dict[str, Any]], name: str) -> List[Dict[str, Any]]:
        """
        Find entities by name (full or partial match) in a collection.
        """
        entities = []
        name_lower = name.lower()

        for entity in collection:
            if entity.get('name', '').lower().find(name_lower) >= 0:
                entities.append(entity)

        return entities

    def _calculate_distance(self, from_location: Dict[str, Any], to_location: Dict[str, Any]) -> float:
        """
        Calculate distance between two locations.
        """
        # Get coordinates
        from_x = from_location.get('x', from_location.get('point', [0, 0])[0])
        from_y = from_location.get('y', from_location.get('point', [0, 0])[1])
        to_x = to_location.get('x', to_location.get('point', [0, 0])[0])
        to_y = to_location.get('y', to_location.get('point', [0, 0])[1])

        # Calculate Euclidean distance
        dx = to_x - from_x
        dy = to_y - from_y
        raw_distance = (dx * dx + dy * dy) ** 0.5

        # Convert to map units
        # Assumption: 1 map unit = 1 mile (this can be adjusted based on map scale)
        map_scale = self.map_data.get('info', {}).get('mapScale', 1)
        distance_miles = raw_distance * map_scale

        return round(distance_miles, 2)

    def _estimate_travel_time(self, distance: float, travel_method: str) -> Dict[str, Any]:
        """
        Estimate travel time based on distance and travel method.
        """
        # Travel speeds in miles per day
        travel_speeds = {
            'walking': 24,  # 3 mph for 8 hours
            'horseback': 40,  # 5 mph for 8 hours
            'carriage': 32,  # 4 mph for 8 hours
            'ship': 72,  # 3 mph for 24 hours (ocean travel)
            'river_boat': 48,  # 2 mph for 24 hours (upstream)
            'river_boat_downstream': 96,  # 4 mph for 24 hours (downstream)
            'fast_mount': 56,  # 7 mph for 8 hours
            'magical': 240  # 10 mph for 24 hours (no rest needed)
        }

        # Get travel speed for method
        speed = travel_speeds.get(travel_method.lower(), travel_speeds['walking'])

        # Calculate days and hours
        total_hours = (distance / (speed / 24))
        days = int(total_hours / 24)
        hours = int(total_hours % 24)

        return {
            'days': days,
            'hours': hours,
            'method': travel_method,
            'speed_per_day': speed
        }

    def _find_path(self, from_location: Dict[str, Any], to_location: Dict[str, Any],
                   travel_method: str) -> List[Dict[str, Any]]:
        """
        Find a path between two locations.

        In a real implementation, this would use pathfinding algorithms like A*
        considering terrain type, roads, rivers, etc. For now, using a simplified approach.
        """
        # Get coordinates
        from_x = from_location.get('x', from_location.get('point', [0, 0])[0])
        from_y = from_location.get('y', from_location.get('point', [0, 0])[1])
        to_x = to_location.get('x', to_location.get('point', [0, 0])[0])
        to_y = to_location.get('y', to_location.get('point', [0, 0])[1])

        # For this simplified implementation, we'll just create a direct path
        # In a real implementation, we would find intermediate points based on roads, etc.
        direct_distance = self._calculate_distance(from_location, to_location)

        # Check if there are roads connecting these points
        road_path = self._check_for_road_path(from_location, to_location)
        if road_path:
            return road_path

        # Simple direct path
        path = [{
            'from': {
                'id': from_location.get('i'),
                'name': from_location.get('name', f"Location {from_location.get('i')}"),
                'x': from_x,
                'y': from_y
            },
            'to': {
                'id': to_location.get('i'),
                'name': to_location.get('name', f"Location {to_location.get('i')}"),
                'x': to_x,
                'y': to_y
            },
            'distance': direct_distance,
            'terrain': self._get_terrain_between(from_location, to_location),
            'travel_method': travel_method
        }]

        return path

    def _check_for_road_path(self, from_location: Dict[str, Any], to_location: Dict[str, Any]) -> Optional[
        List[Dict[str, Any]]]:
        """
        Check if there's a road path between two locations.
        Returns the path if found, None otherwise.
        """
        # This would normally use a graph search algorithm with the roads data
        # For now, returning None as a placeholder
        return None

    def _get_terrain_between(self, from_location: Dict[str, Any], to_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get terrain information for the area between two locations.
        """
        # In a real implementation, this would analyze the cells between the locations
        # For now, providing a simplified approximation

        # Get cells corresponding to the locations
        from_cell = None
        to_cell = None

        if 'cell' in from_location:
            from_cell = self._find_by_id(self.map_data['cells'], from_location['cell'])
        elif 'i' in from_location and from_location.get('i') < len(self.map_data.get('cells', [])):
            from_cell = from_location

        if 'cell' in to_location:
            to_cell = self._find_by_id(self.map_data['cells'], to_location['cell'])
        elif 'i' in to_location and to_location.get('i') < len(self.map_data.get('cells', [])):
            to_cell = to_location

        # If we don't have cell data, return default terrain
        if not from_cell or not to_cell:
            return {
                'primary_biome': 'grassland',
                'elevation': 'lowland',
                'obstacles': [],
                'water_features': []
            }

        # Determine dominant terrain between the two cells
        biomes = [from_cell.get('biome'), to_cell.get('biome')]
        from_height = from_cell.get('height', 0)
        to_height = to_cell.get('height', 0)
        avg_height = (from_height + to_height) / 2

        # Check for water obstacles
        water_features = []
        for river in self.map_data.get('rivers', []):
            # Check if river crosses the path (simplified)
            if self._river_crosses_path(river, from_location, to_location):
                water_features.append({
                    'type': 'river',
                    'name': river.get('name', 'Unnamed River'),
                    'id': river.get('i')
                })

        # Determine elevation category
        elevation = 'lowland'
        if avg_height > 70:
            elevation = 'mountain'
        elif avg_height > 40:
            elevation = 'highland'

        # Determine obstacles based on terrain
        obstacles = []
        if 'mountain' in biomes:
            obstacles.append('mountain pass')
        if 'swamp' in biomes:
            obstacles.append('swamp')
        if 'desert' in biomes:
            obstacles.append('desert crossing')
        if 'forest' in biomes or 'jungle' in biomes:
            obstacles.append('dense vegetation')

        return {
            'primary_biome': biomes[0] or 'grassland',
            'secondary_biome': biomes[1] if biomes[0] != biomes[1] else None,
            'elevation': elevation,
            'obstacles': obstacles,
            'water_features': water_features
        }

    def _river_crosses_path(self, river: Dict[str, Any], from_location: Dict[str, Any],
                            to_location: Dict[str, Any]) -> bool:
        """
        Check if a river crosses the path between two locations.

        This is a simplified check. A real implementation would use
        computational geometry to check line intersections.
        """
        # Placeholder - in a real implementation this would check if the river
        # crosses the path between the two locations
        return False

    def _get_region_details(self, region: Dict[str, Any], region_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a region.
        """
        # Base region info
        region_details = {
            'id': region.get('i'),
            'name': region.get('name', f"Unknown {region_type.capitalize()}"),
            'type': region_type
        }

        # Add region-specific details
        if region_type == 'province':
            # Get state information
            state_id = region.get('state')
            if state_id is not None:
                state = self._find_by_id(self.map_data.get('states', []), state_id)
                if state:
                    region_details['state'] = {
                        'id': state.get('i'),
                        'name': state.get('name', 'Unknown State')
                    }

            # Get burgs in province
            burgs = []
            for burg in self.map_data.get('burgs', []):
                if burg.get('province') == region.get('i'):
                    burgs.append({
                        'id': burg.get('i'),
                        'name': burg.get('name', f"Unnamed Burg {burg.get('i')}")
                    })
            region_details['burgs'] = burgs

        elif region_type == 'state':
            # Get culture information
            culture_id = region.get('culture')
            if culture_id is not None:
                culture = self._find_by_id(self.map_data.get('cultures', []), culture_id)
                if culture:
                    region_details['culture'] = {
                        'id': culture.get('i'),
                        'name': culture.get('name', 'Unknown Culture')
                    }

            # Get religion information
            religion_id = region.get('religion')
            if religion_id is not None:
                religion = self._find_by_id(self.map_data.get('religions', []), religion_id)
                if religion:
                    region_details['religion'] = {
                        'id': religion.get('i'),
                        'name': religion.get('name', 'Unknown Religion')
                    }

            # Get capital
            capital_id = region.get('capital')
            if capital_id is not None:
                capital = self._find_by_id(self.map_data.get('burgs', []), capital_id)
                if capital:
                    region_details['capital'] = {
                        'id': capital.get('i'),
                        'name': capital.get('name', f"Unnamed Capital {capital.get('i')}")
                    }

            # Get provinces
            provinces = []
            for province in self.map_data.get('provinces', []):
                if province.get('state') == region.get('i'):
                    provinces.append({
                        'id': province.get('i'),
                        'name': province.get('name', f"Unnamed Province {province.get('i')}")
                    })
            region_details['provinces'] = provinces

        elif region_type == 'biome':
            # Get cells with this biome
            cells = [c for c in self.map_data.get('cells', []) if c.get('biome') == region.get('i')]
            region_details['cell_count'] = len(cells)

            # Get burgs in this biome
            burgs = []
            for burg in self.map_data.get('burgs', []):
                cell = self._find_by_id(self.map_data.get('cells', []), burg.get('cell'))
                if cell and cell.get('biome') == region.get('i'):
                    burgs.append({
                        'id': burg.get('i'),
                        'name': burg.get('name', f"Unnamed Burg {burg.get('i')}")
                    })
            region_details['burgs'] = burgs

        return region_details

    def _get_political_details(self, entity: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a political entity.
        """
        # Base entity info
        entity_details = {
            'id': entity.get('i'),
            'name': entity.get('name', f"Unknown {entity_type.capitalize()}"),
            'type': entity_type
        }

        # Add entity-specific details
        if entity_type == 'state':
            # Get territory information
            provinces = [p for p in self.map_data.get('provinces', []) if p.get('state') == entity.get('i')]
            territory_size = sum(p.get('area', 0) for p in provinces)
            entity_details['territory_size'] = territory_size
            entity_details['province_count'] = len(provinces)

            # Get population information
            burgs = [b for b in self.map_data.get('burgs', []) if b.get('state') == entity.get('i')]
            total_population = sum(b.get('population', 0) for b in burgs)
            entity_details['population'] = total_population
            entity_details['burg_count'] = len(burgs)

            # Get capital
            capital_id = entity.get('capital')
            if capital_id is not None:
                capital = self._find_by_id(self.map_data.get('burgs', []), capital_id)
                if capital:
                    entity_details['capital'] = {
                        'id': capital.get('i'),
                        'name': capital.get('name', 'Unknown Capital')
                    }

            # Get diplomatic relations
            if 'diplomacy' in entity:
                relations = []
                diplomacy = entity.get('diplomacy', [])
                for i, relation in enumerate(diplomacy):
                    if i == entity.get('i') or relation == 'x':
                        continue

                    other_state = self._find_by_id(self.map_data.get('states', []), i)
                    if other_state:
                        relations.append({
                            'state': {
                                'id': other_state.get('i'),
                                'name': other_state.get('name', f"State {other_state.get('i')}")
                            },
                            'relation': relation
                        })
                entity_details['relations'] = relations

        elif entity_type == 'culture':
            # Get states with this culture
            states = [s for s in self.map_data.get('states', []) if s.get('culture') == entity.get('i')]
            entity_details['state_count'] = len(states)
            entity_details['states'] = [{
                'id': s.get('i'),
                'name': s.get('name', f"State {s.get('i')}")
            } for s in states]

            # Get burgs with this culture
            total_population = 0
            burg_count = 0

            for state in states:
                burgs = [b for b in self.map_data.get('burgs', []) if b.get('state') == state.get('i')]
                total_population += sum(b.get('population', 0) for b in burgs)
                burg_count += len(burgs)

            entity_details['population'] = total_population
            entity_details['burg_count'] = burg_count

        elif entity_type == 'religion':
            # Get states with this religion
            states = [s for s in self.map_data.get('states', []) if s.get('religion') == entity.get('i')]
            entity_details['state_count'] = len(states)
            entity_details['states'] = [{
                'id': s.get('i'),
                'name': s.get('name', f"State {s.get('i')}")
            } for s in states]

            # Get population following this religion
            total_population = 0
            burg_count = 0

            for state in states:
                burgs = [b for b in self.map_data.get('burgs', []) if b.get('state') == state.get('i')]
                total_population += sum(b.get('population', 0) for b in burgs)
                burg_count += len(burgs)

            entity_details['population'] = total_population
            entity_details['burg_count'] = burg_count

        return entity_details

    def _get_relations(self, entity1: Dict[str, Any], entity2: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Get relations between two political entities.
        """
        if entity_type != 'state':
            return {'status': 'unknown'}

        # Get diplomatic relation
        diplomacy = entity1.get('diplomacy', [])
        if entity2.get('i') < len(diplomacy):
            relation = diplomacy[entity2.get('i')]
            if relation and relation != 'x':
                return {'status': relation}

        return {'status': 'neutral'}

    def _get_terrain_info(self, cell: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get terrain information for a cell.
        """
        # Basic terrain info
        terrain_info = {
            'biome': cell.get('biome', 'grassland'),
            'height': cell.get('height', 0),
            'flux': cell.get('flux', 0),  # water flux
            'river': cell.get('river', 0) > 0,
            'coast': cell.get('cost', 0) > 0
        }

        # Convert height to elevation category
        height = cell.get('height', 0)
        if height > 70:
            terrain_info['elevation'] = 'mountain'
        elif height > 40:
            terrain_info['elevation'] = 'highland'
        else:
            terrain_info['elevation'] = 'lowland'

        # Add feature name if available
        if 'featureName' in cell:
            terrain_info['feature_name'] = cell['featureName']

        # Add vegetation information
        biome = cell.get('biome')
        if biome in ['forest', 'jungle']:
            terrain_info['vegetation'] = 'dense'
        elif biome in ['grassland', 'savanna']:
            terrain_info['vegetation'] = 'sparse'
        elif biome in ['desert', 'tundra']:
            terrain_info['vegetation'] = 'minimal'
        else:
            terrain_info['vegetation'] = 'moderate'

        return terrain_info

    def _get_cell_location(self, cell: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get location information for a cell.
        """
        location = {
            'id': cell.get('i'),
            'x': cell.get('p', [0, 0])[0],
            'y': cell.get('p', [0, 0])[1]
        }

        # Add feature name if available
        if 'featureName' in cell:
            location['name'] = cell['featureName']

        # Check if there's a burg in this cell
        for burg in self.map_data.get('burgs', []):
            if burg.get('cell') == cell.get('i'):
                location['burg'] = {
                    'id': burg.get('i'),
                    'name': burg.get('name', f"Unnamed Burg {burg.get('i')}")
                }
                break

        # Get province and state
        province_id = cell.get('province')
        if province_id:
            province = self._find_by_id(self.map_data.get('provinces', []), province_id)
            if province:
                location['province'] = {
                    'id': province.get('i'),
                    'name': province.get('name', f"Unnamed Province {province.get('i')}")
                }

                state_id = province.get('state')
                if state_id:
                    state = self._find_by_id(self.map_data.get('states', []), state_id)
                    if state:
                        location['state'] = {
                            'id': state.get('i'),
                            'name': state.get('name', f"Unnamed State {state.get('i')}")
                        }

        return location

    def _apply_filters(self, entities: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of entities.
        """
        if not filters:
            return entities

        filtered = entities.copy()

        # Apply filters
        for key, value in filters.items():
            if isinstance(value, list):
                # List of values (OR condition)
                filtered = [e for e in filtered if e.get(key) in value]
            elif isinstance(value, dict):
                # Range filter
                min_val = value.get('min')
                max_val = value.get('max')

                if min_val is not None:
                    filtered = [e for e in filtered if e.get(key, 0) >= min_val]

                if max_val is not None:
                    filtered = [e for e in filtered if e.get(key, 0) <= max_val]
            else:
                # Exact match
                filtered = [e for e in filtered if e.get(key) == value]

        return filtered

    # Integration methods for CoreAI

    def get_locations_near(self, location_id: int, radius: float = 50) -> Dict[str, Any]:
        """
        Get locations near a specified location.

        Args:
            location_id: ID of the central location
            radius: Radius in miles to search

        Returns:
            Dictionary with nearby locations
        """
        # Find the central location
        location = self._find_location_by_id(location_id)
        if not location:
            return {
                'status': 'error',
                'message': f"Could not find location with ID: {location_id}"
            }

        # Get location coordinates
        loc_x = location.get('x', location.get('p', [0, 0])[0])
        loc_y = location.get('y', location.get('p', [0, 0])[1])

        # Find nearby burgs
        nearby_burgs = []
        for burg in self.map_data.get('burgs', []):
            if 'removed' in burg and burg['removed']:
                continue

            burg_x = burg.get('x', 0)
            burg_y = burg.get('y', 0)

            # Calculate distance
            dx = burg_x - loc_x
            dy = burg_y - loc_y
            distance = (dx * dx + dy * dy) ** 0.5

            # Convert to miles (assuming 1 unit = 1 mile)
            map_scale = self.map_data.get('info', {}).get('mapScale', 1)
            distance_miles = distance * map_scale

            if distance_miles <= radius:
                nearby_burgs.append({
                    'id': burg.get('i'),
                    'name': burg.get('name', f"Unnamed Burg {burg.get('i')}"),
                    'distance': round(distance_miles, 2),
                    'type': 'burg',
                    'population': burg.get('population', 0)
                })

        # Find nearby features (geographic landmarks)
        nearby_features = []
        for cell in self.map_data.get('cells', []):
            if 'featureName' not in cell:
                continue

            cell_x = cell.get('p', [0, 0])[0]
            cell_y = cell.get('p', [0, 0])[1]

            # Calculate distance
            dx = cell_x - loc_x
            dy = cell_y - loc_y
            distance = (dx * dx + dy * dy) ** 0.5

            # Convert to miles
            map_scale = self.map_data.get('info', {}).get('mapScale', 1)
            distance_miles = distance * map_scale

            if distance_miles <= radius:
                nearby_features.append({
                    'id': cell.get('i'),
                    'name': cell.get('featureName'),
                    'distance': round(distance_miles, 2),
                    'type': 'feature',
                    'biome': cell.get('biome', 'unknown')
                })

        return {
            'status': 'success',
            'center': {
                'id': location.get('i'),
                'name': location.get('name', f"Location {location.get('i')}"),
                'type': 'burg' if 'population' in location else 'feature'
            },
            'radius': radius,
            'nearby_burgs': nearby_burgs,
            'nearby_features': nearby_features
        }

    def get_political_info(self, location_id: int) -> Dict[str, Any]:
        """
        Get political information for a location.

        Args:
            location_id: ID of the location

        Returns:
            Dictionary with political information
        """
        # Find the location
        location = self._find_location_by_id(location_id)
        if not location:
            return {
                'status': 'error',
                'message': f"Could not find location with ID: {location_id}"
            }

        # Get cell ID
        cell_id = location.get('cell') if 'cell' in location else location.get('i')
        cell = self._find_by_id(self.map_data.get('cells', []), cell_id)

        if not cell:
            return {
                'status': 'error',
                'message': f"Could not find cell for location: {location_id}"
            }

        # Get province
        province_id = cell.get('province')
        province = None
        if province_id:
            province = self._find_by_id(self.map_data.get('provinces', []), province_id)

        # Get state
        state_id = province.get('state') if province else None
        state = None
        if state_id:
            state = self._find_by_id(self.map_data.get('states', []), state_id)

        # Get culture
        culture_id = state.get('culture') if state else None
        culture = None
        if culture_id:
            culture = self._find_by_id(self.map_data.get('cultures', []), culture_id)

        # Get religion
        religion_id = state.get('religion') if state else None
        religion = None
        if religion_id:
            religion = self._find_by_id(self.map_data.get('religions', []), religion_id)

        # Build response
        political_info = {
            'location': {
                'id': location.get('i'),
                'name': location.get('name', f"Location {location.get('i')}"),
                'type': 'burg' if 'population' in location else 'feature'
            }
        }

        if province:
            political_info['province'] = {
                'id': province.get('i'),
                'name': province.get('name', f"Unnamed Province {province.get('i')}")
            }

        if state:
            political_info['state'] = {
                'id': state.get('i'),
                'name': state.get('name', f"Unnamed State {state.get('i')}")
            }

            # Add capital info
            capital_id = state.get('capital')
            if capital_id:
                capital = self._find_by_id(self.map_data.get('burgs', []), capital_id)
                if capital:
                    political_info['capital'] = {
                        'id': capital.get('i'),
                        'name': capital.get('name', f"Unnamed Capital {capital.get('i')}"),
                        'population': capital.get('population', 0)
                    }

        if culture:
            political_info['culture'] = {
                'id': culture.get('i'),
                'name': culture.get('name', f"Unnamed Culture {culture.get('i')}")
            }

        if religion:
            political_info['religion'] = {
                'id': religion.get('i'),
                'name': religion.get('name', f"Unnamed Religion {religion.get('i')}")
            }

        return {
            'status': 'success',
            'political_info': political_info
        }

    def get_world_overview(self) -> Dict[str, Any]:
        """
        Get a general overview of the world map.

        Returns:
            Dictionary with world overview information
        """
        # Get basic map information
        info = self.map_data.get('info', {})
        map_name = info.get('name', 'Fantasy World')
        seed = info.get('seed', 'unknown')

        # Count entities
        burgs_count = len([b for b in self.map_data.get('burgs', []) if not b.get('removed', False)])
        states_count = len([s for s in self.map_data.get('states', []) if s.get('i', 0) > 0])  # Skip neutrals
        provinces_count = len(self.map_data.get('provinces', []))
        cultures_count = len([c for c in self.map_data.get('cultures', []) if c.get('i', 0) > 0])
        religions_count = len([r for r in self.map_data.get('religions', []) if r.get('i', 0) > 0])

        # Get major states
        major_states = []
        states = sorted(
            [s for s in self.map_data.get('states', []) if s.get('i', 0) > 0],
            key=lambda s: s.get('area', 0),
            reverse=True
        )

        for state in states[:5]:  # Top 5 by area
            burgs = [b for b in self.map_data.get('burgs', []) if b.get('state') == state.get('i')]

            # Get capital
            capital = None
            capital_id = state.get('capital')
            if capital_id:
                capital = self._find_by_id(self.map_data.get('burgs', []), capital_id)

            major_states.append({
                'id': state.get('i'),
                'name': state.get('name', f"State {state.get('i')}"),
                'area': state.get('area', 0),
                'burgs_count': len(burgs),
                'capital': {
                    'id': capital.get('i'),
                    'name': capital.get('name', 'Unknown Capital')
                } if capital else None
            })

        # Get major settlements
        major_settlements = []
        burgs = sorted(
            [b for b in self.map_data.get('burgs', []) if not b.get('removed', False)],
            key=lambda b: b.get('population', 0),
            reverse=True
        )

        for burg in burgs[:10]:  # Top 10 by population
            # Get state
            state = None
            state_id = burg.get('state')
            if state_id:
                state = self._find_by_id(self.map_data.get('states', []), state_id)

            major_settlements.append({
                'id': burg.get('i'),
                'name': burg.get('name', f"Burg {burg.get('i')}"),
                'population': burg.get('population', 0),
                'capital': bool(burg.get('capital', 0)),
                'state': {
                    'id': state.get('i'),
                    'name': state.get('name', 'Unknown State')
                } if state else None
            })

        return {
            'status': 'success',
            'world_name': map_name,
            'seed': seed,
            'counts': {
                'burgs': burgs_count,
                'states': states_count,
                'provinces': provinces_count,
                'cultures': cultures_count,
                'religions': religions_count
            },
            'major_states': major_states,
            'major_settlements': major_settlements
        }

    def generate_encounter_location(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a location-based encounter based on map data.

        Args:
            params: Optional parameters to guide encounter generation

        Returns:
            Dictionary with generated encounter
        """
        # Default parameters
        default_params = {
            'region_type': 'province',
            'region_id': None,
            'biome': None,
            'near_settlement': False,
            'encounter_type': 'random'
        }

        # Merge provided parameters with defaults
        if params:
            default_params.update(params)

        params = default_params

        # Determine location
        location = None

        # If region ID is specified
        if params['region_id']:
            if params['region_type'] == 'province':
                province = self._find_by_id(self.map_data.get('provinces', []), params['region_id'])
                if province:
                    # Find a random cell in the province
                    province_cells = [c for c in self.map_data.get('cells', [])
                                      if c.get('province') == province.get('i')]
                    if province_cells:
                        import random
                        location = random.choice(province_cells)

            elif params['region_type'] == 'state':
                state = self._find_by_id(self.map_data.get('states', []), params['region_id'])
                if state:
                    # Find a random province in the state
                    state_provinces = [p for p in self.map_data.get('provinces', [])
                                       if p.get('state') == state.get('i')]
                    if state_provinces:
                        import random
                        province = random.choice(state_provinces)
                        # Find a random cell in the province
                        province_cells = [c for c in self.map_data.get('cells', [])
                                          if c.get('province') == province.get('i')]
                        if province_cells:
                            location = random.choice(province_cells)

        # If no location found yet and biome is specified
        if not location and params['biome']:
            biome_cells = [c for c in self.map_data.get('cells', [])
                           if c.get('biome') == params['biome']]
            if biome_cells:
                import random
                location = random.choice(biome_cells)

        # If we still have no location, pick a random cell
        if not location:
            import random
            location = random.choice(self.map_data.get('cells', []))

        # If we want to be near a settlement
        nearby_settlement = None
        if params['near_settlement']:
            # Find nearby burgs
            nearby_burgs = []
            for burg in self.map_data.get('burgs', []):
                if burg.get('cell') == location.get('i'):
                    nearby_burgs.append(burg)
                    break

            if not nearby_burgs:
                # Find the closest burg
                min_distance = float('inf')
                closest_burg = None

                loc_x = location.get('p', [0, 0])[0]
                loc_y = location.get('p', [0, 0])[1]

                for burg in self.map_data.get('burgs', []):
                    if 'removed' in burg and burg['removed']:
                        continue

                    burg_x = burg.get('x', 0)
                    burg_y = burg.get('y', 0)

                    # Calculate distance
                    dx = burg_x - loc_x
                    dy = burg_y - loc_y
                    distance = (dx * dx + dy * dy) ** 0.5

                    if distance < min_distance:
                        min_distance = distance
                        closest_burg = burg

                if closest_burg:
                    nearby_settlement = closest_burg
            else:
                nearby_settlement = nearby_burgs[0]

                # Build encounter location
            encounter_location = {
                'id': location.get('i'),
                'point': location.get('p', [0, 0]),
                'biome': location.get('biome', 'grassland'),
                'height': location.get('height', 0),
                'river': location.get('river', 0) > 0,
                'feature_name': location.get('featureName')
            }

            # Add political information
            province_id = location.get('province')
            if province_id:
                province = self._find_by_id(self.map_data.get('provinces', []), province_id)
                if province:
                    encounter_location['province'] = {
                        'id': province.get('i'),
                        'name': province.get('name', f"Unnamed Province {province.get('i')}")
                    }

                    state_id = province.get('state')
                    if state_id:
                        state = self._find_by_id(self.map_data.get('states', []), state_id)
                        if state:
                            encounter_location['state'] = {
                                'id': state.get('i'),
                                'name': state.get('name', f"Unnamed State {state.get('i')}")
                            }

            # Add nearby settlement if available
            if nearby_settlement:
                encounter_location['nearby_settlement'] = {
                    'id': nearby_settlement.get('i'),
                    'name': nearby_settlement.get('name', f"Unnamed Burg {nearby_settlement.get('i')}"),
                    'population': nearby_settlement.get('population', 0),
                    'distance': round(min_distance * self.map_data.get('info', {}).get('mapScale', 1),
                                      2) if 'min_distance' in locals() else 0
                }

            # Generate appropriate encounter based on location
            encounter_details = self._generate_encounter_for_location(encounter_location, params['encounter_type'])

            return {
                'status': 'success',
                'location': encounter_location,
                'encounter': encounter_details
            }

        def _generate_encounter_for_location(self, location: Dict[str, Any], encounter_type: str) -> Dict[str, Any]:
            """
            Generate an appropriate encounter based on the location.
            """
            import random

            # Get biome type
            biome = location.get('biome', 'grassland')
            is_river = location.get('river', False)
            height = location.get('height', 0)

            # Determine appropriate encounter types for the biome
            encounter_types = {
                'forest': ['wildlife', 'bandit', 'hunter', 'mystical', 'traveler', 'settlement'],
                'jungle': ['wildlife', 'predator', 'tribe', 'ruins', 'mystical', 'disease'],
                'desert': ['wildlife', 'bandit', 'caravan', 'ruins', 'natural hazard', 'oasis'],
                'mountain': ['wildlife', 'giant', 'dwarf', 'natural hazard', 'mine', 'vista'],
                'grassland': ['wildlife', 'bandit', 'caravan', 'farm', 'army', 'settlement'],
                'swamp': ['wildlife', 'tribe', 'ruins', 'mystical', 'disease', 'hunter'],
                'tundra': ['wildlife', 'tribe', 'natural hazard', 'mystical', 'explorer', 'settlement'],
                'arctic': ['wildlife', 'natural hazard', 'explorer', 'mystical', 'giant', 'ruins']
            }

            # Ensure biome exists in our types list
            if biome not in encounter_types:
                biome = 'grassland'

            # Choose encounter type if random
            if encounter_type == 'random':
                encounter_type = random.choice(encounter_types[biome])

            # Generate encounter details based on type
            encounter = {
                'type': encounter_type,
                'difficulty': random.choice(['easy', 'medium', 'hard']),
                'rewards': []
            }

            # Add type-specific details
            if encounter_type == 'wildlife':
                # Wildlife encounters vary by biome
                wildlife_types = {
                    'forest': ['wolves', 'bears', 'deer', 'wild boars', 'foxes'],
                    'jungle': ['tigers', 'monkeys', 'snakes', 'parrots', 'insects'],
                    'desert': ['scorpions', 'snakes', 'vultures', 'camels', 'jackals'],
                    'mountain': ['mountain goats', 'eagles', 'wolves', 'bears', 'mountain lions'],
                    'grassland': ['horses', 'bison', 'wolves', 'hawks', 'rabbits'],
                    'swamp': ['alligators', 'snakes', 'frogs', 'insects', 'fish'],
                    'tundra': ['wolves', 'bears', 'elk', 'foxes', 'birds'],
                    'arctic': ['polar bears', 'seals', 'penguins', 'whales', 'walruses']
                }

                encounter['creature'] = random.choice(wildlife_types[biome])
                encounter['behavior'] = random.choice(
                    ['aggressive', 'neutral', 'fleeing', 'hunting', 'defending territory'])
                encounter[
                    'description'] = f"A group of {encounter['creature']} that appear to be {encounter['behavior']}."

                if encounter['difficulty'] == 'hard':
                    encounter['description'] += " They seem unusually large or numerous."

                # Add rewards if aggressive
                if encounter['behavior'] in ['aggressive', 'hunting']:
                    encounter['rewards'].append({
                        'type': 'crafting_materials',
                        'description': f"{encounter['creature'].rstrip('s')} hide and meat"
                    })

            elif encounter_type == 'bandit':
                bandit_types = ['highwaymen', 'deserters', 'outlaws', 'pirates', 'brigands']
                encounter['group'] = random.choice(bandit_types)
                encounter['size'] = random.choice(['small', 'medium', 'large'])
                encounter['activity'] = random.choice(
                    ['ambushing', 'camping', 'patrolling', 'fighting amongst themselves', 'dividing loot'])

                encounter[
                    'description'] = f"A {encounter['size']} group of {encounter['group']} {encounter['activity']}."

                # Add rewards
                encounter['rewards'].append({
                    'type': 'gold',
                    'amount': random.randint(5, 50) * {'small': 1, 'medium': 2, 'large': 4}[encounter['size']]
                })

                if random.random() < 0.3:
                    encounter['rewards'].append({
                        'type': 'item',
                        'description': random.choice(['weapon', 'armor', 'jewelry', 'map', 'potion'])
                    })

            elif encounter_type == 'settlement':
                settlement_types = {
                    'forest': ['logging camp', 'hunter\'s lodge', 'woodcutter\'s village', 'druid circle',
                               'ranger outpost'],
                    'jungle': ['trading post', 'expedition camp', 'native village', 'temple complex',
                               'colonial outpost'],
                    'desert': ['oasis town', 'trading post', 'nomad camp', 'mining outpost', 'ancient temple'],
                    'mountain': ['mining town', 'fortress', 'monastery', 'dwarf hold', 'giant steading'],
                    'grassland': ['farming village', 'roadside inn', 'market town', 'military outpost', 'nomad camp'],
                    'swamp': ['fishing village', 'witch\'s hut', 'smuggler\'s hideout', 'lizardfolk village',
                              'hermit\'s shack'],
                    'tundra': ['fur trapper camp', 'small fort', 'tribal settlement', 'mining outpost', 'trading post'],
                    'arctic': ['fishing village', 'explorer camp', 'native settlement', 'outpost',
                               'magical research station']
                }

                encounter['settlement_type'] = random.choice(settlement_types[biome])
                encounter['attitude'] = random.choice(['friendly', 'suspicious', 'neutral', 'hostile', 'desperate'])
                encounter['notable_npc'] = random.choice(['elder', 'merchant', 'craftsman', 'guard captain', 'outcast'])
                encounter['problem'] = random.choice(
                    ['monster attacks', 'supply shortage', 'disease', 'internal conflict', 'natural disaster', 'none'])

                encounter[
                    'description'] = f"A {encounter['settlement_type']} where the inhabitants are {encounter['attitude']}."
                if encounter['problem'] != 'none':
                    encounter['description'] += f" They are dealing with {encounter['problem']}."

                # Add potential quest hook
                if encounter['problem'] != 'none':
                    encounter['quest_hook'] = f"Help the settlement deal with {encounter['problem']}."

            elif encounter_type == 'ruins':
                ruin_types = ['temple', 'fortress', 'palace', 'village', 'outpost', 'tomb', 'monument']
                encounter['ruin_type'] = random.choice(ruin_types)
                encounter['age'] = random.choice(['ancient', 'recent', 'primordial', 'forgotten'])
                encounter['condition'] = random.choice(['mostly intact', 'crumbling', 'overgrown', 'buried', 'flooded'])
                encounter['current_occupants'] = random.choice(['monsters', 'bandits', 'wildlife', 'spirits', 'none'])

                encounter[
                    'description'] = f"The {encounter['condition']} ruins of an {encounter['age']} {encounter['ruin_type']}."
                if encounter['current_occupants'] != 'none':
                    encounter['description'] += f" It appears to be occupied by {encounter['current_occupants']}."

                # Add rewards
                if random.random() < 0.7:
                    encounter['rewards'].append({
                        'type': 'treasure',
                        'description': random.choice(
                            ['hidden cache', 'ancient artifact', 'historical relic', 'forgotten knowledge',
                             'valuable treasure'])
                    })

            elif encounter_type == 'mystical':
                mystical_types = ['strange lights', 'unusual weather', 'magical phenomenon', 'planar rift',
                                  'fey crossing', 'haunting', 'vision']
                encounter['phenomenon'] = random.choice(mystical_types)
                encounter['effect'] = random.choice(['beneficial', 'harmful', 'neutral', 'transformative', 'revealing'])

                encounter[
                    'description'] = f"A mystical occurrence featuring {encounter['phenomenon']} with potentially {encounter['effect']} effects."

                # Add possible rewards or consequences
                if encounter['effect'] == 'beneficial':
                    encounter['rewards'].append({
                        'type': 'boon',
                        'description': random.choice(
                            ['temporary magical enhancement', 'healing', 'prophetic vision', 'supernatural ally',
                             'magical insight'])
                    })
                elif encounter['effect'] == 'harmful':
                    encounter['consequence'] = random.choice(
                        ['curse', 'magical affliction', 'hostile entity summoned', 'magical trap', 'corruption'])

            # Add common elements
            encounter['weather'] = random.choice(['clear', 'rainy', 'windy', 'foggy', 'stormy'])
            encounter['time_of_day'] = random.choice(['dawn', 'day', 'dusk', 'night'])

            # Add river element if applicable
            if is_river:
                encounter['river_element'] = random.choice(
                    ['crossing point', 'rapids', 'waterfall', 'fishing spot', 'ambush point'])
                encounter['description'] += f" Near a river with a {encounter['river_element']}."

            # Add elevation element if applicable
            if height > 70:  # Mountain
                encounter['elevation_feature'] = random.choice(['peak', 'cliff', 'cave', 'pass', 'plateau'])
                encounter['description'] += f" In a mountainous area with a {encounter['elevation_feature']}."
            elif height > 40:  # Highland
                encounter['elevation_feature'] = random.choice(['hill', 'ridge', 'overlook', 'valley', 'crag'])
                encounter['description'] += f" In highlands with a {encounter['elevation_feature']}."

            return encounter

        def find_nearest_settlement(self, location_id: int, settlement_type: str = None) -> Dict[str, Any]:
            """
            Find the nearest settlement to a given location.

            Args:
                location_id: ID of the location
                settlement_type: Optional type of settlement to find

            Returns:
                Dictionary with nearest settlement information
            """
            # Find the location
            location = self._find_location_by_id(location_id)
            if not location:
                return {
                    'status': 'error',
                    'message': f"Could not find location with ID: {location_id}"
                }

            # Get location coordinates
            loc_x = location.get('x', location.get('p', [0, 0])[0])
            loc_y = location.get('y', location.get('p', [0, 0])[1])

            # Filter burgs by type if specified
            filtered_burgs = self.map_data.get('burgs', [])
            if settlement_type:
                if settlement_type == 'capital':
                    filtered_burgs = [b for b in filtered_burgs if b.get('capital', 0) == 1]
                elif settlement_type == 'port':
                    filtered_burgs = [b for b in filtered_burgs if b.get('port', 0) > 0]
                elif settlement_type == 'citadel':
                    filtered_burgs = [b for b in filtered_burgs if b.get('citadel', 0) == 1]

            # Remove "removed" burgs
            filtered_burgs = [b for b in filtered_burgs if not b.get('removed', False)]

            if not filtered_burgs:
                return {
                    'status': 'error',
                    'message': f"No settlements of type '{settlement_type}' found"
                }

            # Find nearest burg
            nearest_burg = None
            min_distance = float('inf')

            for burg in filtered_burgs:
                burg_x = burg.get('x', 0)
                burg_y = burg.get('y', 0)

                # Calculate distance
                dx = burg_x - loc_x
                dy = burg_y - loc_y
                distance = (dx * dx + dy * dy) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    nearest_burg = burg

            if not nearest_burg:
                return {
                    'status': 'error',
                    'message': "Could not find nearest settlement"
                }

            # Get political info for the settlement
            political_info = self.get_political_info(nearest_burg.get('i'))

            # Calculate distance in miles
            map_scale = self.map_data.get('info', {}).get('mapScale', 1)
            distance_miles = min_distance * map_scale

            # Create travel time estimate
            travel_time = self._estimate_travel_time(distance_miles, 'walking')

            return {
                'status': 'success',
                'settlement': {
                    'id': nearest_burg.get('i'),
                    'name': nearest_burg.get('name', f"Unnamed Burg {nearest_burg.get('i')}"),
                    'population': nearest_burg.get('population', 0),
                    'capital': bool(nearest_burg.get('capital', 0)),
                    'port': bool(nearest_burg.get('port', 0)),
                    'citadel': bool(nearest_burg.get('citadel', 0))
                },
                'distance': round(distance_miles, 2),
                'unit': 'miles',
                'travel_time': travel_time,
                'political_info': political_info.get('political_info') if political_info.get(
                    'status') == 'success' else None
            }

        def get_random_burg(self, state_id: int = None, min_population: int = 0,
                            is_capital: bool = False, is_port: bool = False) -> Dict[str, Any]:
            """
            Get a random settlement based on criteria.

            Args:
                state_id: Optional ID of the state to search in
                min_population: Minimum population required
                is_capital: Whether the settlement must be a capital
                is_port: Whether the settlement must be a port

            Returns:
                Dictionary with settlement information
            """
            # Filter burgs based on criteria
            filtered_burgs = [b for b in self.map_data.get('burgs', [])
                              if not b.get('removed', False) and
                              b.get('population', 0) >= min_population and
                              (state_id is None or b.get('state') == state_id) and
                              (not is_capital or b.get('capital', 0) == 1) and
                              (not is_port or b.get('port', 0) > 0)]

            if not filtered_burgs:
                return {
                    'status': 'error',
                    'message': "No settlements found matching the criteria"
                }

            # Select random burg
            import random
            burg = random.choice(filtered_burgs)

            # Get political info for the settlement
            political_info = self.get_political_info(burg.get('i'))

            return {
                'status': 'success',
                'settlement': {
                    'id': burg.get('i'),
                    'name': burg.get('name', f"Unnamed Burg {burg.get('i')}"),
                    'population': burg.get('population', 0),
                    'capital': bool(burg.get('capital', 0)),
                    'port': bool(burg.get('port', 0)),
                    'citadel': bool(burg.get('citadel', 0))
                },
                'political_info': political_info.get('political_info') if political_info.get(
                    'status') == 'success' else None
            }

        def get_random_route(self, start_state_id: int = None, end_state_id: int = None,
                             min_distance: float = 0, max_distance: float = float('inf'),
                             travel_method: str = 'walking') -> Dict[str, Any]:
            """
            Generate a random travel route between settlements.

            Args:
                start_state_id: Optional ID of the starting state
                end_state_id: Optional ID of the ending state
                min_distance: Minimum distance in miles
                max_distance: Maximum distance in miles
                travel_method: Method of travel

            Returns:
                Dictionary with route information
            """
            # Get starting settlement
            start_burg = None
            if start_state_id is not None:
                state_burgs = [b for b in self.map_data.get('burgs', [])
                               if not b.get('removed', False) and b.get('state') == start_state_id]
                if state_burgs:
                    import random
                    start_burg = random.choice(state_burgs)

            if not start_burg:
                # Select random non-removed burg
                valid_burgs = [b for b in self.map_data.get('burgs', []) if not b.get('removed', False)]
                if valid_burgs:
                    import random
                    start_burg = random.choice(valid_burgs)
                else:
                    return {
                        'status': 'error',
                        'message': "No valid settlements found for route start"
                    }

            # Find possible end settlements
            possible_end_burgs = []
            start_x = start_burg.get('x', 0)
            start_y = start_burg.get('y', 0)
            map_scale = self.map_data.get('info', {}).get('mapScale', 1)

            for burg in self.map_data.get('burgs', []):
                if burg.get('i') == start_burg.get('i') or burg.get('removed', False):
                    continue

                # Skip if end state doesn't match
                if end_state_id is not None and burg.get('state') != end_state_id:
                    continue

                burg_x = burg.get('x', 0)
                burg_y = burg.get('y', 0)

                # Calculate distance
                dx = burg_x - start_x
                dy = burg_y - start_y
                distance = (dx * dx + dy * dy) ** 0.5 * map_scale

                if min_distance <= distance <= max_distance:
                    possible_end_burgs.append((burg, distance))

            if not possible_end_burgs:
                return {
                    'status': 'error',
                    'message': "No valid end points found matching distance criteria"
                }

            # Select random end point
            import random
            end_burg, distance = random.choice(possible_end_burgs)

            # Create path
            path = self._find_path(start_burg, end_burg, travel_method)

            # Calculate travel time
            travel_time = self._estimate_travel_time(distance, travel_method)

            return {
                'status': 'success',
                'route': {
                    'start': {
                        'id': start_burg.get('i'),
                        'name': start_burg.get('name', f"Unnamed Burg {start_burg.get('i')}"),
                        'population': start_burg.get('population', 0)
                    },
                    'end': {
                        'id': end_burg.get('i'),
                        'name': end_burg.get('name', f"Unnamed Burg {end_burg.get('i')}"),
                        'population': end_burg.get('population', 0)
                    },
                    'distance': round(distance, 2),
                    'unit': 'miles',
                    'travel_time': travel_time,
                    'travel_method': travel_method,
                    'path': path
                }
            }

        def get_map_stats(self) -> Dict[str, Any]:
            """
            Get statistical information about the map.

            Returns:
                Dictionary with map statistics
            """
            # Basic map information
            info = self.map_data.get('info', {})
            map_name = info.get('name', 'Fantasy World')
            seed = info.get('seed', 'unknown')

            # Count entities
            total_cells = len(self.map_data.get('cells', []))
            total_burgs = len([b for b in self.map_data.get('burgs', []) if not b.get('removed', False)])
            total_states = len([s for s in self.map_data.get('states', []) if s.get('i', 0) > 0])  # Skip neutrals
            total_provinces = len(self.map_data.get('provinces', []))
            total_religions = len([r for r in self.map_data.get('religions', []) if r.get('i', 0) > 0])
            total_cultures = len([c for c in self.map_data.get('cultures', []) if c.get('i', 0) > 0])

            # Biome distribution
            biomes = {}
            for cell in self.map_data.get('cells', []):
                biome = cell.get('biome', 'unknown')
                if biome not in biomes:
                    biomes[biome] = 0
                biomes[biome] += 1

            # State size analysis
            states = [s for s in self.map_data.get('states', []) if s.get('i', 0) > 0]
            state_sizes = {}
            for state in states:
                state_sizes[state.get('name', f"State {state.get('i')}")] = state.get('area', 0)

            # Population analysis
            total_population = sum(
                b.get('population', 0) for b in self.map_data.get('burgs', []) if not b.get('removed', False))
            capitals_population = sum(b.get('population', 0) for b in self.map_data.get('burgs', [])
                                      if not b.get('removed', False) and b.get('capital', 0) == 1)
            ports_population = sum(b.get('population', 0) for b in self.map_data.get('burgs', [])
                                   if not b.get('removed', False) and b.get('port', 0) > 0)

            # Population by state
            population_by_state = {}
            for state in states:
                state_burgs = [b for b in self.map_data.get('burgs', [])
                               if not b.get('removed', False) and b.get('state') == state.get('i')]
                state_population = sum(b.get('population', 0) for b in state_burgs)
                population_by_state[state.get('name', f"State {state.get('i')}")] = state_population

            return {
                'status': 'success',
                'map_info': {
                    'name': map_name,
                    'seed': seed
                },
                'entity_counts': {
                    'cells': total_cells,
                    'burgs': total_burgs,
                    'states': total_states,
                    'provinces': total_provinces,
                    'religions': total_religions,
                    'cultures': total_cultures
                },
                'biome_distribution': biomes,
                'state_sizes': state_sizes,
                'population': {
                    'total': total_population,
                    'capitals': capitals_population,
                    'ports': ports_population,
                    'by_state': population_by_state
                }
            }

            # Debugging function (optional)

        def test_map_query_engine():
            """
            Test function for the MapQueryEngine.
            """
            # Initialize engine with default paths
            engine = MapQueryEngine()

            # Test loading map data
            print("Loading map data...")
            engine._load_map_data()

            # Print basic map info
            print(f"Map info: {engine.map_data.get('info', {})}")
            print(f"Number of cells: {len(engine.map_data.get('cells', []))}")
            print(f"Number of burgs: {len(engine.map_data.get('burgs', []))}")
            print(f"Number of states: {len(engine.map_data.get('states', []))}")

            # Test a simple query
            print("\nTesting query...")
            query_result = engine.process_query({
                'type': 'list',
                'entity_type': 'burgs',
                'limit': 5
            })
            print(f"Query result: {query_result}")

            # Test world overview
            print("\nGetting world overview...")
            overview = engine.get_world_overview()
            print(f"World overview: {overview}")

        if __name__ == "__main__":
            test_map_query_engine()