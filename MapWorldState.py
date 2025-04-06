import os
import json
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class MapRegion:
    """Represents a geographical region with biome and climate information"""
    
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: str = ""  # Biome type
        self.climate: str = ""  # Climate category
        self.is_dangerous: bool = False  # Whether the region is dangerous
        self.resources: List[str] = []  # Resources available


class MapPoliticalEntity:
    """Represents a political entity like a kingdom, empire, etc."""
    
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.capital_id: str = ""  # ID of the capital location
        self.color: str = ""  # Color on the map
        self.government: str = ""  # Type of government
        self.formation_year: int = 0  # Year when the entity was formed
        self.stability: float = 0.0  # Political stability (0-1)
        self.relationships: List[str] = []  # Relationships with other entities


class MapLocation:
    """Represents a location like a city, town, or point of interest"""
    
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: str = ""  # Settlement type
        self.x: float = 0.0  # X coordinate
        self.y: float = 0.0  # Y coordinate
        self.state_id: str = ""  # ID of the political entity it belongs to
        self.population: int = 0  # Population count
        self.prosperity: float = 0.0  # Economic prosperity (0-1)
        self.points_of_interest: List[str] = []  # Notable locations within


class MapWorldEvent:
    """Represents a world event that can affect regions, locations, or political entities"""
    
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: str = ""  # Political, Natural, Cultural, Economic, Military
        self.description: str = ""
        self.year: int = 0
        self.month: int = 0
        self.season: str = ""
        self.related_region_id: str = ""  # ID of related region (if applicable)
        self.related_location_id: str = ""  # ID of related location (if applicable)
        self.related_entity_id: str = ""  # ID of related political entity (if applicable)


class WorldStateSaveData:
    """Container for world state data for saving/loading"""
    
    def __init__(self):
        self.regions: Dict[str, MapRegion] = {}
        self.political_entities: Dict[str, MapPoliticalEntity] = {}
        self.locations: Dict[str, MapLocation] = {}
        self.discovered_locations: List[MapLocation] = []
        self.world_event_history: List[MapWorldEvent] = []
        self.current_year: int = 0
        self.current_month: int = 0
        self.current_season: str = ""
        self.regional_weather: Dict[str, str] = {}


class MapWorldState:
    """
    Core component for maintaining the overall world state derived from Azgaar's Fantasy Map Generator.
    Provides interfaces for querying map data and tracking changes to the world state.
    """
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MapWorldState()
        return cls._instance
    
    def __init__(self):
        # Reference to other core components
        self.integration_manager = None  # Will be set during initialization
        self.local_server = None  # Will be set during initialization
        
        # World map data
        self.map_file_path: str = "Maps/test.map"
        self.map_data: Dict = {}
        
        # Core world state components
        self.regions: Dict[str, MapRegion] = {}
        self.political_entities: Dict[str, MapPoliticalEntity] = {}
        self.locations: Dict[str, MapLocation] = {}
        
        # Player tracking
        self.current_player_location: Optional[MapLocation] = None
        self.discovered_locations: List[MapLocation] = []
        
        # Event history
        self.world_event_history: List[MapWorldEvent] = []
        
        # Path for saving/loading world state
        self.world_state_save_path: str = os.path.join(os.getcwd(), "WorldState.json")
        
        # World time tracking
        self.current_year: int = 1000
        self.current_month: int = 1
        self.current_season: str = "Spring"
        
        # Weather system
        self.regional_weather: Dict[str, str] = {}
        
        print("MapWorldState initialized")
    
    def initialize(self):
        """Initialize the world state from map data"""
        try:
            # Try to load existing world state first
            if self.load_world_state():
                print("World state loaded from saved file")
                return
            
            # If no saved state, create a new one from map file
            map_content = self.read_map_file(self.map_file_path)
            if map_content:
                self.parse_map_data(map_content)
                print("New world state initialized from map file")
            else:
                print("Failed to read map file")
        except Exception as ex:
            print(f"Error initializing world state: {str(ex)}")
    
    def read_map_file(self, file_path: str) -> Optional[str]:
        """Read the map file content"""
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as file:
                return file.read()
        
        print(f"Map file not found at {full_path}, trying alternative locations")
        
        # Try alternative location
        alt_path = os.path.join(os.getcwd(), "AzgaarViewer", "Maps", os.path.basename(file_path))
        if os.path.exists(alt_path):
            with open(alt_path, 'r') as file:
                return file.read()
        
        print(f"Map file not found at {alt_path} either")
        return None
    
    def parse_map_data(self, map_content: str):
        """Parse map data from the map file content"""
        try:
            # Parse the map data JSON
            self.map_data = json.loads(map_content)
            
            # Initialize regions from map's biomes
            self.initialize_regions()
            
            # Initialize political entities from map's states
            self.initialize_political_entities()
            
            # Initialize locations from map's burgs
            self.initialize_locations()
            
            # Set default weather patterns
            self.initialize_weather()
        except Exception as ex:
            print(f"Error parsing map data: {str(ex)}")
    
    def initialize_regions(self):
        """Initialize regions from map's biomes data"""
        self.regions.clear()
        
        try:
            # Extract biomes data from map
            biomes_token = self.map_data.get("biomes", [])
            if biomes_token:
                for biome in biomes_token:
                    biome_id = str(biome.get("i", ""))
                    name = biome.get("name", "")
                    biome_type = biome.get("type", "")
                    
                    region = MapRegion()
                    region.id = biome_id
                    region.name = name
                    region.type = biome_type
                    region.climate = self.determine_climate_from_biome(biome_type)
                    region.is_dangerous = self.is_dangerous_biome(biome_type)
                    
                    self.regions[biome_id] = region
                
                print(f"Initialized {len(self.regions)} regions from map data")
        except Exception as ex:
            print(f"Error initializing regions: {str(ex)}")
    
    def initialize_political_entities(self):
        """Initialize political entities from map's states data"""
        self.political_entities.clear()
        
        try:
            # Extract states data from map
            states_token = self.map_data.get("states", [])
            if states_token:
                for state in states_token:
                    state_id = str(state.get("i", ""))
                    name = state.get("name", "")
                    color = state.get("color", "")
                    capital = str(state.get("capital", ""))
                    
                    entity = MapPoliticalEntity()
                    entity.id = state_id
                    entity.name = name
                    entity.capital_id = capital
                    entity.color = color
                    entity.government = self.generate_random_government()
                    entity.formation_year = self.current_year - random.randint(50, 500)
                    entity.stability = random.random()
                    
                    self.political_entities[state_id] = entity
                
                print(f"Initialized {len(self.political_entities)} political entities from map data")
        except Exception as ex:
            print(f"Error initializing political entities: {str(ex)}")
    
    def initialize_locations(self):
        """Initialize locations from map's burgs data"""
        self.locations.clear()
        
        try:
            # Extract burgs data from map
            burgs_token = self.map_data.get("burgs", [])
            if burgs_token:
                for i in range(1, len(burgs_token)):  # Skip first (empty) burg
                    burg = burgs_token[i]
                    
                    burg_id = str(burg.get("i", ""))
                    name = burg.get("name", "")
                    state_id = str(burg.get("state", ""))
                    population = float(burg.get("population", 0))
                    
                    # Get coordinates
                    x = float(burg.get("x", 0))
                    y = float(burg.get("y", 0))
                    
                    # Create location object
                    location = MapLocation()
                    location.id = burg_id
                    location.name = name
                    location.type = "settlement"
                    location.x = x
                    location.y = y
                    location.state_id = state_id
                    location.population = int(population * 1000)  # Convert to actual population
                    location.prosperity = random.uniform(0.2, 0.9)
                    location.points_of_interest = self.generate_points_of_interest(name, population)
                    
                    self.locations[burg_id] = location
                
                print(f"Initialized {len(self.locations)} locations from map data")
        except Exception as ex:
            print(f"Error initializing locations: {str(ex)}")
    
    def initialize_weather(self):
        """Initialize weather patterns across the world"""
        self.regional_weather.clear()
        
        for region_key, region in self.regions.items():
            self.regional_weather[region_key] = self.generate_weather_for_climate(region.climate)
        
        print("Weather patterns initialized")
    
    def save_world_state(self) -> bool:
        """Save the current world state to a file"""
        try:
            save_data = self.create_save_data()
            
            # Convert to dictionary for JSON serialization
            save_dict = {
                "regions": self.serialize_dict(save_data.regions),
                "political_entities": self.serialize_dict(save_data.political_entities),
                "locations": self.serialize_dict(save_data.locations),
                "discovered_locations": self.serialize_list(save_data.discovered_locations),
                "world_event_history": self.serialize_list(save_data.world_event_history),
                "current_year": save_data.current_year,
                "current_month": save_data.current_month,
                "current_season": save_data.current_season,
                "regional_weather": save_data.regional_weather
            }
            
            json_data = json.dumps(save_dict, indent=4)
            with open(self.world_state_save_path, 'w') as file:
                file.write(json_data)
            
            print(f"World state saved to {self.world_state_save_path}")
            return True
        except Exception as ex:
            print(f"Error saving world state: {str(ex)}")
            return False
    
    def create_save_data(self) -> WorldStateSaveData:
        """Create save data object from current state"""
        save_data = WorldStateSaveData()
        save_data.regions = self.regions
        save_data.political_entities = self.political_entities
        save_data.locations = self.locations
        save_data.discovered_locations = self.discovered_locations
        save_data.world_event_history = self.world_event_history
        save_data.current_year = self.current_year
        save_data.current_month = self.current_month
        save_data.current_season = self.current_season
        save_data.regional_weather = self.regional_weather
        return save_data
    
    def serialize_dict(self, data_dict):
        """Helper method to serialize dictionary of objects to dictionary of dictionaries"""
        result = {}
        for key, value in data_dict.items():
            result[key] = value.__dict__
        return result
    
    def serialize_list(self, data_list):
        """Helper method to serialize list of objects to list of dictionaries"""
        return [item.__dict__ for item in data_list]
    
    def load_world_state(self) -> bool:
        """Load the world state from a file"""
        try:
            if not os.path.exists(self.world_state_save_path):
                print("No saved world state found")
                return False
            
            with open(self.world_state_save_path, 'r') as file:
                json_data = file.read()
            
            save_dict = json.loads(json_data)
            
            # Restore regions
            self.regions = self.deserialize_dict(save_dict.get("regions", {}), MapRegion)
            
            # Restore political entities
            self.political_entities = self.deserialize_dict(save_dict.get("political_entities", {}), MapPoliticalEntity)
            
            # Restore locations
            self.locations = self.deserialize_dict(save_dict.get("locations", {}), MapLocation)
            
            # Restore discovered locations
            self.discovered_locations = self.deserialize_list(save_dict.get("discovered_locations", []), MapLocation)
            
            # Restore world event history
            self.world_event_history = self.deserialize_list(save_dict.get("world_event_history", []), MapWorldEvent)
            
            # Restore basic properties
            self.current_year = save_dict.get("current_year", 1000)
            self.current_month = save_dict.get("current_month", 1)
            self.current_season = save_dict.get("current_season", "Spring")
            self.regional_weather = save_dict.get("regional_weather", {})
            
            print(f"World state loaded from {self.world_state_save_path}")
            return True
        except Exception as ex:
            print(f"Error loading world state: {str(ex)}")
            return False
    
    def deserialize_dict(self, data_dict, class_type):
        """Helper method to deserialize dictionary of dictionaries to dictionary of objects"""
        result = {}
        for key, value_dict in data_dict.items():
            obj = class_type()
            for attr_key, attr_value in value_dict.items():
                setattr(obj, attr_key, attr_value)
            result[key] = obj
        return result
    
    def deserialize_list(self, data_list, class_type):
        """Helper method to deserialize list of dictionaries to list of objects"""
        result = []
        for item_dict in data_list:
            obj = class_type()
            for key, value in item_dict.items():
                setattr(obj, key, value)
            result.append(obj)
        return result
    
    def get_locations_within_distance(self, x: float, y: float, distance: float) -> List[MapLocation]:
        """Query locations within a certain distance of a point"""
        result = []
        
        for location in self.locations.values():
            dx = location.x - x
            dy = location.y - y
            dist_squared = dx * dx + dy * dy
            
            if dist_squared <= distance * distance:
                result.append(location)
        
        return result
    
    def get_location_by_name(self, name: str) -> Optional[MapLocation]:
        """Get location by name (case-insensitive search)"""
        name = name.lower()
        for location in self.locations.values():
            if location.name.lower() == name:
                return location
        
        return None
    
    def set_player_location(self, location_id: str):
        """Set the player's current location and mark it as discovered"""
        if location_id in self.locations:
            location = self.locations[location_id]
            self.current_player_location = location
            
            if location not in self.discovered_locations:
                self.discovered_locations.append(location)
            
            print(f"Player location set to {location.name}")
        else:
            print(f"Location with ID {location_id} not found")
    
    def advance_time(self, months: int = 1):
        """Update the world state by advancing time"""
        # Track current month and year
        self.current_month += months
        while self.current_month > 12:
            self.current_month -= 12
            self.current_year += 1
        
        # Update season
        self.current_season = self.get_season_for_month(self.current_month)
        
        # Update weather patterns
        self.update_weather()
        
        # Process random world events based on time passage
        self.process_world_events(months)
        
        print(f"Time advanced to Year {self.current_year}, Month {self.current_month} ({self.current_season})")
    
    def process_world_events(self, months: int):
        """Process random world events based on time passage"""
        # Chance for events increases with more months passed
        event_chance = 5 * months  # 5% per month
        
        if random.randint(1, 100) <= event_chance:
            # Generate a random event
            world_event = self.generate_random_world_event()
            self.world_event_history.append(world_event)
            
            # Apply event effects
            self.apply_world_event_effects(world_event)
            
            print(f"World event occurred: {world_event.name}")
    
    def update_weather(self):
        """Update weather patterns across regions"""
        for region in self.regions:
            self.regional_weather[region.id] = self.generate_weather_for_climate(
                region.climate, self.current_season)
    
    # Helper methods
    
    def determine_climate_from_biome(self, biome_type: str) -> str:
        """Determine climate category from biome type"""
        biome_type = biome_type.lower()
        
        if "tropical" in biome_type or "savanna" in biome_type:
            return "tropical"
        elif "desert" in biome_type:
            return "arid"
        elif "temperate" in biome_type:
            return "temperate"
        elif "taiga" in biome_type or "tundra" in biome_type or "glacier" in biome_type:
            return "arctic"
        elif "wetland" in biome_type:
            return "humid"
        else:
            return "temperate"
    
    def is_dangerous_biome(self, biome_type: str) -> bool:
        """Check if a biome type is considered dangerous"""
        dangerous_biomes = ["tundra", "glacier", "hot desert", "cold desert", "wetland"]
        biome_type = biome_type.lower()
        
        return any(dangerous in biome_type for dangerous in dangerous_biomes)
    
    def generate_random_government(self) -> str:
        """Generate a random government type"""
        government_types = [
            "Monarchy", "Republic", "Theocracy", "Oligarchy",
            "Despotism", "Federation", "Tribal Confederation", "Magocracy"
        ]
        
        return random.choice(government_types)
    
    def generate_points_of_interest(self, location_name: str, population_factor: float) -> List[str]:
        """Generate points of interest for a location"""
        poi = []
        
        # Higher population means more points of interest
        num_poi = int(population_factor * 10) + 1
        num_poi = max(1, min(num_poi, 10))
        
        poi_types = [
            "Inn", "Tavern", "Market", "Temple", "Guild Hall",
            "Blacksmith", "Stable", "Manor", "Garden", "Tower",
            "Library", "Shop", "Park", "Monument", "Warehouse"
        ]
        
        # Ensure at least one inn for travelers
        poi.append(f"The {self.generate_random_inn_name()} (Inn)")
        
        # Add additional points of interest
        for i in range(1, num_poi):
            poi_type = random.choice(poi_types)
            
            if poi_type in ["Inn", "Tavern"]:
                poi_name = self.generate_random_inn_name()
            elif poi_type == "Temple":
                poi_name = f"Temple of {self.generate_random_deity_name()}"
            else:
                # Use location name as part of POI name
                poi_name = f"{location_name}'s {poi_type}"
            
            poi.append(f"{poi_name} ({poi_type})")
        
        return poi
    
    def generate_random_inn_name(self) -> str:
        """Generate a random name for an inn or tavern"""
        adjectives = ["Prancing", "Golden", "Silver", "Rusty", "Laughing", "Sleeping", "Dancing", "Howling"]
        nouns = ["Pony", "Lion", "Dragon", "Sword", "Shield", "Giant", "Goblin", "Wizard", "Barrel", "Eagle"]
        
        return f"{random.choice(adjectives)} {random.choice(nouns)}"
    
    def generate_random_deity_name(self) -> str:
        """Generate a random deity name"""
        deity_names = [
            "Solaris", "Lunara", "Thalor", "Zephyra", "Terravox",
            "Aquarius", "Pyros", "Silvanus", "Mysteria", "Chronos"
        ]
        
        return random.choice(deity_names)
    
    def get_season_for_month(self, month: int) -> str:
        """Get the season for a given month"""
        # Northern hemisphere seasons
        if 3 <= month <= 5:
            return "Spring"
        elif 6 <= month <= 8:
            return "Summer"
        elif 9 <= month <= 11:
            return "Autumn"
        else:
            return "Winter"
    
    def generate_weather_for_climate(self, climate: str, season: str = None) -> str:
        """Generate weather for a climate and season"""
        if season is None:
            season = self.current_season
        
        # Weather patterns by climate and season
        weather_patterns = {
            "tropical": {
                "Spring": ["Rainy", "Thunderstorm", "Humid", "Cloudy", "Warm"],
                "Summer": ["Hot", "Humid", "Thunderstorm", "Rainy", "Stormy"],
                "Autumn": ["Rainy", "Humid", "Cloudy", "Warm", "Thunderstorm"],
                "Winter": ["Mild", "Warm", "Light Rain", "Humid", "Cloudy"]
            },
            "arid": {
                "Spring": ["Warm", "Dry", "Windy", "Clear", "Dusty"],
                "Summer": ["Hot", "Very Dry", "Clear", "Scorching", "Dusty"],
                "Autumn": ["Warm", "Dry", "Clear", "Windy", "Dusty"],
                "Winter": ["Cool", "Clear", "Cold Nights", "Dry", "Windy"]
            },
            "temperate": {
                "Spring": ["Mild", "Rainy", "Cloudy", "Windy", "Variable"],
                "Summer": ["Warm", "Sunny", "Clear", "Occasional Rain", "Humid"],
                "Autumn": ["Cool", "Rainy", "Windy", "Cloudy", "Foggy"],
                "Winter": ["Cold", "Snowy", "Freezing", "Icy", "Cloudy"]
            },
            "arctic": {
                "Spring": ["Cold", "Snowy", "Icy", "Windy", "Thawing"],
                "Summer": ["Cool", "Clear", "Mild", "Light Rain", "Bright"],
                "Autumn": ["Cold", "Windy", "Cloudy", "Early Snow", "Freezing"],
                "Winter": ["Freezing", "Blizzard", "Heavy Snow", "Ice Storm", "Dark"]
            },
            "humid": {
                "Spring": ["Misty", "Rainy", "Foggy", "Muddy", "Humid"],
                "Summer": ["Humid", "Hot", "Foggy", "Thunderstorm", "Muggy"],
                "Autumn": ["Rainy", "Foggy", "Misty", "Humid", "Cloudy"],
                "Winter": ["Cold Rain", "Sleet", "Foggy", "Icy", "Wet"]
            }
        }
        
        # Get weather options for this climate and season
        if climate in weather_patterns and season in weather_patterns[climate]:
            weather_options = weather_patterns[climate][season]
            return random.choice(weather_options)
        
        # Default weather if climate/season not found
        return "Clear"
    
    def generate_random_world_event(self) -> MapWorldEvent:
        """Generate a random world event"""
        event_types = ["Political", "Natural", "Cultural", "Economic", "Military"]
        event_type = random.choice(event_types)
        
        world_event = MapWorldEvent()
        world_event.id = str(uuid.uuid4())
        world_event.type = event_type
        world_event.year = self.current_year
        world_event.month = self.current_month
        world_event.season = self.current_season
        
        if event_type == "Political":
            self.generate_political_event(world_event)
        elif event_type == "Natural":
            self.generate_natural_event(world_event)
        elif event_type == "Cultural":
            self.generate_cultural_event(world_event)
        elif event_type == "Economic":
            self.generate_economic_event(world_event)
        elif event_type == "Military":
            self.generate_military_event(world_event)
        
        return world_event
    
    def generate_political_event(self, world_event: MapWorldEvent):
        """Generate a political event"""
        events = [
            "Succession Crisis", "New Ruler Crowned", "Political Alliance Formed",
            "Diplomatic Incident", "Treaty Signed", "Government Change"
        ]
        
        world_event.name = random.choice(events)
        
        # Select a random political entity for this event
        if self.political_entities:
            state_ids = list(self.political_entities.keys())
            world_event.related_entity_id = random.choice(state_ids)
            
            world_event.description = (
                f"A {world_event.name.lower()} has occurred in "
                f"{self.political_entities[world_event.related_entity_id].name}."
            )
    
    def generate_natural_event(self, world_event: MapWorldEvent):
        """Generate a natural event"""
        events = [
            "Earthquake", "Flood", "Drought", "Wildfire",
            "Harsh Winter", "Bountiful Harvest", "Disease Outbreak", "Meteor Shower"
        ]
        
        world_event.name = random.choice(events)
        
        # Select a random region for this event
        if self.regions:
            region_ids = list(self.regions.keys())
            world_event.related_region_id = random.choice(region_ids)
            
            world_event.description = (
                f"A {world_event.name.lower()} has affected the region of "
                f"{self.regions[world_event.related_region_id].name}."
            )
    
    def generate_cultural_event(self, world_event: MapWorldEvent):
        """Generate a cultural event"""
        events = [
            "Festival", "Religious Revival", "Artistic Renaissance",
            "Cultural Exchange", "New Philosophy", "Religious Schism"
        ]
        
        world_event.name = random.choice(events)
        
        # Select a random location for this event
        if self.locations:
            location_ids = list(self.locations.keys())
            world_event.related_location_id = random.choice(location_ids)
            
            world_event.description = (
                f"A {world_event.name.lower()} is taking place in "
                f"{self.locations[world_event.related_location_id].name}."
            )
    
    def generate_economic_event(self, world_event: MapWorldEvent):
        """Generate an economic event"""
        events = [
            "Economic Boom", "Trade Dispute", "New Trade Route",
            "Resource Discovery", "Market Crash", "Guild Formation"
        ]
        
        world_event.name = random.choice(events)
        
        # Select a random location for this event
        if self.locations:
            location_ids = list(self.locations.keys())
            world_event.related_location_id = random.choice(location_ids)
            
            world_event.description = (
                f"An {world_event.name.lower()} has occurred in "
                f"{self.locations[world_event.related_location_id].name}."
            )
    
    def generate_military_event(self, world_event: MapWorldEvent):
        """Generate a military event"""
        events = [
            "Border Skirmish", "Military Buildup", "Fortification Construction",
            "Monster Incursion", "Bandit Activity", "Hero's Quest"
        ]
        
        world_event.name = random.choice(events)
        
        # Select random political entities for this event
        if len(self.political_entities) >= 2:
            state_ids = list(self.political_entities.keys())
            world_event.related_entity_id = random.choice(state_ids)
            
            # Select a different second state
            second_state_options = [s for s in state_ids if s != world_event.related_entity_id]
            second_state_id = random.choice(second_state_options)
            
            world_event.description = (
                f"A {world_event.name.lower()} has occurred between "
                f"{self.political_entities[world_event.related_entity_id].name} and "
                f"{self.political_entities[second_state_id].name}."
            )
    
    def apply_world_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of a world event"""
        if world_event.type == "Political":
            self.apply_political_event_effects(world_event)
        elif world_event.type == "Natural":
            self.apply_natural_event_effects(world_event)
        elif world_event.type == "Cultural":
            self.apply_cultural_event_effects(world_event)
        elif world_event.type == "Economic":
            self.apply_economic_event_effects(world_event)
        elif world_event.type == "Military":
            self.apply_military_event_effects(world_event)
    
    def apply_political_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of a political event"""
        if world_event.related_entity_id and world_event.related_entity_id in self.political_entities:
            entity = self.political_entities[world_event.related_entity_id]
            
            if world_event.name == "Succession Crisis":
                entity.stability = max(0.1, entity.stability - 0.2)
            elif world_event.name == "New Ruler Crowned":
                entity.stability = min(1.0, entity.stability + 0.1)
            elif world_event.name == "Government Change":
                entity.government = self.generate_random_government()
                entity.stability = max(0.1, entity.stability - 0.1)
    
    def apply_natural_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of a natural event"""
        if world_event.related_region_id and world_event.related_region_id in self.regions:
            region = self.regions[world_event.related_region_id]
            
            # Find all locations in this region and apply effects
            for location in self.locations.values():
                # This is a simplification as we're not actually tracking which regions contain which locations
                # In a full implementation, we'd have proper region-location relationships
                
                # Let's assume a 25% chance the location is affected by the regional event
                if random.randint(0, 100) < 25:
                    if world_event.name in ["Earthquake", "Flood", "Wildfire"]:
                        location.prosperity = max(0.1, location.prosperity - 0.2)
                    elif world_event.name == "Drought":
                        location.prosperity = max(0.1, location.prosperity - 0.15)
                    elif world_event.name == "Bountiful Harvest":
                        location.prosperity = min(1.0, location.prosperity + 0.15)
                    elif world_event.name == "Disease Outbreak":
                        location.population = int(location.population * 0.9)  # 10% population loss
    
    def apply_cultural_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of a cultural event"""
        if world_event.related_location_id and world_event.related_location_id in self.locations:
            location = self.locations[world_event.related_location_id]
            
            if world_event.name in ["Festival", "Artistic Renaissance"]:
                location.prosperity = min(1.0, location.prosperity + 0.1)
                # Add a temporary point of interest
                location.points_of_interest.append("Festival Grounds (Temporary)")
            elif world_event.name == "Religious Revival":
                # Add a new temple
                location.points_of_interest.append(f"New Temple of {self.generate_random_deity_name()} (Temple)")
    
    def apply_economic_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of an economic event"""
        if world_event.related_location_id and world_event.related_location_id in self.locations:
            location = self.locations[world_event.related_location_id]
            
            if world_event.name == "Economic Boom":
                location.prosperity = min(1.0, location.prosperity + 0.2)
                location.population = int(location.population * 1.05)  # 5% population growth
            elif world_event.name == "Market Crash":
                location.prosperity = max(0.1, location.prosperity - 0.2)
            elif world_event.name == "Resource Discovery":
                location.prosperity = min(1.0, location.prosperity + 0.15)
                # Add a new point of interest
                location.points_of_interest.append("New Resource Site (Economic)")
            elif world_event.name == "Guild Formation":
                # Add a new guild hall
                location.points_of_interest.append("New Guild Hall (Guild)")
    
    def apply_military_event_effects(self, world_event: MapWorldEvent):
        """Apply effects of a military event"""
        if world_event.related_entity_id and world_event.related_entity_id in self.political_entities:
            entity = self.political_entities[world_event.related_entity_id]
            
            if world_event.name == "Border Skirmish":
                entity.stability = max(0.1, entity.stability - 0.1)
            elif world_event.name == "Fortification Construction":
                entity.stability = min(1.0, entity.stability + 0.1)
                
                # Add fortifications to a border settlement
                for location in self.locations.values():
                    if location.state_id == world_event.related_entity_id:
                        # Add fortification to a location
                        location.points_of_interest.append("New Fortifications (Military)")
                        break  # Just add to one location
            elif world_event.name in ["Monster Incursion", "Bandit Activity"]:
                entity.stability = max(0.1, entity.stability - 0.15)
                
                # Reduce prosperity in affected locations
                for location in self.locations.values():
                    if location.state_id == world_event.related_entity_id and random.randint(0, 100) < 30:
                        location.prosperity = max(0.1, location.prosperity - 0.1)