# EncounterEngine/EnvironmentManager.py
import random
from typing import Dict, List, Any, Optional


class EnvironmentManager:
    """Manages environmental features, hazards, and conditions for encounters."""

    def __init__(self):
        """Initialize the environment manager."""
        # Define environment types
        self.environment_types = [
            "forest", "mountain", "dungeon", "urban", "coastal",
            "desert", "grassland", "arctic", "underdark", "swamp"
        ]

        # Environment features by type
        self.environment_features = {
            "forest": [
                "Dense Foliage", "Fallen Trees", "Tree Canopy", "Forest Clearing",
                "Brambles", "Thick Undergrowth", "Animal Trails", "Mushroom Circle"
            ],
            "mountain": [
                "Rocky Terrain", "Steep Slopes", "Narrow Ledges", "Boulder Field",
                "Mountain Pass", "Cliff Face", "Cave Entrance", "Snowcapped Peak"
            ],
            "dungeon": [
                "Narrow Corridors", "Trapped Floor", "Secret Doors", "Prison Cells",
                "Collapsed Passage", "Underground River", "Ancient Statues", "Mysterious Altar"
            ],
            "urban": [
                "Marketplace", "Alleyways", "Rooftops", "Sewers",
                "Town Square", "Guard Post", "Noble District", "Slums"
            ],
            "coastal": [
                "Sandy Beach", "Rocky Shore", "Tide Pools", "Sea Cave",
                "Coastal Cliffs", "Shipwreck", "Fishing Village", "Lighthouse"
            ],
            "desert": [
                "Sand Dunes", "Oasis", "Ancient Ruins", "Rocky Outcroppings",
                "Quicksand", "Mirage", "Desert Caravan", "Sandstorm"
            ],
            "grassland": [
                "Rolling Hills", "Tall Grass", "Scattered Trees", "Grazing Herds",
                "River Crossing", "Farmland", "Tribal Camp", "Burial Mounds"
            ],
            "arctic": [
                "Snowfield", "Frozen Lake", "Ice Cave", "Glacier",
                "Hot Springs", "Frozen Waterfall", "Blizzard", "Northern Lights"
            ],
            "underdark": [
                "Fungal Forest", "Underground Lake", "Bioluminescent Cavern", "Narrow Tunnels",
                "Stalactites/Stalagmites", "Drow Outpost", "Ancient Dwarven Ruins", "Crystal Cave"
            ],
            "swamp": [
                "Bog", "Quicksand", "Murky Water", "Twisted Trees",
                "Floating Vegetation", "Ancient Ruins", "Witch's Hut", "Giant Mushrooms"
            ]
        }

        # Environment hazards by type
        self.environment_hazards = {
            "forest": [
                {"name": "Falling Branch", "type": "trap", "damage": "1d6", "dc": 12},
                {"name": "Poisonous Plants", "type": "poison", "damage": "1d4", "dc": 10},
                {"name": "Wildlife Trap", "type": "trap", "damage": "1d8", "dc": 14},
                {"name": "Dangerous Wildlife", "type": "encounter", "damage": "0", "dc": 0}
            ],
            "mountain": [
                {"name": "Rockslide", "type": "trap", "damage": "2d6", "dc": 15},
                {"name": "Thin Air", "type": "exhaustion", "damage": "0", "dc": 12},
                {"name": "Unstable Ground", "type": "trap", "damage": "1d6", "dc": 12},
                {"name": "Freezing Wind", "type": "weather", "damage": "1d4", "dc": 10}
            ],
            "dungeon": [
                {"name": "Pit Trap", "type": "trap", "damage": "2d6", "dc": 15},
                {"name": "Poison Dart Trap", "type": "trap", "damage": "1d4", "dc": 15},
                {"name": "Cave In", "type": "trap", "damage": "3d6", "dc": 15},
                {"name": "Gas Leak", "type": "poison", "damage": "1d6", "dc": 12}
            ],
            "urban": [
                {"name": "Collapsing Roof", "type": "trap", "damage": "2d6", "dc": 15},
                {"name": "Street Thugs", "type": "encounter", "damage": "0", "dc": 0},
                {"name": "Pickpocket", "type": "social", "damage": "0", "dc": 15},
                {"name": "Fire", "type": "hazard", "damage": "1d6", "dc": 12}
            ],
            "coastal": [
                {"name": "High Tide", "type": "hazard", "damage": "1d6", "dc": 12},
                {"name": "Undertow", "type": "hazard", "damage": "1d6", "dc": 15},
                {"name": "Slippery Rocks", "type": "trap", "damage": "1d4", "dc": 12},
                {"name": "Shark Encounter", "type": "encounter", "damage": "0", "dc": 0}
            ],
            "desert": [
                {"name": "Heat Exhaustion", "type": "exhaustion", "damage": "1d4", "dc": 15},
                {"name": "Quicksand", "type": "trap", "damage": "1d4", "dc": 15},
                {"name": "Sandstorm", "type": "weather", "damage": "1d6", "dc": 15},
                {"name": "Dehydration", "type": "exhaustion", "damage": "1d6", "dc": 15}
            ],
            "grassland": [
                {"name": "Wildfire", "type": "hazard", "damage": "2d6", "dc": 15},
                {"name": "Hidden Burrow", "type": "trap", "damage": "1d4", "dc": 12},
                {"name": "Lightning Storm", "type": "weather", "damage": "3d6", "dc": 15},
                {"name": "Stampede", "type": "encounter", "damage": "2d8", "dc": 15}
            ],
            "arctic": [
                {"name": "Thin Ice", "type": "trap", "damage": "1d6", "dc": 15},
                {"name": "Frostbite", "type": "exhaustion", "damage": "1d6", "dc": 15},
                {"name": "Blizzard", "type": "weather", "damage": "1d8", "dc": 15},
                {"name": "Avalanche", "type": "hazard", "damage": "3d6", "dc": 18}
            ],
            "underdark": [
                {"name": "Toxic Spores", "type": "poison", "damage": "1d8", "dc": 15},
                {"name": "Unstable Ceiling", "type": "trap", "damage": "2d6", "dc": 15},
                {"name": "Underground River", "type": "hazard", "damage": "1d6", "dc": 15},
                {"name": "Drow Patrol", "type": "encounter", "damage": "0", "dc": 0}
            ],
            "swamp": [
                {"name": "Quicksand", "type": "trap", "damage": "1d4", "dc": 15},
                {"name": "Disease Cloud", "type": "poison", "damage": "1d4", "dc": 12},
                {"name": "Venomous Snake", "type": "encounter", "damage": "1d4", "dc": 12},
                {"name": "Dangerous Plants", "type": "trap", "damage": "1d8", "dc": 15}
            ]
        }

        # Weather conditions by environment
        self.weather_conditions = {
            "forest": ["Clear", "Rain", "Fog", "Thunderstorm"],
            "mountain": ["Clear", "Snow", "Fog", "Hail", "High Winds"],
            "dungeon": ["Stale Air", "Humid", "Dry", "Drafty"],
            "urban": ["Clear", "Rain", "Fog", "Snow"],
            "coastal": ["Clear", "Rain", "Fog", "Storm", "High Winds"],
            "desert": ["Clear", "Sandstorm", "Hot", "Dust Devil"],
            "grassland": ["Clear", "Rain", "Fog", "Thunderstorm"],
            "arctic": ["Clear", "Blizzard", "Snow", "Freezing Fog"],
            "underdark": ["Stale Air", "Humid", "Spore Cloud", "Steam Vents"],
            "swamp": ["Humid", "Rain", "Fog", "Thunderstorm"]
        }

        # Time of day options
        self.time_options = ["Dawn", "Morning", "Noon", "Afternoon", "Dusk", "Evening", "Night", "Midnight"]

    def generate_environment(self, environment_type, complexity=2, hazard_level=1):
        """
        Generate a detailed environment for an encounter.

        Args:
            environment_type: Type of environment
            complexity: Number of features to include (1-5)
            hazard_level: Level of environmental hazards (0-3)

        Returns:
            Dictionary with environment details
        """
        # Validate environment type
        if environment_type not in self.environment_types:
            environment_type = random.choice(self.environment_types)

        # Limit complexity and hazard_level to valid ranges
        complexity = max(1, min(5, complexity))
        hazard_level = max(0, min(3, hazard_level))

        # Select random features
        available_features = self.environment_features.get(environment_type, [])
        features = random.sample(available_features, min(complexity, len(available_features)))

        # Select random hazards based on hazard level
        hazards = []
        available_hazards = self.environment_hazards.get(environment_type, [])

        if hazard_level > 0 and available_hazards:
            num_hazards = hazard_level
            hazards = random.sample(available_hazards, min(num_hazards, len(available_hazards)))

        # Select weather condition
        available_weather = self.weather_conditions.get(environment_type, ["Clear"])
        weather = random.choice(available_weather)

        # Select time of day
        time_of_day = random.choice(self.time_options)

        # Determine lighting conditions based on time of day and weather
        lighting = self._determine_lighting(time_of_day, weather, environment_type)

        # Generate environment description
        description = self._generate_environment_description(
            environment_type, features, weather, time_of_day, lighting
        )

        return {
            "type": environment_type,
            "features": features,
            "hazards": hazards,
            "weather": weather,
            "time_of_day": time_of_day,
            "lighting": lighting,
            "description": description,
            "combat_modifiers": self._determine_combat_modifiers(environment_type, features, weather, lighting)
        }

    def _determine_lighting(self, time_of_day, weather, environment_type):
        """
        Determine lighting conditions based on time and weather.

        Args:
            time_of_day: Time of day
            weather: Weather condition
            environment_type: Type of environment

        Returns:
            Lighting condition string
        """
        # Start with default lighting based on time
        if time_of_day in ["Dawn", "Dusk"]:
            lighting = "Dim Light"
        elif time_of_day in ["Morning", "Noon", "Afternoon"]:
            lighting = "Bright Light"
        elif time_of_day in ["Evening"]:
            lighting = "Dim Light"
        elif time_of_day in ["Night", "Midnight"]:
            lighting = "Darkness"
        else:
            lighting = "Bright Light"

        # Adjust based on weather
        if weather in ["Fog", "Heavy Rain", "Blizzard", "Sandstorm"]:
            # Make lighting one step darker
            if lighting == "Bright Light":
                lighting = "Dim Light"
            elif lighting == "Dim Light":
                lighting = "Darkness"

        # Adjust based on environment
        if environment_type == "dungeon" or environment_type == "underdark":
            # Dungeons and underdark are typically dark
            lighting = "Darkness"
        elif environment_type == "forest" and time_of_day in ["Morning", "Noon", "Afternoon"]:
            # Forests filter light
            lighting = "Dim Light"

        return lighting

    def _generate_environment_description(self, environment_type, features, weather, time_of_day, lighting):
        """
        Generate a descriptive text for the environment.

        Args:
            environment_type: Type of environment
            features: List of environment features
            weather: Weather condition
            time_of_day: Time of day
            lighting: Lighting condition

        Returns:
            Description text
        """
        # Environment opening descriptions
        environment_openings = {
            "forest": ["A dense forest surrounds you", "Tall trees tower above",
                       "The woodland stretches in all directions"],
            "mountain": ["Rugged mountain terrain extends before you", "The rocky slopes rise steeply",
                         "The mountain path winds ahead"],
            "dungeon": ["The dark dungeon corridors stretch before you", "Ancient stonework lines the walls",
                        "The air is stale in this underground complex"],
            "urban": ["The city streets bustle with activity", "Buildings rise around you",
                      "The urban landscape spreads out"],
            "coastal": ["Waves crash against the shore", "The salty sea breeze fills the air",
                        "The coastline stretches into the distance"],
            "desert": ["The desert sands stretch endlessly", "Heat rises in waves from the barren landscape",
                       "The arid desert extends in all directions"],
            "grassland": ["The open plains stretch toward the horizon", "Tall grasses sway in the breeze",
                          "The wide savanna extends around you"],
            "arctic": ["The frozen tundra stretches out", "Snow and ice cover everything in sight",
                       "The frigid landscape extends into the distance"],
            "underdark": ["The vast underground cavern opens before you", "Darkness pervades this subterranean realm",
                          "The twisting tunnels of the underdark stretch ahead"],
            "swamp": ["The murky swamp waters stretch out", "Twisted trees rise from the boggy terrain",
                      "The humid swampland extends in all directions"]
        }

        # Select an opening line
        opening_options = environment_openings.get(environment_type, ["The area around you"])
        opening = random.choice(opening_options)

        # Create description
        description = f"{opening}, as {time_of_day.lower()} brings {weather.lower()} conditions. "

        # Add lighting description
        if lighting == "Bright Light":
            description += "Visibility is excellent. "
        elif lighting == "Dim Light":
            description += "Visibility is limited, with shadows obscuring details. "
        elif lighting == "Darkness":
            description += "Darkness engulfs the area, making visibility extremely poor without a light source. "

        # Add features
        if features:
            feature_text = ", ".join(features[:-1])
            if len(features) > 1:
                feature_text += f", and {features[-1]}"
            else:
                feature_text = features[0]

            description += f"The area features {feature_text}."

        return description

    def _determine_combat_modifiers(self, environment_type, features, weather, lighting):
        """
        Determine combat modifiers based on environment conditions.

        Args:
            environment_type: Type of environment
            features: List of environment features
            weather: Weather condition
            lighting: Lighting condition

        Returns:
            Dictionary of combat modifiers
        """
        modifiers = {}

        # Lighting modifiers
        if lighting == "Dim Light":
            modifiers["perception"] = -2  # Penalty to perception checks
            modifiers["ranged_attacks"] = -2  # Penalty to ranged attacks
        elif lighting == "Darkness":
            modifiers["perception"] = -5  # Significant penalty to perception
            modifiers["ranged_attacks"] = -5  # Significant penalty to ranged attacks
            modifiers["melee_attacks"] = -2  # Penalty to melee attacks

        # Weather modifiers
        if weather in ["Rain", "Snow", "Fog"]:
            modifiers["perception"] = modifiers.get("perception", 0) - 2
            modifiers["ranged_attacks"] = modifiers.get("ranged_attacks", 0) - 2
        elif weather in ["Thunderstorm", "Blizzard", "Sandstorm"]:
            modifiers["perception"] = modifiers.get("perception", 0) - 5
            modifiers["ranged_attacks"] = modifiers.get("ranged_attacks", 0) - 5
            modifiers["movement"] = 0.5  # Half movement speed

        # Terrain modifiers based on environment and features
        difficult_terrain_environments = ["swamp", "mountain", "forest", "underdark"]
        difficult_terrain_features = ["Thick Undergrowth", "Rocky Terrain", "Bog", "Narrow Ledges", "Boulder Field"]

        if environment_type in difficult_terrain_environments or any(
                feature in difficult_terrain_features for feature in features):
            modifiers["movement"] = modifiers.get("movement", 0.75)  # Difficult terrain reduces movement

        # Cover modifiers
        cover_features = ["Dense Foliage", "Tree Canopy", "Boulder Field", "Ancient Ruins", "Urban Buildings"]

        if any(feature in cover_features for feature in features):
            modifiers["cover"] = "Half Cover"  # +2 AC and Dexterity saving throws

        return modifiers

    def apply_environment_effect(self, entity, environment):
        """
        Apply environmental effects to an entity.

        Args:
            entity: Entity affected by environment
            environment: Environment data

        Returns:
            Effect results
        """
        effects = []

        # Check for hazards
        for hazard in environment.get("hazards", []):
            # Determine if hazard triggers
            trigger_chance = 0.2  # 20% chance by default

            if random.random() < trigger_chance:
                # Hazard triggers
                effect = self._resolve_hazard(entity, hazard)
                effects.append(effect)

        # Apply lighting and weather effects
        lighting = environment.get("lighting", "Bright Light")
        weather = environment.get("weather", "Clear")

        lighting_effect = self._apply_lighting_effect(entity, lighting)
        if lighting_effect:
            effects.append(lighting_effect)

        weather_effect = self._apply_weather_effect(entity, weather, environment.get("type", ""))
        if weather_effect:
            effects.append(weather_effect)

        return effects

    def _resolve_hazard(self, entity, hazard):
        """
        Resolve the effect of a hazard on an entity.

        Args:
            entity: Entity affected by hazard
            hazard: Hazard data

        Returns:
            Hazard effect result
        """
        hazard_name = hazard.get("name", "Unknown Hazard")
        hazard_type = hazard.get("type", "trap")
        dc = hazard.get("dc", 12)
        damage_dice = hazard.get("damage", "1d6")

        # Determine appropriate saving throw
        save_ability = "dexterity"  # Default

        if hazard_type == "poison":
            save_ability = "constitution"
        elif hazard_type == "social":
            save_ability = "charisma"
        elif hazard_type == "exhaustion":
            save_ability = "constitution"

        # Roll saving throw
        save_mod = 0
        abilities = entity.get("stats", {}).get("abilities", {})
        if save_ability in abilities:
            ability_score = abilities[save_ability]
            save_mod = (ability_score - 10) // 2

        save_roll = random.randint(1, 20) + save_mod
        saved = save_roll >= dc

        # Calculate effect
        effect = {
            "hazard": hazard_name,
            "type": hazard_type,
            "dc": dc,
            "save_ability": save_ability,
            "save_roll": save_roll,
            "saved": saved,
        }

        # Apply damage if applicable
        if damage_dice != "0":
            damage = self._roll_dice(damage_dice)

            if saved and hazard_type in ["trap", "hazard", "weather"]:
                damage = damage // 2  # Half damage on successful save

            effect["damage"] = damage

            # Apply damage to entity
            if "current_hp" in entity:
                old_hp = entity["current_hp"]
                current_hp = old_hp

                # Convert to int if necessary
                if isinstance(current_hp, str):
                    try:
                        current_hp = int(current_hp)
                    except (ValueError, TypeError):
                        current_hp = 0

                # Apply damage
                entity["current_hp"] = max(0, current_hp - damage)
                effect["old_hp"] = old_hp
                effect["new_hp"] = entity["current_hp"]

        # Apply conditions if applicable
        if hazard_type == "poison" and not saved:
            if "conditions" not in entity:
                entity["conditions"] = []

            entity["conditions"].append({
                "type": "poisoned",
                "duration": 1,  # 1 round
                "source": hazard_name
            })

            effect["condition_applied"] = "poisoned"

        elif hazard_type == "exhaustion" and not saved:
            # Increase exhaustion level
            exhaustion_level = entity.get("exhaustion", 0)
            entity["exhaustion"] = exhaustion_level + 1

            effect["exhaustion_level"] = entity["exhaustion"]

        return effect

    def _apply_lighting_effect(self, entity, lighting):
        """
        Apply lighting effects to an entity.

        Args:
            entity: Entity affected by lighting
            lighting: Lighting condition

        Returns:
            Lighting effect result or None
        """
        # Only apply effects for dim light or darkness
        if lighting == "Bright Light":
            return None

        effect = {
            "type": "lighting",
            "condition": lighting
        }

        if lighting == "Dim Light":
            # Disadvantage on perception checks
            effect["perception_modifier"] = "disadvantage"

        elif lighting == "Darkness":
            # Various penalties unless entity has darkvision
            has_darkvision = entity.get("stats", {}).get("darkvision", False)

            if not has_darkvision:
                effect["perception_modifier"] = "disadvantage"
                effect["attack_modifier"] = "disadvantage"
                effect["attackers_modifier"] = "advantage"  # Attackers have advantage

        return effect

    def _apply_weather_effect(self, entity, weather, environment_type):
        """
        Apply weather effects to an entity.

        Args:
            entity: Entity affected by weather
            weather: Weather condition
            environment_type: Type of environment

        Returns:
            Weather effect result or None
        """
        # Only apply effects for significant weather
        if weather in ["Clear", "Cloudy"]:
            return None

        effect = {
            "type": "weather",
            "condition": weather
        }

        if weather in ["Rain", "Snow", "Fog"]:
            # Minor effects
            effect["perception_modifier"] = "disadvantage"
            effect["ranged_attacks_modifier"] = "disadvantage"

        elif weather in ["Thunderstorm", "Blizzard", "Sandstorm"]:
            # Major effects
            effect["perception_modifier"] = "disadvantage"
            effect["ranged_attacks_modifier"] = "disadvantage"
            effect["movement_multiplier"] = 0.5  # Half movement speed

            # Check for environmental damage in extreme conditions
            if (weather == "Blizzard" and environment_type == "arctic") or \
                    (weather == "Sandstorm" and environment_type == "desert"):

                # Possibly apply damage each round
                if random.random() < 0.2:  # 20% chance per round
                    damage = random.randint(1, 4)  # 1d4 damage

                    if "current_hp" in entity:
                        old_hp = entity["current_hp"]
                        current_hp = old_hp

                        # Convert to int if necessary
                        if isinstance(current_hp, str):
                            try:
                                current_hp = int(current_hp)
                            except (ValueError, TypeError):
                                current_hp = 0

                        # Apply damage
                        entity["current_hp"] = max(0, current_hp - damage)
                        effect["damage"] = damage
                        effect["old_hp"] = old_hp
                        effect["new_hp"] = entity["current_hp"]

        return effect

    def _roll_dice(self, dice_str):
        """Roll dice based on string format like '3d6' or '1d10'."""
        if "+" in dice_str:
            dice_part, bonus_part = dice_str.split("+")
            num_dice, die_size = map(int, dice_part.split("d"))
            bonus = int(bonus_part)

            total = bonus
            for _ in range(num_dice):
                total += random.randint(1, die_size)

            return total
        else:
            num_dice, die_size = map(int, dice_str.split("d"))

            total = 0
            for _ in range(num_dice):
                total += random.randint(1, die_size)

            return total