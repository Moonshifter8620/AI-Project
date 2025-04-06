"""
MapLocationManager.py
Part of the D&D5e MapAI system
Manages cities, points of interest, and landmarks within the game world.

Based on the structure from Azgaar's Fantasy Map Generator
"""

import json
import os
import random
import math
from enum import Enum
from typing import Dict, List, Tuple, Set, Optional, Union, Any

# Import from other MapAI components
from MapWorldState import MapWorldState
from MapRegionManager import MapRegionManager
from MapPoliticalManager import MapPoliticalManager


class LocationType(Enum):
    """Types of locations based on Azgaar's Fantasy Map Generator"""
    CAPITAL = "Capital"
    CITY = "City"
    TOWN = "Town"
    VILLAGE = "Village"
    HAMLET = "Hamlet"
    FORTRESS = "Fortress"
    TEMPLE = "Temple"
    RUINS = "Ruins"
    DUNGEON = "Dungeon"
    LANDMARK = "Landmark"
    CAVE = "Cave"
    CAMP = "Camp"
    TAVERN = "Tavern"
    INTERSECTION = "Intersection"


class SettlementSizeCategory(Enum):
    """Size categories for settlements"""
    HAMLET = "Hamlet"          # < 100
    VILLAGE = "Village"        # 100-1000
    TOWN = "Town"              # 1000-5000
    CITY = "City"              # 5000-10000
    LARGE_CITY = "Large City"  # 10000-25000
    CAPITAL = "Capital"        # > 25000


class PointOfInterestCategory(Enum):
    """Categories for points of interest"""
    TAVERN = "Tavern"
    INN = "Inn"
    SHOP = "Shop"
    TEMPLE = "Temple"
    GUILDHALL = "Guildhall"
    MARKET = "Market"
    BLACKSMITH = "Blacksmith"
    STABLE = "Stable"
    MANSION = "Mansion"
    PALACE = "Palace"
    PARK = "Park"
    MONUMENT = "Monument"
    LIBRARY = "Library"
    WIZARD_TOWER = "Wizard Tower"
    ARENA = "Arena"
    TRAINING_GROUND = "Training Ground"
    MINE = "Mine"
    FARM = "Farm"
    MILITARY_POST = "Military Post"
    CRAFTING_HALL = "Crafting Hall"


class Location:
    """Base class for all locations in the game world"""

    def __init__(self,
                 location_id: str,
                 name: str,
                 position: Tuple[float, float],
                 location_type: LocationType = LocationType.LANDMARK):
        """
        Initialize a location

        Args:
            location_id: Unique identifier
            name: Name of the location
            position: (x, y) coordinates
            location_type: Type of location
        """
        self.id = location_id
        self.name = name
        self.x, self.y = position
        self.type = location_type
        self.description = ""
        self.discovered = False
        self.notes = []

        # Physical characteristics
        self.elevation = 0.0
        self.temperature = 0.0
        self.humidity = 0.0
        self.biome_id = ""

        # References to other entities
        self.region_id = ""
        self.state_id = ""
        self.culture_id = ""

        # Game-specific data
        self.danger_level = 0.5  # 0.0-1.0 scale
        self.available_quests = []
        self.available_resources = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert location to a dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "type": self.type.value,
            "description": self.description,
            "discovered": self.discovered,
            "notes": self.notes,
            "elevation": self.elevation,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "biome_id": self.biome_id,
            "region_id": self.region_id,
            "state_id": self.state_id,
            "culture_id": self.culture_id,
            "danger_level": self.danger_level,
            "available_quests": self.available_quests,
            "available_resources": self.available_resources
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        """Create a Location from a dictionary"""
        location = cls(
            location_id=data["id"],
            name=data["name"],
            position=(data["x"], data["y"]),
            location_type=LocationType(data["type"]),
        )

        location.description = data.get("description", "")
        location.discovered = data.get("discovered", False)
        location.notes = data.get("notes", [])
        location.elevation = data.get("elevation", 0.0)
        location.temperature = data.get("temperature", 0.0)
        location.humidity = data.get("humidity", 0.0)
        location.biome_id = data.get("biome_id", "")
        location.region_id = data.get("region_id", "")
        location.state_id = data.get("state_id", "")
        location.culture_id = data.get("culture_id", "")
        location.danger_level = data.get("danger_level", 0.5)
        location.available_quests = data.get("available_quests", [])
        location.available_resources = data.get("available_resources", [])

        return location


class Settlement(Location):
    """Represents a settlement (city, town, village, etc.)"""

    def __init__(self,
                 location_id: str,
                 name: str,
                 position: Tuple[float, float],
                 location_type: LocationType = LocationType.TOWN,
                 population: int = 0):
        """
        Initialize a settlement

        Args:
            location_id: Unique identifier
            name: Name of the settlement
            position: (x, y) coordinates
            location_type: Type of settlement
            population: Population count
        """
        super().__init__(location_id, name, position, location_type)

        self.population = population
        self.is_capital = False
        self.is_port = False

        # Settlement features
        self.has_walls = False
        self.has_castle = False
        self.has_temple = False
        self.has_market = False
        self.has_shanty_town = False

        # Economic and social factors
        self.wealth = 0.5  # 0.0-1.0 scale
        self.stability = 0.5  # 0.0-1.0 scale
        self.authority_type = ""  # e.g., "mayor", "lord", "council", etc.
        self.authority_name = ""

        # Points of interest in this settlement
        self.points_of_interest: List[PointOfInterest] = []

        # Trading and resources
        self.trading_goods = []
        self.local_resources = []

        # Settlement appearance
        self.architecture_style = ""
        self.notable_features = []

    def get_size_category(self) -> SettlementSizeCategory:
        """Determine the settlement size category based on population"""
        if self.is_capital:
            return SettlementSizeCategory.CAPITAL
        elif self.population >= 10000:
            return SettlementSizeCategory.LARGE_CITY
        elif self.population >= 5000:
            return SettlementSizeCategory.CITY
        elif self.population >= 1000:
            return SettlementSizeCategory.TOWN
        elif self.population >= 100:
            return SettlementSizeCategory.VILLAGE
        else:
            return SettlementSizeCategory.HAMLET

    def to_dict(self) -> Dict[str, Any]:
        """Convert settlement to a dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "population": self.population,
            "is_capital": self.is_capital,
            "is_port": self.is_port,
            "has_walls": self.has_walls,
            "has_castle": self.has_castle,
            "has_temple": self.has_temple,
            "has_market": self.has_market,
            "has_shanty_town": self.has_shanty_town,
            "wealth": self.wealth,
            "stability": self.stability,
            "authority_type": self.authority_type,
            "authority_name": self.authority_name,
            "points_of_interest": [poi.to_dict() for poi in self.points_of_interest],
            "trading_goods": self.trading_goods,
            "local_resources": self.local_resources,
            "architecture_style": self.architecture_style,
            "notable_features": self.notable_features,
            "size_category": self.get_size_category().value
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settlement':
        """Create a Settlement from a dictionary"""
        settlement = cls(
            location_id=data["id"],
            name=data["name"],
            position=(data["x"], data["y"]),
            location_type=LocationType(data["type"]),
            population=data.get("population", 0)
        )

        # Load location base attributes
        settlement.description = data.get("description", "")
        settlement.discovered = data.get("discovered", False)
        settlement.notes = data.get("notes", [])
        settlement.elevation = data.get("elevation", 0.0)
        settlement.temperature = data.get("temperature", 0.0)
        settlement.humidity = data.get("humidity", 0.0)
        settlement.biome_id = data.get("biome_id", "")
        settlement.region_id = data.get("region_id", "")
        settlement.state_id = data.get("state_id", "")
        settlement.culture_id = data.get("culture_id", "")
        settlement.danger_level = data.get("danger_level", 0.5)
        settlement.available_quests = data.get("available_quests", [])
        settlement.available_resources = data.get("available_resources", [])

        # Load settlement-specific attributes
        settlement.is_capital = data.get("is_capital", False)
        settlement.is_port = data.get("is_port", False)
        settlement.has_walls = data.get("has_walls", False)
        settlement.has_castle = data.get("has_castle", False)
        settlement.has_temple = data.get("has_temple", False)
        settlement.has_market = data.get("has_market", False)
        settlement.has_shanty_town = data.get("has_shanty_town", False)
        settlement.wealth = data.get("wealth", 0.5)
        settlement.stability = data.get("stability", 0.5)
        settlement.authority_type = data.get("authority_type", "")
        settlement.authority_name = data.get("authority_name", "")
        settlement.trading_goods = data.get("trading_goods", [])
        settlement.local_resources = data.get("local_resources", [])
        settlement.architecture_style = data.get("architecture_style", "")
        settlement.notable_features = data.get("notable_features", [])

        # Load points of interest
        poi_data = data.get("points_of_interest", [])
        settlement.points_of_interest = [PointOfInterest.from_dict(poi) for poi in poi_data]

        return settlement


class PointOfInterest(Location):
    """Represents a specific point of interest within a location or the world"""

    def __init__(self,
                 location_id: str,
                 name: str,
                 position: Tuple[float, float],
                 location_type: LocationType = LocationType.LANDMARK,
                 category: PointOfInterestCategory = PointOfInterestCategory.SHOP,
                 parent_location_id: Optional[str] = None):
        """
        Initialize a point of interest

        Args:
            location_id: Unique identifier
            name: Name of the point of interest
            position: (x, y) coordinates
            location_type: Type of location
            category: Specific category of point of interest
            parent_location_id: ID of the parent location (e.g., city), if any
        """
        super().__init__(location_id, name, position, location_type)

        self.category = category
        self.parent_location_id = parent_location_id
        self.owner_name = ""
        self.npcs = []
        self.quest_hooks = []
        self.items_available = []
        self.room_count = 0
        self.quality = 0.5  # 0.0-1.0 scale

    def to_dict(self) -> Dict[str, Any]:
        """Convert point of interest to a dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "category": self.category.value,
            "parent_location_id": self.parent_location_id,
            "owner_name": self.owner_name,
            "npcs": self.npcs,
            "quest_hooks": self.quest_hooks,
            "items_available": self.items_available,
            "room_count": self.room_count,
            "quality": self.quality
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointOfInterest':
        """Create a PointOfInterest from a dictionary"""
        poi = cls(
            location_id=data["id"],
            name=data["name"],
            position=(data["x"], data["y"]),
            location_type=LocationType(data["type"]),
            category=PointOfInterestCategory(data["category"]),
            parent_location_id=data.get("parent_location_id")
        )

        # Load location base attributes
        poi.description = data.get("description", "")
        poi.discovered = data.get("discovered", False)
        poi.notes = data.get("notes", [])
        poi.elevation = data.get("elevation", 0.0)
        poi.temperature = data.get("temperature", 0.0)
        poi.humidity = data.get("humidity", 0.0)
        poi.biome_id = data.get("biome_id", "")
        poi.region_id = data.get("region_id", "")
        poi.state_id = data.get("state_id", "")
        poi.culture_id = data.get("culture_id", "")
        poi.danger_level = data.get("danger_level", 0.5)
        poi.available_quests = data.get("available_quests", [])
        poi.available_resources = data.get("available_resources", [])

        # Load point of interest-specific attributes
        poi.owner_name = data.get("owner_name", "")
        poi.npcs = data.get("npcs", [])
        poi.quest_hooks = data.get("quest_hooks", [])
        poi.items_available = data.get("items_available", [])
        poi.room_count = data.get("room_count", 0)
        poi.quality = data.get("quality", 0.5)

        return poi


class Dungeon(Location):
    """Represents a dungeon or other adventure location"""

    def __init__(self,
                 location_id: str,
                 name: str,
                 position: Tuple[float, float],
                 location_type: LocationType = LocationType.DUNGEON,
                 difficulty: int = 1,
                 size: str = "Medium"):
        """
        Initialize a dungeon

        Args:
            location_id: Unique identifier
            name: Name of the dungeon
            position: (x, y) coordinates
            location_type: Type of dungeon
            difficulty: Challenge rating (1-20)
            size: Size of the dungeon
        """
        super().__init__(location_id, name, position, location_type)

        self.difficulty = difficulty
        self.size = size
        self.levels = 1
        self.origin = ""  # e.g., "natural", "constructed", "magical", etc.
        self.current_inhabitants = []
        self.previous_inhabitants = []
        self.traps = []
        self.treasure = []
        self.notable_features = []
        self.completed = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert dungeon to a dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "difficulty": self.difficulty,
            "size": self.size,
            "levels": self.levels,
            "origin": self.origin,
            "current_inhabitants": self.current_inhabitants,
            "previous_inhabitants": self.previous_inhabitants,
            "traps": self.traps,
            "treasure": self.treasure,
            "notable_features": self.notable_features,
            "completed": self.completed
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dungeon':
        """Create a Dungeon from a dictionary"""
        dungeon = cls(
            location_id=data["id"],
            name=data["name"],
            position=(data["x"], data["y"]),
            location_type=LocationType(data["type"]),
            difficulty=data.get("difficulty", 1),
            size=data.get("size", "Medium")
        )

        # Load location base attributes
        dungeon.description = data.get("description", "")
        dungeon.discovered = data.get("discovered", False)
        dungeon.notes = data.get("notes", [])
        dungeon.elevation = data.get("elevation", 0.0)
        dungeon.temperature = data.get("temperature", 0.0)
        dungeon.humidity = data.get("humidity", 0.0)
        dungeon.biome_id = data.get("biome_id", "")
        dungeon.region_id = data.get("region_id", "")
        dungeon.state_id = data.get("state_id", "")
        dungeon.culture_id = data.get("culture_id", "")
        dungeon.danger_level = data.get("danger_level", 0.5)
        dungeon.available_quests = data.get("available_quests", [])
        dungeon.available_resources = data.get("available_resources", [])

        # Load dungeon-specific attributes
        dungeon.levels = data.get("levels", 1)
        dungeon.origin = data.get("origin", "")
        dungeon.current_inhabitants = data.get("current_inhabitants", [])
        dungeon.previous_inhabitants = data.get("previous_inhabitants", [])
        dungeon.traps = data.get("traps", [])
        dungeon.treasure = data.get("treasure", [])
        dungeon.notable_features = data.get("notable_features", [])
        dungeon.completed = data.get("completed", False)

        return dungeon


class MapLocationManager:
    """
    Manages locations, settlements, points of interest, and landmarks.
    Provides interfaces for querying location data and generating new locations.
    """

    # Singleton instance
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MapLocationManager()
        return cls._instance

    def __init__(self):
        # References to other managers
        self.world_state = None
        self.region_manager = None
        self.political_manager = None

        # Location storage
        self.locations: Dict[str, Location] = {}
        self.settlements: Dict[str, Settlement] = {}
        self.points_of_interest: Dict[str, PointOfInterest] = {}
        self.dungeons: Dict[str, Dungeon] = {}

        # ID tracking
        self.next_location_id = 1
        self.next_settlement_id = 1
        self.next_poi_id = 1
        self.next_dungeon_id = 1

        # Cache for spatial queries
        self.location_grid = {}
        self.grid_cell_size = 10.0  # Grid cell size for spatial indexing

        # Name generation
        self.settlement_name_prefixes = [
            "North", "South", "East", "West", "New", "Old", "Upper", "Lower",
            "Great", "Little", "High", "Low", "Fort", "Port", "Mount", "Lake"
        ]

        self.settlement_name_suffixes = [
            "town", "ville", "burg", "borough", "port", "ford", "bridge", "mill",
            "field", "wood", "forest", "river", "lake", "shore", "bay", "cliff",
            "dale", "valley", "glen", "haven", "harbor", "falls", "crossing"
        ]

        print("MapLocationManager initialized")

    def initialize(self):
        """Initialize the location manager with data from world state"""
        try:
            # Get references to other managers
            self.world_state = MapWorldState.instance()
            self.region_manager = MapRegionManager.instance()
            self.political_manager = MapPoliticalManager.instance()

            # Load locations from world state if available
            self.load_locations_from_world_state()

            # Generate spatial indexing grid for locations
            self.regenerate_spatial_index()

            print("MapLocationManager initialization complete")
        except Exception as ex:
            print(f"Error initializing MapLocationManager: {str(ex)}")

    def load_locations_from_world_state(self):
        """Load locations from world state data"""
        # Clear existing locations
        self.locations.clear()
        self.settlements.clear()
        self.points_of_interest.clear()
        self.dungeons.clear()

        try:
            # Get locations from world state
            if hasattr(self.world_state, 'locations'):
                for location_id, location_data in self.world_state.locations.items():
                    # Determine location type and create appropriate object
                    location_type = location_data.get('type', 'settlement')

                    if location_type == 'settlement':
                        settlement = Settlement(
                            location_id=location_id,
                            name=location_data.get('name', f'Settlement {location_id}'),
                            position=(location_data.get('x', 0), location_data.get('y', 0)),
                            location_type=LocationType.TOWN,
                            population=location_data.get('population', 1000)
                        )

                        # Update settlement-specific properties
                        settlement.is_capital = location_data.state_id == location_data.capital_id

                        self.settlements[location_id] = settlement
                        self.locations[location_id] = settlement
                    else:
                        # Generic location
                        location = Location(
                            location_id=location_id,
                            name=location_data.get('name', f'Location {location_id}'),
                            position=(location_data.get('x', 0), location_data.get('y', 0)),
                            location_type=LocationType.LANDMARK
                        )

                        self.locations[location_id] = location

                # Update ID tracking
                if self.locations:
                    max_id = max([int(loc_id) for loc_id in self.locations.keys() if loc_id.isdigit()], default=0)
                    self.next_location_id = max_id + 1

                if self.settlements:
                    max_id = max([int(loc_id) for loc_id in self.settlements.keys() if loc_id.isdigit()], default=0)
                    self.next_settlement_id = max_id + 1

                print(f"Loaded {len(self.locations)} locations from world state")
            else:
                print("No locations found in world state, will initialize with default generation")
                # Generate some basic settlements if none exist
                self.generate_settlements_from_political_entities()
        except Exception as ex:
            print(f"Error loading locations from world state: {str(ex)}")

    def generate_settlements_from_political_entities(self):
        """Generate basic settlements for each political entity"""
        try:
            if not self.political_manager:
                print("Political manager not available, skipping settlement generation")
                return

            for entity_id, entity in self.political_manager.entities.items():
                # Skip if no cell data available
                if not entity.center_cell_id:
                    continue

                # Get position from cell ID
                x, y = self.convert_cell_id_to_position(entity.center_cell_id)

                # Create capital settlement
                capital_id = f"settlement_{self.next_settlement_id}"
                self.next_settlement_id += 1

                capital_name = self.generate_settlement_name(entity.name, True)

                capital = Settlement(
                    location_id=capital_id,
                    name=capital_name,
                    position=(x, y),
                    location_type=LocationType.CAPITAL,
                    population=random.randint(10000, 50000)
                )

                capital.is_capital = True
                capital.state_id = entity_id
                capital.has_castle = True
                capital.has_walls = True

                self.settlements[capital_id] = capital
                self.locations[capital_id] = capital

                # Generate additional settlements for this entity
                self.generate_settlements_for_entity(entity)

            print(f"Generated {len(self.settlements)} settlements from political entities")
        except Exception as ex:
            print(f"Error generating settlements from political entities: {str(ex)}")

    def convert_cell_id_to_position(self, cell_id: int) -> Tuple[float, float]:
        """Convert a cell ID to (x, y) position"""
        if self.region_manager:
            # Use region manager's conversion if available
            return self.region_manager.GetCellPosition(cell_id)
        else:
            # Fallback calculation
            grid_size = 1000  # Default grid size
            x = cell_id % grid_size
            y = cell_id // grid_size
            return (float(x), float(y))

    def generate_settlements_for_entity(self, entity):
        """Generate additional settlements for a political entity"""
        # Determine how many settlements to create based on territory size
        territory_size = len(entity.territory_cells)

        num_towns = max(1, territory_size // 500)
        num_villages = max(2, territory_size // 200)

        # Generate towns
        for _ in range(num_towns):
            if not entity.territory_cells:
                continue

            # Select a cell for the town
            cell_id = self.select_settlement_location(entity.territory_cells, entity.center_cell_id)

            # Get position from cell ID
            x, y = self.convert_cell_id_to_position(cell_id)

            # Create town
            town_id = f"settlement_{self.next_settlement_id}"
            self.next_settlement_id += 1

            town_name = self.generate_settlement_name(entity.name, False)

            town = Settlement(
                location_id=town_id,
                name=town_name,
                position=(x, y),
                location_type=LocationType.TOWN,
                population=random.randint(2000, 8000)
            )

            town.state_id = entity.id
            town.has_walls = random.random() < 0.7

            self.settlements[town_id] = town
            self.locations[town_id] = town

        # Generate villages
        for _ in range(num_villages):
            if not entity.territory_cells:
                continue

            # Select a cell for the village
            cell_id = self.select_settlement_location(entity.territory_cells, entity.center_cell_id)

            # Get position from cell ID
            x, y = self.convert_cell_id_to_position(cell_id)

            # Create village
            village_id = f"settlement_{self.next_settlement_id}"
            self.next_settlement_id += 1

            village_name = self.generate_settlement_name(entity.name, False)

            village = Settlement(
                location_id=village_id,
                name=village_name,
                position=(x, y),
                location_type=LocationType.VILLAGE,
                population=random.randint(200, 1000)
            )

            village.state_id = entity.id

            self.settlements[village_id] = village
            self.locations[village_id] = village

    def select_settlement_location(self, territory_cells: Set[int], capital_cell_id: int) -> int:
        """
        Select a good cell for settlement placement

        Args:
            territory_cells: Set of cell IDs belonging to a territory
            capital_cell_id: Cell ID of the capital to avoid placing too close

        Returns:
            Selected cell ID
        """
        # Convert to list for selection
        cells = list(territory_cells)

        # If there's only one cell, use it
        if len(cells) <= 1:
            return cells[0]

        # Try to find cells that are suitable for settlements
        suitable_cells = []

        for cell_id in cells:
            # Skip cells too close to capital
            if abs(cell_id - capital_cell_id) < 100:  # Arbitrary distance
                continue

            # Check if cell is suitable for a settlement
            if self.is_cell_suitable_for_settlement(cell_id):
                suitable_cells.append(cell_id)

        # If we found suitable cells, randomly select one
        if suitable_cells:
            return random.choice(suitable_cells)

        # Otherwise, select a random cell
        return random.choice(cells)

    def is_cell_suitable_for_settlement(self, cell_id: int) -> bool:
        """
        Check if a cell is suitable for a settlement

        Args:
            cell_id: Cell ID to check

        Returns:
            True if suitable, False otherwise
        """
        # Check if region manager is available
        if not self.region_manager:
            return True

        # Check terrain type
        terrain_type = self.region_manager.GetTerrainTypeForCell(cell_id)

        # Unsuitable terrain types
        unsuitable_terrains = ["ocean", "sea", "mountain", "high_mountain", "glacier"]

        if terrain_type in unsuitable_terrains:
            return False

        # Check if there's water nearby (good for settlements)
        neighboring_cells = self.region_manager.GetNeighboringCells(cell_id)

        for neighbor_cell in neighboring_cells:
            neighbor_terrain = self.region_manager.GetTerrainTypeForCell(neighbor_cell)
            if neighbor_terrain in ["river", "lake"]:
                return True

        # Default to suitable if nothing else applies
        return True

    def generate_settlement_name(self, region_name: str, is_capital: bool) -> str:
        """
        Generate a name for a settlement

        Args:
            region_name: Name of the region/state the settlement is in
            is_capital: Whether this is a capital city

        Returns:
            Generated settlement name
        """
        if is_capital:
            # Capitals often share the name of the state or region
            if random.random() < 0.6:
                return region_name

            if random.random() < 0.5:
                return f"New {region_name}"

            capital_suffixes = ["City", "Keep", "Throne", "Crown", "Hold", "Palace"]
            return f"{region_name} {random.choice(capital_suffixes)}"

        # Generate a name for regular settlements
        if random.random() < 0.3:
            # Use a prefix with region name
            prefix = random.choice(self.settlement_name_prefixes)
            return f"{prefix} {region_name}"

        if random.random() < 0.3:
            # Use region name with a suffix
            suffix = random.choice(self.settlement_name_suffixes)
            return f"{region_name}{suffix}"

        # Generate a completely new name
        if random.random() < 0.5:
            # Use prefix + suffix
            prefix = random.choice(self.settlement_name_prefixes)
            suffix = random.choice(self.settlement_name_suffixes)
            return f"{prefix}{suffix}"
        else:
            # Use a random combination of syllables
            syllables = ["al", "an", "ar", "ba", "ber", "borg", "burgh", "by", "ca", "cen",
                         "cle", "co", "dal", "den", "dor", "el", "en", "er", "ford", "ga",
                         "gard", "gate", "gle", "glen", "ham", "haven", "hill", "in", "ing",
                         "ke", "la", "lake", "land", "le", "leigh", "li", "lin", "lis", "lo",
                         "mer", "mi", "minster", "mont", "more", "mouth", "na", "ne", "ness",
                         "nor", "o", "polis", "port", "pur", "ra", "ri", "rich", "ridge", "ris",
                         "ro", "se", "shaw", "shi", "shire", "side", "sta", "stead", "ston",
                         "stone", "ta", "ter", "terrace", "ton", "town", "vale", "valley",
                         "view", "ville", "vis", "wan", "water", "well", "wich", "wick",
                         "wood", "worth", "wyn"]

            name_length = random.randint(2, 4)
            name = "".join(random.choice(syllables) for _ in range(name_length))

            # Capitalize first letter
            return name.capitalize()

    def regenerate_spatial_index(self):
        """Regenerate the spatial index for fast location lookups"""
        self.location_grid = {}

        for location_id, location in self.locations.items():
            grid_x = int(location.x / self.grid_cell_size)
            grid_y = int(location.y / self.grid_cell_size)
            grid_key = f"{grid_x}_{grid_y}"

            if grid_key not in self.location_grid:
                self.location_grid[grid_key] = []

            self.location_grid[grid_key].append(location_id)

    def create_settlement(self, name: str, position: Tuple[float, float],
                          location_type: LocationType = LocationType.TOWN,
                          population: int = 0, state_id: str = "") -> Settlement:
        """
        Create a new settlement

        Args:
            name: Name of the settlement
            position: (x, y) coordinates
            location_type: Type of settlement
            population: Population count
            state_id: ID of the political entity it belongs to

        Returns:
            The created Settlement
        """
        # Generate ID
        settlement_id = f"settlement_{self.next_settlement_id}"
        self.next_settlement_id += 1

        # Create settlement
        settlement = Settlement(
            location_id=settlement_id,
            name=name,
            position=position,
            location_type=location_type,
            population=population
        )

        # Set additional properties
        settlement.state_id = state_id

        # Set as capital if appropriate
        if location_type == LocationType.CAPITAL and state_id:
            settlement.is_capital = True
            settlement.has_castle = True
            settlement.has_walls = True

        # Add to collections
        self.settlements[settlement_id] = settlement
        self.locations[settlement_id] = settlement

        # Update spatial index
        grid_x = int(position[0] / self.grid_cell_size)
        grid_y = int(position[1] / self.grid_cell_size)
        grid_key = f"{grid_x}_{grid_y}"

        if grid_key not in self.location_grid:
            self.location_grid[grid_key] = []

        self.location_grid[grid_key].append(settlement_id)

        return settlement

    def create_point_of_interest(self, name: str, position: Tuple[float, float],
                                 location_type: LocationType = LocationType.LANDMARK,
                                 category: PointOfInterestCategory = PointOfInterestCategory.SHOP,
                                 parent_location_id: Optional[str] = None) -> PointOfInterest:
        """
        Create a new point of interest

        Args:
            name: Name of the point of interest
            position: (x, y) coordinates
            location_type: Type of location
            category: Specific category of point of interest
            parent_location_id: ID of the parent location (e.g., city), if any

        Returns:
            The created PointOfInterest
        """
        # Generate ID
        poi_id = f"poi_{self.next_poi_id}"
        self.next_poi_id += 1

        # Create point of interest
        poi = PointOfInterest(
            location_id=poi_id,
            name=name,
            position=position,
            location_type=location_type,
            category=category,
            parent_location_id=parent_location_id
        )

        # Add to collections
        self.points_of_interest[poi_id] = poi
        self.locations[poi_id] = poi

        # If this POI belongs to a settlement, add it to the settlement's POIs
        if parent_location_id and parent_location_id in self.settlements:
            parent = self.settlements[parent_location_id]
            parent.points_of_interest.append(poi)

        # Update spatial index
        grid_x = int(position[0] / self.grid_cell_size)
        grid_y = int(position[1] / self.grid_cell_size)
        grid_key = f"{grid_x}_{grid_y}"

        if grid_key not in self.location_grid:
            self.location_grid[grid_key] = []

        self.location_grid[grid_key].append(poi_id)

        return poi

    def create_dungeon(self, name: str, position: Tuple[float, float],
                       location_type: LocationType = LocationType.DUNGEON,
                       difficulty: int = 1, size: str = "Medium") -> Dungeon:
        """
        Create a new dungeon

        Args:
            name: Name of the dungeon
            position: (x, y) coordinates
            location_type: Type of dungeon
            difficulty: Challenge rating (1-20)
            size: Size of the dungeon

        Returns:
            The created Dungeon
        """
        # Generate ID
        dungeon_id = f"dungeon_{self.next_dungeon_id}"
        self.next_dungeon_id += 1

        # Create dungeon
        dungeon = Dungeon(
            location_id=dungeon_id,
            name=name,
            position=position,
            location_type=location_type,
            difficulty=difficulty,
            size=size
        )

        # Add to collections
        self.dungeons[dungeon_id] = dungeon
        self.locations[dungeon_id] = dungeon

        # Update spatial index
        grid_x = int(position[0] / self.grid_cell_size)
        grid_y = int(position[1] / self.grid_cell_size)
        grid_key = f"{grid_x}_{grid_y}"

        if grid_key not in self.location_grid:
            self.location_grid[grid_key] = []

        self.location_grid[grid_key].append(dungeon_id)

        return dungeon

    def populate_settlement_with_points_of_interest(self, settlement_id: str) -> List[PointOfInterest]:
        """
        Populate a settlement with points of interest

        Args:
            settlement_id: ID of the settlement to populate

        Returns:
            List of created points of interest
        """
        if settlement_id not in self.settlements:
            return []

        settlement = self.settlements[settlement_id]
        created_pois = []

        # Determine how many POIs based on settlement size
        population = settlement.population
        min_pois = 0
        max_pois = 0

        if population >= 25000:  # Capital or large city
            min_pois = 15
            max_pois = 30
        elif population >= 10000:  # City
            min_pois = 10
            max_pois = 20
        elif population >= 5000:  # Town
            min_pois = 5
            max_pois = 15
        elif population >= 1000:  # Village
            min_pois = 3
            max_pois = 8
        else:  # Hamlet
            min_pois = 1
            max_pois = 3

        num_pois = random.randint(min_pois, max_pois)

        # Generate POIs
        for _ in range(num_pois):
            poi_type = self.select_poi_type_for_settlement(settlement)
            poi_name = self.generate_poi_name(poi_type, settlement.name)

            # Create a position slightly offset from the settlement
            offset_x = random.uniform(-0.5, 0.5)
            offset_y = random.uniform(-0.5, 0.5)
            poi_pos = (settlement.x + offset_x, settlement.y + offset_y)

            # Create the POI
            poi = self.create_point_of_interest(
                name=poi_name,
                position=poi_pos,
                location_type=LocationType.LANDMARK,
                category=poi_type,
                parent_location_id=settlement_id
            )

            created_pois.append(poi)

        return created_pois

    def select_poi_type_for_settlement(self, settlement: Settlement) -> PointOfInterestCategory:
        """
        Select an appropriate POI type for a settlement

        Args:
            settlement: Settlement to select POI type for

        Returns:
            Selected POI category
        """
        # Basic POIs that every settlement should have
        basic_pois = [
            PointOfInterestCategory.TAVERN,
            PointOfInterestCategory.SHOP,
            PointOfInterestCategory.BLACKSMITH
        ]

        # Check if settlement already has a tavern
        existing_types = [poi.category for poi in settlement.points_of_interest]
        missing_basics = [poi for poi in basic_pois if poi not in existing_types]

        if missing_basics:
            return random.choice(missing_basics)

        # POIs for larger settlements
        if settlement.population >= 5000:
            advanced_pois = [
                PointOfInterestCategory.INN,
                PointOfInterestCategory.TEMPLE,
                PointOfInterestCategory.GUILDHALL,
                PointOfInterestCategory.MARKET,
                PointOfInterestCategory.MANSION,
                PointOfInterestCategory.LIBRARY
            ]

            # Add special POIs for capitals
            if settlement.is_capital:
                advanced_pois.extend([
                    PointOfInterestCategory.PALACE,
                    PointOfInterestCategory.ARENA,
                    PointOfInterestCategory.MILITARY_POST,
                    PointOfInterestCategory.WIZARD_TOWER
                ])

            return random.choice(advanced_pois)

        # POIs for medium settlements
        if settlement.population >= 1000:
            medium_pois = [
                PointOfInterestCategory.INN,
                PointOfInterestCategory.TEMPLE,
                PointOfInterestCategory.MARKET,
                PointOfInterestCategory.STABLE
            ]
            return random.choice(medium_pois)

        # POIs for small settlements
        small_pois = [
            PointOfInterestCategory.INN,
            PointOfInterestCategory.FARM,
            PointOfInterestCategory.STABLE
        ]
        return random.choice(small_pois)

    def generate_poi_name(self, poi_type: PointOfInterestCategory, settlement_name: str) -> str:
        """
        Generate a name for a point of interest

        Args:
            poi_type: Type of POI
            settlement_name: Name of the settlement it's in

        Returns:
            Generated POI name
        """
        if poi_type == PointOfInterestCategory.TAVERN:
            prefixes = ["The", "Ye Olde", "Old", "Silver", "Golden", "Red", "Black", "Blue", "Green"]
            nouns = ["Dragon", "Lion", "Eagle", "Crown", "Sword", "Shield", "Anvil", "Hammer",
                     "Goblet", "Flagon", "Barrel", "Tankard", "Boar", "Bear", "Wolf", "Fox",
                     "Mermaid", "Sailor", "Merchant", "Traveler", "Wanderer", "Adventurer"]
            return f"{random.choice(prefixes)} {random.choice(nouns)}"

        elif poi_type == PointOfInterestCategory.INN:
            prefixes = ["The", "Ye Olde", "Old", "Cozy", "Restful", "Quiet", "Travelers'", "Wayfarers'"]
            nouns = ["Rest", "Respite", "Haven", "Hearth", "Bed", "Pillow", "Lodging", "Rooms",
                     "Stop", "Welcome", "Comfort", "Retreat", "Roost"]
            return f"{random.choice(prefixes)} {random.choice(nouns)}"

        elif poi_type == PointOfInterestCategory.SHOP:
            owner_names = ["Smith", "Johnson", "Brown", "Miller", "Baker", "Fisher", "Cooper",
                           "Potter", "Weaver", "Tanner", "Chandler", "Fletcher", "Wright"]
            goods = ["Goods", "Wares", "Supplies", "Merchandise", "Trade Goods", "Curiosities",
                     "Sundries", "Provisions", "Necessities", "Oddities"]
            if random.random() < 0.5:
                return f"{random.choice(owner_names)}'s {random.choice(goods)}"
            else:
                return f"{settlement_name} General Store"

        elif poi_type == PointOfInterestCategory.TEMPLE:
            deities = ["Light", "Sun", "Moon", "Stars", "Nature", "Life", "Death", "War",
                       "Peace", "Wisdom", "Knowledge", "Strength", "Courage", "Love", "Fate"]

            if random.random() < 0.5:
                return f"Temple of {random.choice(deities)}"
            else:
                return f"The {random.choice(deities)} Sanctuary"

        elif poi_type == PointOfInterestCategory.BLACKSMITH:
            prefixes = ["The", "Hot", "Fiery", "Mighty", "Strong", "Skilled", "Master"]
            nouns = ["Anvil", "Hammer", "Forge", "Furnace", "Ingot", "Steel", "Iron", "Metal"]

            if random.random() < 0.5:
                return f"{random.choice(prefixes)} {random.choice(nouns)}"
            else:
                owner_names = ["Smith", "Hammer", "Forge", "Steel", "Iron", "Anvil"]
                return f"{random.choice(owner_names)}'s Smithy"

        elif poi_type == PointOfInterestCategory.PALACE:
            return f"{settlement_name} Palace"

        elif poi_type == PointOfInterestCategory.GUILDHALL:
            guilds = ["Merchants", "Crafters", "Masons", "Carpenters", "Brewers", "Bakers",
                      "Alchemists", "Scribes", "Artists", "Musicians", "Adventurers"]
            return f"{random.choice(guilds)} Guild"

        # Default naming pattern for other POI types
        return f"{settlement_name} {poi_type.value}"

    def get_locations_within_distance(self, center_x: float, center_y: float,
                                      distance: float) -> List[Location]:
        """
        Find all locations within a certain distance of a point

        Args:
            center_x: X coordinate of center point
            center_y: Y coordinate of center point
            distance: Maximum distance

        Returns:
            List of locations within the distance
        """
        result = []

        # Calculate grid cell range to search
        grid_radius = int(distance / self.grid_cell_size) + 1
        center_grid_x = int(center_x / self.grid_cell_size)
        center_grid_y = int(center_y / self.grid_cell_size)

        # Search all grid cells within radius
        for dx in range(-grid_radius, grid_radius + 1):
            for dy in range(-grid_radius, grid_radius + 1):
                grid_key = f"{center_grid_x + dx}_{center_grid_y + dy}"

                if grid_key in self.location_grid:
                    # Check each location in this grid cell
                    for location_id in self.location_grid[grid_key]:
                        location = self.locations.get(location_id)

                        if location:
                            # Calculate actual distance
                            dx = location.x - center_x
                            dy = location.y - center_y
                            actual_distance = math.sqrt(dx * dx + dy * dy)

                            if actual_distance <= distance:
                                result.append(location)

        return result

    def get_nearest_location(self, x: float, y: float,
                             location_type: Optional[LocationType] = None) -> Optional[Location]:
        """
        Find the nearest location to a point

        Args:
            x: X coordinate
            y: Y coordinate
            location_type: Optional filter for location type

        Returns:
            Nearest location or None if none found
        """
        nearest_location = None
        nearest_distance = float('inf')

        # Search in expanding grid cells
        for radius in range(1, 10):  # Limit search radius
            found = False

            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check the perimeter of each square
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    grid_x = int(x / self.grid_cell_size) + dx
                    grid_y = int(y / self.grid_cell_size) + dy
                    grid_key = f"{grid_x}_{grid_y}"

                    if grid_key in self.location_grid:
                        for location_id in self.location_grid[grid_key]:
                            location = self.locations.get(location_id)

                            if not location:
                                continue

                            # Skip if type doesn't match filter
                            if location_type and location.type != location_type:
                                continue

                            # Calculate distance
                            dx = location.x - x
                            dy = location.y - y
                            distance = math.sqrt(dx * dx + dy * dy)

                            if distance < nearest_distance:
                                nearest_distance = distance
                                nearest_location = location
                                found = True

            # Stop searching if we found a location in this radius
            if found:
                break

        return nearest_location

    def get_locations_by_type(self, location_type: LocationType) -> List[Location]:
        """
        Get all locations of a specific type

        Args:
            location_type: Type of locations to get

        Returns:
            List of locations of the specified type
        """
        return [loc for loc in self.locations.values() if loc.type == location_type]

    def get_settlements_by_state(self, state_id: str) -> List[Settlement]:
        """
        Get all settlements belonging to a political entity

        Args:
            state_id: ID of the political entity

        Returns:
            List of settlements belonging to the entity
        """
        return [s for s in self.settlements.values() if s.state_id == state_id]

    def get_capital_of_state(self, state_id: str) -> Optional[Settlement]:
        """
        Get the capital settlement of a political entity

        Args:
            state_id: ID of the political entity

        Returns:
            Capital settlement or None if not found
        """
        for settlement in self.settlements.values():
            if settlement.state_id == state_id and settlement.is_capital:
                return settlement

        return None

    def generate_dungeons_in_region(self, region_id: str, count: int = 3) -> List[Dungeon]:
        """
        Generate dungeons in a specific region

        Args:
            region_id: ID of the region to place dungeons in
            count: Number of dungeons to generate

        Returns:
            List of created dungeons
        """
        created_dungeons = []

        # Get region information
        if not self.region_manager:
            return []

        region = self.region_manager.get_region(region_id)
        if not region:
            return []

        # Get suitable locations for dungeons
        suitable_locations = []

        # Try to find suitable locations based on terrain
        for cell_id in region.cell_ids:
            terrain = self.region_manager.GetTerrainTypeForCell(cell_id)

            # Dungeons are often in mountains, hills, or forests
            if terrain in ["mountain", "hill", "forest", "highland"]:
                suitable_locations.append(cell_id)

        # If no suitable locations found, use any cell
        if not suitable_locations and region.cell_ids:
            suitable_locations = list(region.cell_ids)

        # Generate dungeons
        for _ in range(min(count, len(suitable_locations))):
            # Choose a location
            cell_id = random.choice(suitable_locations)
            suitable_locations.remove(cell_id)  # Don't reuse the same location

            # Get position
            x, y = self.convert_cell_id_to_position(cell_id)

            # Generate dungeon
            name = self.generate_dungeon_name()
            difficulty = random.randint(1, 20)
            size = random.choice(["Small", "Medium", "Large"])

            dungeon = self.create_dungeon(
                name=name,
                position=(x, y),
                location_type=LocationType.DUNGEON,
                difficulty=difficulty,
                size=size
            )

            dungeon.region_id = region_id

            # Add some details
            dungeon.origin = random.choice([
                "natural", "constructed", "magical", "divine", "demonic", "ancient"
            ])

            # Add appropriate creatures
            dungeon.current_inhabitants = self.generate_dungeon_inhabitants(difficulty)

            created_dungeons.append(dungeon)

        return created_dungeons

    def generate_dungeon_name(self) -> str:
        """
        Generate a name for a dungeon

        Returns:
            Generated dungeon name
        """
        prefixes = [
            "Dark", "Deep", "Black", "Shadow", "Grim", "Dire", "Forgotten", "Lost", "Ancient",
            "Haunted", "Cursed", "Abandoned", "Secret", "Hidden", "Infested", "Forbidden",
            "Sunken", "Ruined", "Shattered", "Crumbling", "Elder", "Primordial", "Elemental"
        ]

        nouns = [
            "Caverns", "Caves", "Catacombs", "Crypts", "Tombs", "Temple", "Shrine", "Monastery",
            "Halls", "Palace", "Castle", "Fortress", "Tower", "Keep", "Barrow", "Ruins",
            "Depths", "Labyrinth", "Maze", "Pits", "Mine", "Tunnels", "Vaults", "Sanctum"
        ]

        return f"{random.choice(prefixes)} {random.choice(nouns)}"

    def generate_dungeon_inhabitants(self, difficulty: int) -> List[str]:
        """
        Generate a list of inhabitants for a dungeon based on difficulty

        Args:
            difficulty: Challenge rating (1-20)

        Returns:
            List of inhabitant types
        """
        # Group monsters by difficulty
        easy_monsters = [
            "Goblins", "Kobolds", "Bandits", "Giant Rats", "Skeletons", "Zombies",
            "Giant Spiders", "Stirges", "Wolves", "Giant Bats"
        ]

        medium_monsters = [
            "Orcs", "Hobgoblins", "Bugbears", "Ghouls", "Cult Fanatics", "Giant Snakes",
            "Wererats", "Animated Armors", "Swarms of Insects", "Duergar"
        ]

        hard_monsters = [
            "Trolls", "Ogres", "Werewolves", "Wights", "Ghasts", "Mimics",
            "Phase Spiders", "Harpies", "Yuan-ti", "Gargoyles"
        ]

        very_hard_monsters = [
            "Giants", "Chimeras", "Elementals", "Vampire Spawn", "Wraiths",
            "Medusas", "Basilisks", "Young Dragons", "Manticores", "Golems"
        ]

        deadly_monsters = [
            "Adult Dragons", "Liches", "Demons", "Devils", "Vampires",
            "Beholders", "Mind Flayers", "Aboleths", "Ancient Undead", "Mages"
        ]

        # Select appropriate monsters based on difficulty
        if difficulty <= 4:
            monsters = easy_monsters
        elif difficulty <= 8:
            monsters = medium_monsters
        elif difficulty <= 12:
            monsters = hard_monsters
        elif difficulty <= 16:
            monsters = very_hard_monsters
        else:
            monsters = deadly_monsters

        # Select 1-3 types of inhabitants
        num_types = random.randint(1, 3)
        return random.sample(monsters, min(num_types, len(monsters)))

    def save_to_json(self, filepath: str) -> bool:
        """
        Save location data to a JSON file

        Args:
            filepath: Path to save file

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "locations": {loc_id: loc.to_dict() for loc_id, loc in self.locations.items()},
                "next_ids": {
                    "location_id": self.next_location_id,
                    "settlement_id": self.next_settlement_id,
                    "poi_id": self.next_poi_id,
                    "dungeon_id": self.next_dungeon_id
                }
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Saved location data to {filepath}")
            return True
        except Exception as ex:
            print(f"Error saving location data: {str(ex)}")
            return False

    def load_from_json(self, filepath: str) -> bool:
        """
        Load location data from a JSON file

        Args:
            filepath: Path to load file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Clear existing collections
            self.locations.clear()
            self.settlements.clear()
            self.points_of_interest.clear()
            self.dungeons.clear()

            # Load locations
            locations_data = data.get("locations", {})

            for loc_id, loc_data in locations_data.items():
                location_type = loc_data.get("type", "")

                if "population" in loc_data:
                    # This is a settlement
                    settlement = Settlement.from_dict(loc_data)
                    self.settlements[loc_id] = settlement
                    self.locations[loc_id] = settlement
                elif "category" in loc_data:
                    # This is a point of interest
                    poi = PointOfInterest.from_dict(loc_data)
                    self.points_of_interest[loc_id] = poi
                    self.locations[loc_id] = poi
                elif "difficulty" in loc_data:
                    # This is a dungeon
                    dungeon = Dungeon.from_dict(loc_data)
                    self.dungeons[loc_id] = dungeon
                    self.locations[loc_id] = dungeon
                else:
                    # Generic location
                    location = Location.from_dict(loc_data)
                    self.locations[loc_id] = location

            # Load next IDs
            next_ids = data.get("next_ids", {})
            self.next_location_id = next_ids.get("location_id", self.next_location_id)
            self.next_settlement_id = next_ids.get("settlement_id", self.next_settlement_id)
            self.next_poi_id = next_ids.get("poi_id", self.next_poi_id)
            self.next_dungeon_id = next_ids.get("dungeon_id", self.next_dungeon_id)

            # Regenerate spatial index
            self.regenerate_spatial_index()

            print(f"Loaded {len(self.locations)} locations from {filepath}")
            return True
        except Exception as ex:
            print(f"Error loading location data: {str(ex)}")
            return False

    def update_world_state(self):
        """Update the world state with the current locations data"""
        if not self.world_state:
            print("World state not available, cannot update")
            return

        try:
            # Convert locations to the format expected by world state
            world_state_locations = {}

            for loc_id, location in self.locations.items():
                # Create base location data
                location_data = {
                    "id": location.id,
                    "name": location.name,
                    "x": location.x,
                    "y": location.y,
                    "type": location.type.value
                }

                # Add settlement-specific data
                if isinstance(location, Settlement):
                    location_data["population"] = location.population
                    location_data["is_capital"] = location.is_capital
                    location_data["is_port"] = location.is_port

                world_state_locations[loc_id] = location_data

            # Update world state
            self.world_state.locations = world_state_locations

            print(f"Updated world state with {len(world_state_locations)} locations")
        except Exception as ex:
            print(f"Error updating world state: {str(ex)}")

    # region Unity-Python Interface Methods

    def GetLocationById(self, location_id: str) -> Dict[str, Any]:
        """
        Unity interface method: Get location data by ID

        Args:
            location_id: ID of the location

        Returns:
            Dictionary containing location data, or empty dict if not found
        """
        if location_id in self.locations:
            return self.locations[location_id].to_dict()
        return {}

    def GetSettlementById(self, settlement_id: str) -> Dict[str, Any]:
        """
        Unity interface method: Get settlement data by ID

        Args:
            settlement_id: ID of the settlement

        Returns:
            Dictionary containing settlement data, or empty dict if not found
        """
        if settlement_id in self.settlements:
            return self.settlements[settlement_id].to_dict()
        return {}

    def GetLocationsInRange(self, x: float, y: float, distance: float) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get locations within a distance of a point

        Args:
            x: X coordinate
            y: Y coordinate
            distance: Maximum distance

        Returns:
            List of dictionaries containing location data
        """
        locations = self.get_locations_within_distance(x, y, distance)
        return [loc.to_dict() for loc in locations]

    def GetLocationsOfType(self, location_type: str) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all locations of a specific type

        Args:
            location_type: Type of locations to get

        Returns:
            List of dictionaries containing location data
        """
        try:
            loc_type = LocationType(location_type)
            locations = self.get_locations_by_type(loc_type)
            return [loc.to_dict() for loc in locations]
        except Exception:
            return []

    def GetNearestLocation(self, x: float, y: float, location_type: str = None) -> Dict[str, Any]:
        """
        Unity interface method: Get the nearest location to a point

        Args:
            x: X coordinate
            y: Y coordinate
            location_type: Optional type of location to find

        Returns:
            Dictionary containing location data, or empty dict if not found
        """
        try:
            loc_type = LocationType(location_type) if location_type else None
            location = self.get_nearest_location(x, y, loc_type)

            if location:
                return location.to_dict()

            return {}
        except Exception:
            return {}

    def GetSettlementsByState(self, state_id: str) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all settlements in a state

        Args:
            state_id: ID of the state

        Returns:
            List of dictionaries containing settlement data
        """
        settlements = self.get_settlements_by_state(state_id)
        return [s.to_dict() for s in settlements]

    def GetCapitalOfState(self, state_id: str) -> Dict[str, Any]:
        """
        Unity interface method: Get the capital settlement of a state

        Args:
            state_id: ID of the state

        Returns:
            Dictionary containing capital data, or empty dict if not found
        """
        capital = self.get_capital_of_state(state_id)

        if capital:
            return capital.to_dict()

        return {}

    def GetPointsOfInterestInSettlement(self, settlement_id: str) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all points of interest in a settlement

        Args:
            settlement_id: ID of the settlement

        Returns:
            List of dictionaries containing POI data
        """
        if settlement_id in self.settlements:
            settlement = self.settlements[settlement_id]
            return [poi.to_dict() for poi in settlement.points_of_interest]

        return []

    def CreateNewSettlement(self, name: str, x: float, y: float,
                            location_type: str = "Town", population: int = 0,
                            state_id: str = "") -> str:
        """
        Unity interface method: Create a new settlement

        Args:
            name: Name of the settlement
            x: X coordinate
            y: Y coordinate
            location_type: Type of settlement
            population: Population count
            state_id: ID of the state it belongs to

        Returns:
            ID of the created settlement, or empty string if failed
        """
        try:
            # Convert location type
            loc_type = LocationType(location_type)

            # Create settlement
            settlement = self.create_settlement(
                name=name,
                position=(x, y),
                location_type=loc_type,
                population=population,
                state_id=state_id
            )

            return settlement.id
        except Exception as ex:
            print(f"Error creating settlement: {str(ex)}")
            return ""

    def CreateNewPointOfInterest(self, name: str, x: float, y: float,
                                 location_type: str = "Landmark", category: str = "Shop",
                                 parent_location_id: str = None) -> str:
        """
        Unity interface method: Create a new point of interest

        Args:
            name: Name of the point of interest
            x: X coordinate
            y: Y coordinate
            location_type: Type of location
            category: Category of POI
            parent_location_id: ID of parent location

        Returns:
            ID of the created POI, or empty string if failed
        """
        try:
            # Convert location type and category
            loc_type = LocationType(location_type)
            poi_category = PointOfInterestCategory(category)

            # Create POI
            poi = self.create_point_of_interest(
                name=name,
                position=(x, y),
                location_type=loc_type,
                category=poi_category,
                parent_location_id=parent_location_id
            )

            return poi.id
        except Exception as ex:
            print(f"Error creating point of interest: {str(ex)}")
            return ""

    def CreateNewDungeon(self, name: str, x: float, y: float,
                         location_type: str = "Dungeon", difficulty: int = 1,
                         size: str = "Medium") -> str:
        """
        Unity interface method: Create a new dungeon

        Args:
            name: Name of the dungeon
            x: X coordinate
            y: Y coordinate
            location_type: Type of dungeon
            difficulty: Challenge rating
            size: Size of the dungeon

        Returns:
            ID of the created dungeon, or empty string if failed
        """
        try:
            # Convert location type
            loc_type = LocationType(location_type)

            # Create dungeon
            dungeon = self.create_dungeon(
                name=name,
                position=(x, y),
                location_type=loc_type,
                difficulty=difficulty,
                size=size
            )

            return dungeon.id
        except Exception as ex:
            print(f"Error creating dungeon: {str(ex)}")
            return ""

    def PopulateSettlementWithPOIs(self, settlement_id: str) -> List[str]:
        """
        Unity interface method: Populate a settlement with points of interest

        Args:
            settlement_id: ID of the settlement to populate

        Returns:
            List of IDs of created POIs
        """
        pois = self.populate_settlement_with_points_of_interest(settlement_id)
        return [poi.id for poi in pois]

    def GenerateDungeonsInRegion(self, region_id: str, count: int = 3) -> List[str]:
        """
        Unity interface method: Generate dungeons in a region

        Args:
            region_id: ID of the region
            count: Number of dungeons to generate

        Returns:
            List of IDs of created dungeons
        """
        dungeons = self.generate_dungeons_in_region(region_id, count)
        return [dungeon.id for dungeon in dungeons]

    def SaveLocationsToFile(self, filepath: str) -> bool:
        """
        Unity interface method: Save location data to a file

        Args:
            filepath: Path to save file

        Returns:
            True if successful, False otherwise
        """
        return self.save_to_json(filepath)

    def LoadLocationsFromFile(self, filepath: str) -> bool:
        """
        Unity interface method: Load location data from a file

        Args:
            filepath: Path to load file

        Returns:
            True if successful, False otherwise
        """
        return self.load_from_json(filepath)

    def GenerateAllSettlements(self) -> int:
        """
        Unity interface method: Generate settlements for all political entities

        Returns:
            Number of settlements generated
        """
        initial_count = len(self.settlements)
        self.generate_settlements_from_political_entities()
        return len(self.settlements) - initial_count
    # endregion