import os
import json
import math
import random
from typing import Dict, List, Set, Tuple, Optional, Any

# Import the MapWorldState module
from MapWorldState import MapWorldState


class BiomeData:
    """Represents a biome in the map"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: str = ""
        self.color: str = ""
        self.icon_set: str = ""
        self.cell_ids: Set[int] = set()


class HeightmapData:
    """Represents height data for a cell in the map"""

    def __init__(self):
        self.cell_id: int = 0
        self.height_value: float = 0.0
        self.terrain_type: str = ""


class RiverData:
    """Represents a river in the map"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: str = ""
        self.width: float = 0.0
        self.cells: List[int] = []


class RegionResource:
    """Represents a resource available in a region"""

    def __init__(self):
        self.name: str = ""
        self.abundance: float = 0.0  # 0.0-1.0 scale
        self.value: float = 0.0  # 0.0-1.0 scale
        self.is_rare: bool = False


class RegionAnalysis:
    """Contains analysis data for a region"""

    def __init__(self):
        self.region_id: str = ""
        self.resources: List[RegionResource] = []
        self.contains_water: bool = False
        self.contains_mountains: bool = False
        self.danger_level: float = 0.0  # 0.0-1.0 scale


class TravelTimeEstimate:
    """Contains travel time estimation data"""

    def __init__(self):
        self.is_valid: bool = False
        self.total_distance_km: float = 0.0
        self.travel_time_hours: float = 0.0
        self.travel_time_days: float = 0.0
        self.terrain_types_crossed: List[str] = []
        self.obstacles_crossed: List[str] = []
        self.has_river_crossing: bool = False
        self.has_mountain_crossing: bool = False
        self.has_sea_crossing: bool = False

    def __str__(self):
        if not self.is_valid:
            return "Invalid travel estimate"

        result = f"Distance: {self.total_distance_km:.1f} km, Time: "

        if self.travel_time_days >= 1:
            result += f"{self.travel_time_days:.1f} days"
        else:
            result += f"{self.travel_time_hours:.1f} hours"

        terrains = ", ".join(self.terrain_types_crossed)
        obstacles = "river crossings" if self.has_river_crossing else ""

        if self.has_mountain_crossing:
            if obstacles:
                obstacles += ", "
            obstacles += "mountain passes"

        if self.has_sea_crossing:
            if obstacles:
                obstacles += ", "
            obstacles += "sea crossing"

        if terrains:
            result += f"\nTerrain: {terrains}"

        if obstacles:
            result += f"\nObstacles: {obstacles}"

        return result


class GridPosition:
    """Represents a position in the grid"""

    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y

    def __eq__(self, other):
        if not isinstance(other, GridPosition):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class GridCell:
    """Represents a cell in the grid"""

    def __init__(self):
        self.terrain_type: str = "unknown"
        self.movement_cost: float = 1.0
        self.is_passable: bool = True


class PathNode:
    """Represents a node in the A* pathfinding algorithm"""

    def __init__(self, position: GridPosition):
        self.position: GridPosition = position
        self.g_cost: float = float('inf')  # Cost from start
        self.h_cost: float = 0.0  # Heuristic cost to goal
        self.parent: Optional['PathNode'] = None

    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost


class MapGrid:
    """Represents a grid of the map for pathfinding and terrain analysis"""

    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        self.cells: List[List[GridCell]] = []

        # Initialize cells
        for y in range(height):
            row = []
            for x in range(width):
                row.append(GridCell())
            self.cells.append(row)

    def is_in_bounds(self, x: int, y: int) -> bool:
        """Check if a position is within the grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height

    def set_cell(self, x: int, y: int, terrain_type: str, movement_cost: float):
        """Set the properties of a cell in the grid"""
        if not self.is_in_bounds(x, y):
            return

        self.cells[y][x].terrain_type = terrain_type
        self.cells[y][x].movement_cost = movement_cost
        self.cells[y][x].is_passable = terrain_type not in ["ocean", "sea", "mountain"]

    def get_cell(self, x: int, y: int) -> Optional[GridCell]:
        """Get a cell from the grid"""
        if not self.is_in_bounds(x, y):
            return None

        return self.cells[y][x]

    def find_path(self, start: GridPosition, end: GridPosition) -> List[GridPosition]:
        """Find a path between two points using A* pathfinding"""
        # Check if start or end is out of bounds
        if not self.is_in_bounds(start.x, start.y) or not self.is_in_bounds(end.x, end.y):
            return []

        # Check if end is not passable
        if not self.cells[end.y][end.x].is_passable:
            # Try to find nearest passable cell
            nearest_passable = self.find_nearest_passable_cell(end)
            if nearest_passable.x == -1:
                return []  # No passable cell found

            end = nearest_passable

        # Check if start is not passable
        if not self.cells[start.y][start.x].is_passable:
            # Try to find nearest passable cell
            nearest_passable = self.find_nearest_passable_cell(start)
            if nearest_passable.x == -1:
                return []  # No passable cell found

            start = nearest_passable

        # Initialize open and closed lists
        open_list: List[PathNode] = []
        closed_set: Set[GridPosition] = set()
        all_nodes: Dict[GridPosition, PathNode] = {}

        # Add start node to open list
        start_node = PathNode(start)
        start_node.g_cost = 0
        start_node.h_cost = self.calculate_heuristic(start, end)
        open_list.append(start_node)
        all_nodes[start] = start_node

        while open_list:
            # Get node with lowest F cost
            current_node = open_list[0]
            for i in range(1, len(open_list)):
                if (open_list[i].f_cost < current_node.f_cost or
                        (open_list[i].f_cost == current_node.f_cost and
                         open_list[i].h_cost < current_node.h_cost)):
                    current_node = open_list[i]

            # Remove current node from open list and add to closed list
            open_list.remove(current_node)
            closed_set.add(current_node.position)

            # Check if we reached the end
            if current_node.position.x == end.x and current_node.position.y == end.y:
                # Reconstruct path
                return self.reconstruct_path(current_node)

            # Check neighbors
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    # Skip current node
                    if dx == 0 and dy == 0:
                        continue

                    # Calculate neighbor position
                    nx = current_node.position.x + dx
                    ny = current_node.position.y + dy

                    # Check bounds
                    if not self.is_in_bounds(nx, ny):
                        continue

                    # Check if neighbor is in closed list
                    neighbor_pos = GridPosition(nx, ny)
                    if neighbor_pos in closed_set:
                        continue

                    # Check if neighbor is passable
                    if not self.cells[ny][nx].is_passable:
                        continue

                    # Calculate cost to neighbor
                    movement_cost = self.cells[ny][nx].movement_cost

                    # Diagonal movement costs more
                    if dx != 0 and dy != 0:
                        movement_cost *= 1.414  # Sqrt(2)

                    g_cost = current_node.g_cost + movement_cost

                    # Get or create neighbor node
                    if neighbor_pos in all_nodes:
                        neighbor_node = all_nodes[neighbor_pos]
                        # Skip if path to neighbor is not better
                        if g_cost >= neighbor_node.g_cost:
                            continue
                    else:
                        # Create new node
                        neighbor_node = PathNode(neighbor_pos)
                        all_nodes[neighbor_pos] = neighbor_node

                    # Update neighbor node
                    neighbor_node.g_cost = g_cost
                    neighbor_node.h_cost = self.calculate_heuristic(neighbor_pos, end)
                    neighbor_node.parent = current_node

                    # Add to open list if not already in it
                    if neighbor_node not in open_list:
                        open_list.append(neighbor_node)

        # No path found
        return []

    def find_nearest_passable_cell(self, position: GridPosition) -> GridPosition:
        """Find the nearest passable cell to a given position"""
        # Search in expanding squares around the position
        for radius in range(1, 11):
            # Check perimeter of square
            for y in range(position.y - radius, position.y + radius + 1):
                for x in range(position.x - radius, position.x + radius + 1):
                    # Only check perimeter
                    if (x == position.x - radius or x == position.x + radius or
                            y == position.y - radius or y == position.y + radius):
                        # Check bounds
                        if self.is_in_bounds(x, y) and self.cells[y][x].is_passable:
                            return GridPosition(x, y)

        # No passable cell found
        return GridPosition(-1, -1)

    def calculate_heuristic(self, from_pos: GridPosition, to_pos: GridPosition) -> float:
        """Calculate heuristic (estimated cost) from a position to the goal"""
        # Manhattan distance
        return abs(from_pos.x - to_pos.x) + abs(from_pos.y - to_pos.y)

    def reconstruct_path(self, end_node: PathNode) -> List[GridPosition]:
        """Reconstruct path from end node to start node"""
        path: List[GridPosition] = []
        current_node = end_node

        # Traverse from end to start
        while current_node:
            path.append(current_node.position)
            current_node = current_node.parent

        # Reverse to get path from start to end
        path.reverse()

        return path


class MapRegionManager:
    """
    Manages geographical regions, biomes, and terrain types from Azgaar's map data.
    Provides interfaces for querying region data and handling geographical features.
    """

    # Singleton instance
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MapRegionManager()
        return cls._instance

    def __init__(self):
        # References to other managers
        self.world_state = None

        # Region data
        self.biomes: Dict[str, BiomeData] = {}
        self.heightmap: Dict[str, HeightmapData] = {}
        self.rivers: Dict[str, RiverData] = {}

        # Geography settings
        self.danger_level_threshold: float = 0.7
        self.resource_density_multiplier: float = 1.0

        # Cached region analysis
        self.region_analyses: Dict[str, RegionAnalysis] = {}

        # Map grid data for pathfinding and terrain analysis
        self.map_grid: Optional[MapGrid] = None

        # Terrain difficulty multipliers by type
        self.terrain_difficulty_multipliers: Dict[str, float] = {
            "water": 2.5,
            "sea": 5.0,
            "ocean": 10.0,
            "mountain": 2.0,
            "hill": 1.5,
            "highland": 1.3,
            "wetland": 1.8,
            "desert": 1.7,
            "forest": 1.4,
            "plain": 1.0,
            "grassland": 1.0
        }

        print("MapRegionManager initialized")

    def initialize(self):
        """Initialize the region manager with map data"""
        try:
            # Get reference to world state
            self.world_state = MapWorldState.instance()

            # Load biome data from map
            self.load_biomes_from_map()

            # Load heightmap data from map
            self.load_heightmap_from_map()

            # Load river data from map
            self.load_rivers_from_map()

            # Generate the map grid for terrain analysis
            self.generate_map_grid()

            print("MapRegionManager initialization complete")
        except Exception as ex:
            print(f"Error initializing MapRegionManager: {str(ex)}")

    def load_biomes_from_map(self):
        """Load biome data from the map"""
        try:
            self.biomes.clear()

            map_data = self.world_state.map_data
            if not map_data:
                print("Map data not available")
                return

            # Load biomes
            biomes_token = map_data.get("biomes", [])
            if biomes_token:
                for biome in biomes_token:
                    biome_id = str(biome.get("i", ""))
                    if not biome_id:
                        continue

                    biome_data = BiomeData()
                    biome_data.id = biome_id
                    biome_data.name = biome.get("name", "Unknown Biome")
                    biome_data.type = biome.get("type", "unknown")
                    biome_data.color = biome.get("color", "#000000")
                    biome_data.icon_set = biome.get("iconSet", "default")
                    biome_data.cell_ids = set()

                    # Parse cells that belong to this biome
                    cells_token = biome.get("cells", [])
                    if cells_token:
                        for cell_token in cells_token:
                            try:
                                cell_id = int(cell_token)
                                biome_data.cell_ids.add(cell_id)
                            except ValueError:
                                continue

                    self.biomes[biome_id] = biome_data

                print(f"Loaded {len(self.biomes)} biomes from map data")
            else:
                print("No biomes found in map data")
        except Exception as ex:
            print(f"Error loading biomes: {str(ex)}")

    def load_heightmap_from_map(self):
        """Load heightmap data from the map"""
        try:
            self.heightmap.clear()

            map_data = self.world_state.map_data
            if not map_data:
                print("Map data not available")
                return

            # Load heightmap data
            heights_token = map_data.get("heights", [])
            if heights_token:
                for i, height_token in enumerate(heights_token):
                    if height_token is None:
                        continue

                    # Parse height values
                    try:
                        height_value = float(height_token)

                        height_data = HeightmapData()
                        height_data.cell_id = i
                        height_data.height_value = height_value
                        height_data.terrain_type = self.get_terrain_type_from_height(height_value)

                        self.heightmap[str(i)] = height_data
                    except ValueError:
                        continue

                print(f"Loaded {len(self.heightmap)} heightmap points from map data")
            else:
                print("No heightmap found in map data")
        except Exception as ex:
            print(f"Error loading heightmap: {str(ex)}")

    def load_rivers_from_map(self):
        """Load river data from the map"""
        try:
            self.rivers.clear()

            map_data = self.world_state.map_data
            if not map_data:
                print("Map data not available")
                return

            # Load rivers data
            rivers_token = map_data.get("rivers", [])
            if rivers_token:
                for river in rivers_token:
                    river_id = str(river.get("i", ""))
                    if not river_id:
                        continue

                    river_data = RiverData()
                    river_data.id = river_id
                    river_data.name = river.get("name", "Unnamed River")
                    river_data.type = river.get("type", "river")

                    try:
                        river_data.width = float(river.get("width", 1.0))
                    except ValueError:
                        river_data.width = 1.0

                    river_data.cells = []

                    # Parse cells that the river flows through
                    cells_token = river.get("cells", [])
                    if cells_token:
                        for cell_token in cells_token:
                            try:
                                cell_id = int(cell_token)
                                river_data.cells.append(cell_id)
                            except ValueError:
                                continue

                    self.rivers[river_id] = river_data

                print(f"Loaded {len(self.rivers)} rivers from map data")
            else:
                print("No rivers found in map data")
        except Exception as ex:
            print(f"Error loading rivers: {str(ex)}")

    def generate_map_grid(self):
        """Generate a grid representation of the map for terrain analysis and pathfinding"""
        try:
            map_data = self.world_state.map_data
            if not map_data:
                print("Map data not available")
                return

            # Get grid size from map data
            width = int(map_data.get("info", {}).get("width", 1000))
            height = int(map_data.get("info", {}).get("height", 1000))

            # Create grid
            self.map_grid = MapGrid(width, height)

            # Populate grid with terrain data
            for height_key, height_data in self.heightmap.items():
                cell_id = height_data.cell_id

                # Convert cell ID to grid position
                # Note: This is a simplified conversion that doesn't match Azgaar's exact cell system
                # In a full implementation, we would need to use the actual cell coordinates from the map
                x = cell_id % width
                y = cell_id // width

                if x < 0 or x >= width or y < 0 or y >= height:
                    continue

                # Set grid cell terrain type and movement cost
                terrain_type = height_data.terrain_type
                movement_cost = self.get_movement_cost_for_terrain(terrain_type)

                self.map_grid.set_cell(x, y, terrain_type, movement_cost)

                # Add river crossings (if any)
                for river in self.rivers.values():
                    if cell_id in river.cells:
                        # Rivers increase movement cost
                        river_cost = movement_cost * self.get_river_crossing_multiplier(
                            river.type, river.width)
                        self.map_grid.set_cell(x, y, f"{terrain_type}+river", river_cost)
                        break

            print(f"Generated map grid of size {width}x{height}")
        except Exception as ex:
            print(f"Error generating map grid: {str(ex)}")

    def get_terrain_type_from_height(self, height: float) -> str:
        """Get the terrain type from a height value"""
        # Convert height value to terrain type
        # Thresholds based on Azgaar's map generator conventions
        if height < 0.2:
            return "ocean"
        elif height < 0.25:
            return "sea"
        elif height < 0.3:
            return "water"
        elif height < 0.4:
            return "plain"
        elif height < 0.5:
            return "grassland"
        elif height < 0.65:
            return "hill"
        elif height < 0.8:
            return "highland"
        else:
            return "mountain"

    def get_movement_cost_for_terrain(self, terrain_type: str) -> float:
        """Calculate the movement cost for a terrain type"""
        # Get movement cost multiplier for this terrain type
        if terrain_type in self.terrain_difficulty_multipliers:
            return self.terrain_difficulty_multipliers[terrain_type]

        # Default multiplier for unknown terrain
        return 1.5

    def get_river_crossing_multiplier(self, river_type: str, river_width: float) -> float:
        """Calculate the movement cost multiplier for crossing a river"""
        river_type = river_type.lower()

        if river_type == "brook":
            return 1.2
        elif river_type == "stream":
            return 1.5
        elif river_type == "river":
            return 2.0 + (river_width * 0.2)  # Wider rivers are harder to cross
        elif river_type == "major river":
            return 3.0 + (river_width * 0.3)
        else:
            return 1.5

    def find_path(self, start_x: float, start_y: float, end_x: float, end_y: float) -> List[Tuple[float, float]]:
        """Find a path between two points on the map"""
        if not self.map_grid:
            print("Map grid not initialized")
            return []

        # Convert world coordinates to grid coordinates
        start_grid_x = round(start_x)
        start_grid_y = round(start_y)
        end_grid_x = round(end_x)
        end_grid_y = round(end_y)

        # Check bounds
        if (not self.map_grid.is_in_bounds(start_grid_x, start_grid_y) or
                not self.map_grid.is_in_bounds(end_grid_x, end_grid_y)):
            print("Path start or end is out of bounds")
            return []

        # Perform A* pathfinding
        grid_path = self.map_grid.find_path(
            GridPosition(start_grid_x, start_grid_y),
            GridPosition(end_grid_x, end_grid_y)
        )

        # Convert grid path to world coordinates
        world_path = []
        for grid_pos in grid_path:
            world_path.append((float(grid_pos.x), float(grid_pos.y)))

        return world_path

    def calculate_travel_time(self, start_x: float, start_y: float, end_x: float, end_y: float,
                              travel_speed: float = 1.0) -> TravelTimeEstimate:
        """Calculate the estimated travel time between two points based on terrain"""
        # Find path between points
        path = self.find_path(start_x, start_y, end_x, end_y)

        if not path:
            print("Could not find path for travel time calculation")
            return TravelTimeEstimate()

        # Calculate total distance and adjusted distance (accounting for terrain)
        total_distance = 0.0
        adjusted_distance = 0.0
        last_point = path[0]
        terrain_types_crossed = []
        obstacles_crossed = []

        for i in range(1, len(path)):
            current_point = path[i]
            dx = current_point[0] - last_point[0]
            dy = current_point[1] - last_point[1]
            segment_distance = math.sqrt(dx * dx + dy * dy)
            total_distance += segment_distance

            # Get terrain type and movement cost for this segment
            grid_x = round(current_point[0])
            grid_y = round(current_point[1])
            cell = self.map_grid.get_cell(grid_x, grid_y)

            # Track terrain types crossed
            if cell and cell.terrain_type not in terrain_types_crossed:
                terrain_types_crossed.append(cell.terrain_type)

            # Track obstacles (rivers, mountains, etc.)
            if cell:
                if "river" in cell.terrain_type and "river" not in obstacles_crossed:
                    obstacles_crossed.append("river")
                elif cell.terrain_type == "mountain" and "mountain" not in obstacles_crossed:
                    obstacles_crossed.append("mountain")
                elif cell.terrain_type == "sea" and "sea" not in obstacles_crossed:
                    obstacles_crossed.append("sea")

            # Adjust distance by terrain difficulty
            if cell:
                adjusted_distance += segment_distance * cell.movement_cost
            else:
                adjusted_distance += segment_distance  # Default if cell not found

            last_point = current_point

        # Calculate travel time based on adjusted distance and travel speed
        travel_time_hours = adjusted_distance / travel_speed

        # Create travel time estimate
        estimate = TravelTimeEstimate()
        estimate.is_valid = True
        estimate.total_distance_km = total_distance * 10  # Scale to km (approximation)
        estimate.travel_time_hours = travel_time_hours
        estimate.travel_time_days = travel_time_hours / 8  # Assuming 8 hours of travel per day
        estimate.terrain_types_crossed = terrain_types_crossed
        estimate.obstacles_crossed = obstacles_crossed
        estimate.has_river_crossing = "river" in obstacles_crossed
        estimate.has_mountain_crossing = "mountain" in obstacles_crossed
        estimate.has_sea_crossing = "sea" in obstacles_crossed

        return estimate

    def get_biome_at_position(self, x: float, y: float) -> Optional[BiomeData]:
        """Get the biome at a specific point on the map"""
        # Convert position to cell ID
        # Note: This is a simplified conversion that doesn't match Azgaar's exact cell system
        width = self.map_grid.width if self.map_grid else 1000
        cell_id = round(y) * width + round(x)

        # Find the biome that contains this cell
        for biome in self.biomes.values():
            if cell_id in biome.cell_ids:
                return biome

        # No biome found
        return None

    def get_height_at_position(self, x: float, y: float) -> Optional[HeightmapData]:
        """Get the height data at a specific point on the map"""
        # Convert position to cell ID
        width = self.map_grid.width if self.map_grid else 1000
        cell_id = round(y) * width + round(x)

        # Find the height data for this cell
        if str(cell_id) in self.heightmap:
            return self.heightmap[str(cell_id)]

        # No height data found
        return None

    def is_water(self, x: float, y: float) -> bool:
        """Check if a point is on water (ocean, sea, lake, or river)"""
        # Check heightmap first
        height = self.get_height_at_position(x, y)
        if height:
            if height.terrain_type in ["ocean", "sea", "water"]:
                return True

        # Check for rivers
        width = self.map_grid.width if self.map_grid else 1000
        cell_id = round(y) * width + round(x)

        for river in self.rivers.values():
            if cell_id in river.cells:
                return True

        return False

    def find_nearest_land(self, x: float, y: float) -> Tuple[float, float]:
        """Find the nearest land point to a given position (useful if position is in water)"""
        # If the position is already on land, return it
        if not self.is_water(x, y):
            return (x, y)

        # Grid search for nearest land
        max_search_radius = 20  # Limit search radius
        width = self.map_grid.width if self.map_grid else 1000
        height = self.map_grid.height if self.map_grid else 1000

        center_x = round(x)
        center_y = round(y)

        for radius in range(1, max_search_radius + 1):
            # Search in a square pattern outward
            for y_offset in range(-radius, radius + 1):
                for x_offset in range(-radius, radius + 1):
                    # Only check the perimeter of the square
                    if (x_offset == -radius or x_offset == radius or
                            y_offset == -radius or y_offset == radius):
                        # Check bounds
                        check_x = center_x + x_offset
                        check_y = center_y + y_offset

                        if 0 <= check_x < width and 0 <= check_y < height:
                            if not self.is_water(float(check_x), float(check_y)):
                                return (float(check_x), float(check_y))

        # If no land found, return original position
        print("Could not find nearby land")
        return (x, y)

    def get_all_rivers(self) -> List[RiverData]:
        """Get a list of all rivers"""
        return list(self.rivers.values())

    def get_all_biomes(self) -> List[BiomeData]:
        """Get a list of all biomes"""
        return list(self.biomes.values())

    def get_region_danger_level(self, region_id: str) -> float:
        """Get the danger level for a specific region on the map"""
        # Get or compute region analysis
        analysis = self.get_region_analysis(region_id)
        if analysis:
            return analysis.danger_level

        return 0.5  # Default medium danger level

    def get_region_resources(self, region_id: str) -> List[RegionResource]:
        """Get all available resources in a specific region"""
        # Get or compute region analysis
        analysis = self.get_region_analysis(region_id)
        if analysis:
            return analysis.resources

        return []

    def get_region_analysis(self, region_id: str) -> Optional[RegionAnalysis]:
        """Get the region analysis for a specific region, computing it if necessary"""
        # Return cached analysis if available
        if region_id in self.region_analyses:
            return self.region_analyses[region_id]

        # Find the region
        if region_id in self.biomes:
            # Compute region analysis
            biome = self.biomes[region_id]
            analysis = self.analyze_region(biome)
            self.region_analyses[region_id] = analysis
            return analysis

        return None

    def analyze_region(self, biome: BiomeData) -> RegionAnalysis:
        """Analyze a region to determine its characteristics"""
        analysis = RegionAnalysis()
        analysis.region_id = biome.id
        analysis.resources = []
        analysis.contains_water = False
        analysis.contains_mountains = False
        analysis.danger_level = 0.5  # Default medium danger

        # Examine cells in this region
        for cell_id in biome.cell_ids:
            # Check height/terrain type
            if str(cell_id) in self.heightmap:
                height = self.heightmap[str(cell_id)]

                # Check for mountains
                if height.terrain_type in ["mountain", "highland"]:
                    analysis.contains_mountains = True

                    # Mountains increase danger level
                    analysis.danger_level += 0.05

                # Check for water
                if height.terrain_type in ["water", "sea", "ocean"]:
                    analysis.contains_water = True

            # Check for rivers
            cell_has_river = False
            for river in self.rivers.values():
                if cell_id in river.cells:
                    analysis.contains_water = True
                    cell_has_river = True
                    break

            # Determine resources based on biome type and terrain
            self.determine_region_resources(analysis, biome.type,
                                            height.terrain_type if str(cell_id) in self.heightmap else None,
                                            cell_has_river)

        # Adjust danger level based on biome type
        self.adjust_danger_level_for_biome(analysis, biome.type)

        # Cap danger level between 0.1 and 1.0
        analysis.danger_level = max(0.1, min(analysis.danger_level, 1.0))

        return analysis

    def determine_region_resources(self, analysis: RegionAnalysis, biome_type: str,
                                   terrain_type: Optional[str], has_river: bool):
        """Determine resources available in a region based on biome and terrain"""
        # Check if we've already added resources
        if analysis.resources:
            return

        # Generate resources based on biome type
        biome_type = biome_type.lower()

        if "tropical" in biome_type:
            self.add_resource_if_not_present(analysis, "Exotic Wood", 0.8)
            self.add_resource_if_not_present(analysis, "Tropical Fruits", 0.9)
            self.add_resource_if_not_present(analysis, "Spices", 0.7)
        elif "forest" in biome_type and ("temperate" in biome_type or "rainforest" in biome_type):
            self.add_resource_if_not_present(analysis, "Timber", 0.9)
            self.add_resource_if_not_present(analysis, "Wild Game", 0.8)
            self.add_resource_if_not_present(analysis, "Medicinal Herbs", 0.6)
        elif "savanna" in biome_type or "grassland" in biome_type:
            self.add_resource_if_not_present(analysis, "Livestock", 0.9)
            self.add_resource_if_not_present(analysis, "Grain", 0.8)
            self.add_resource_if_not_present(analysis, "Wild Game", 0.7)
        elif "desert" in biome_type:
            self.add_resource_if_not_present(analysis, "Salt", 0.7)
            self.add_resource_if_not_present(analysis, "Gems", 0.4)
            self.add_resource_if_not_present(analysis, "Gold", 0.3)
        elif "taiga" in biome_type:
            self.add_resource_if_not_present(analysis, "Furs", 0.8)
            self.add_resource_if_not_present(analysis, "Timber", 0.7)
            self.add_resource_if_not_present(analysis, "Wild Game", 0.6)
        elif "tundra" in biome_type:
            self.add_resource_if_not_present(analysis, "Furs", 0.7)
            self.add_resource_if_not_present(analysis, "Wild Game", 0.5)
        elif "wetland" in biome_type:
            self.add_resource_if_not_present(analysis, "Fish", 0.9)
            self.add_resource_if_not_present(analysis, "Reeds", 0.8)
            self.add_resource_if_not_present(analysis, "Clay", 0.7)
        else:
            # Default resources based on terrain
            if terrain_type == "mountain":
                self.add_resource_if_not_present(analysis, "Iron", 0.7)
                self.add_resource_if_not_present(analysis, "Stone", 0.9)
            elif terrain_type == "forest":
                self.add_resource_if_not_present(analysis, "Timber", 0.8)
                self.add_resource_if_not_present(analysis, "Wild Game", 0.7)
            elif terrain_type in ["grassland", "plain"]:
                self.add_resource_if_not_present(analysis, "Grain", 0.8)
                self.add_resource_if_not_present(analysis, "Livestock", 0.7)

        # Add river-based resources
        if has_river or analysis.contains_water:
            self.add_resource_if_not_present(analysis, "Fish", 0.8)
            self.add_resource_if_not_present(analysis, "Fresh Water", 1.0)

        # Add mountain-based resources
        if analysis.contains_mountains or terrain_type in ["mountain", "highland"]:
            self.add_resource_if_not_present(analysis, "Stone", 0.9)
            self.add_resource_if_not_present(analysis, "Iron", 0.6)
            self.add_resource_if_not_present(analysis, "Copper", 0.5)

            # Small chance for precious resources
            if random.random() < 0.3:
                self.add_resource_if_not_present(analysis, "Silver", 0.4)

            if random.random() < 0.2:
                self.add_resource_if_not_present(analysis, "Gold", 0.3)

            if random.random() < 0.1:
                self.add_resource_if_not_present(analysis, "Gems", 0.2)

    def add_resource_if_not_present(self, analysis: RegionAnalysis, resource_name: str, abundance: float):
        """Add a resource to the region analysis if not already present"""
        # Check if resource already exists
        for resource in analysis.resources:
            if resource.name == resource_name:
                return

        # Apply resource density multiplier
        abundance *= self.resource_density_multiplier

        # Randomize abundance slightly
        abundance *= random.uniform(0.8, 1.2)

        # Add resource to analysis
        resource = RegionResource()
        resource.name = resource_name
        resource.abundance = abundance
        resource.value = self.determine_resource_value(resource_name)
        resource.is_rare = abundance < 0.5

        analysis.resources.append(resource)

    def determine_resource_value(self, resource_name: str) -> float:
        """Determine the relative value of a resource"""
        # Resource value table (0.0-1.0 scale)
        resource_values = {
            "Fish": 0.5,
            "Fresh Water": 0.4,
            "Timber": 0.5,
            "Wild Game": 0.6,
            "Medicinal Herbs": 0.7,
            "Spices": 0.8,
            "Exotic Wood": 0.7,
            "Tropical Fruits": 0.6,
            "Livestock": 0.5,
            "Grain": 0.4,
            "Salt": 0.6,
            "Stone": 0.3,
            "Clay": 0.4,
            "Reeds": 0.3,
            "Furs": 0.6,
            "Iron": 0.7,
            "Copper": 0.6,
            "Silver": 0.8,
            "Gold": 0.9,
            "Gems": 1.0
        }

        # Return value if found, otherwise medium value
        return resource_values.get(resource_name, 0.5)

    def adjust_danger_level_for_biome(self, analysis: RegionAnalysis, biome_type: str):
        """Adjust danger level based on biome type"""
        # Base danger adjustment by biome
        biome_type = biome_type.lower()

        if "tundra" in biome_type or "glacier" in biome_type:
            analysis.danger_level += 0.2
        elif "desert" in biome_type:
            analysis.danger_level += 0.15
        elif "wetland" in biome_type:
            analysis.danger_level += 0.1
        elif "tropical" in biome_type or "savanna" in biome_type or "taiga" in biome_type:
            analysis.danger_level += 0.05
        elif "grassland" in biome_type:
            analysis.danger_level -= 0.05
        # No change for temperate forests

        # Additional factors
        if analysis.contains_mountains:
            analysis.danger_level += 0.1

        if analysis.contains_water:
            analysis.danger_level -= 0.05  # Water generally makes areas less dangerous (access to resources)

    def find_settlement_locations(self, count: int = 5) -> List[Tuple[float, float]]:
        """Find suitable locations for a settlement based on terrain and resources"""
        locations = []

        if not self.map_grid:
            print("Map grid not initialized")
            return locations

        # Criteria for good settlement location:
        # 1. Near water (river or lake)
        # 2. Not in mountains or ocean
        # 3. Access to resources
        # 4. Not too close to other settlements

        # Score all potential locations
        location_scores = {}

        # Sample grid at lower resolution for performance
        step_size = max(1, self.map_grid.width // 100)

        for y in range(0, self.map_grid.height, step_size):
            for x in range(0, self.map_grid.width, step_size):
                # Skip water and mountains
                if self.is_water(float(x), float(y)):
                    continue

                height = self.get_height_at_position(float(x), float(y))
                if height and height.terrain_type == "mountain":
                    continue

                # Calculate score for this location
                score = 0.0

                # Prefer locations near water (rivers or lakes)
                near_water = False
                water_search_radius = 5

                for dy in range(-water_search_radius, water_search_radius + 1):
                    for dx in range(-water_search_radius, water_search_radius + 1):
                        nx = x + dx
                        ny = y + dy

                        if 0 <= nx < self.map_grid.width and 0 <= ny < self.map_grid.height:
                            if self.is_water(float(nx), float(ny)):
                                near_water = True
                                # Closer water is better
                                distance = math.sqrt(dx * dx + dy * dy)
                                score += 10 * (1.0 - distance / water_search_radius)
                                break

                    if near_water:
                        break

                if not near_water:
                    continue  # Skip locations not near water

                # Check biome resources
                biome = self.get_biome_at_position(float(x), float(y))
                if biome:
                    analysis = self.get_region_analysis(biome.id)
                    if analysis:
                        # Add points for resources
                        for resource in analysis.resources:
                            score += resource.value * resource.abundance * 5

                        # Subtract points for danger
                        score -= analysis.danger_level * 10

                # Prefer flatter terrain (plains, grasslands)
                if height:
                    if height.terrain_type in ["plain", "grassland"]:
                        score += 5
                    elif height.terrain_type == "hill":
                        score += 2

                # Store score for this location
                location_scores[(float(x), float(y))] = score

        # Get top scoring locations
        sorted_locations = sorted(location_scores.items(), key=lambda x: x[1], reverse=True)
        top_locations = sorted_locations[:count * 2]

        # Filter to ensure locations aren't too close to each other
        min_distance_between_locations = max(10, self.map_grid.width / 20)

        for loc, score in top_locations:
            # Check if this location is far enough from already selected locations
            too_close = False
            for selected_loc in locations:
                dx = loc[0] - selected_loc[0]
                dy = loc[1] - selected_loc[1]
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < min_distance_between_locations:
                    too_close = True
                    break

            if not too_close:
                locations.append(loc)

                if len(locations) >= count:
                    break

        return locations