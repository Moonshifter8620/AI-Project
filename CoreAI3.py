# CoreAI2.py - CHUNK 1
# Enhanced Dungeons & Dragons Narrative AI System with Improved Dynamic Responses

import os
import random
import json
import logging
import time
from typing import Dict, List, Optional, Union, Any
from threading import Lock

# Import core game system components
from DataManager.DatabaseLoader import DatabaseLoader
from DataManager.MonsterData import MonsterData
from DataManager.EntityConverter import EntityConverter

# Import combat engine components
from CombatEngine.CombatManager import CombatManager
from CombatEngine.InitiativeTracker import InitiativeTracker
from CombatEngine.ActionResolver import ActionResolver
from CombatEngine.SpellSystem import SpellSystem
from CombatEngine.ConditionTracker import ConditionTracker

# Import encounter engine components
from EncounterEngine.EncounterGenerator import EncounterGenerator
from EncounterEngine.EnvironmentManager import EnvironmentManager
from EncounterEngine.TreasureGenerator import TreasureGenerator

# Import new language processing components
from NarrativeEngine.language_integration import LanguageIntegration
from NarrativeEngine.language_client import LanguageServiceClient
from NarrativeEngine.fantasy_text_adapter import TextGenerationAdapter

# Utility module for shared functions
from Utilities.common import roll_dice, calculate_modifier, load_resource

# Global logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dm_ai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DungeonMasterAI")


class DungeonMasterAI:
    """
    Enhanced AI system for autonomous Dungeon Mastering
    with advanced narrative generation capabilities.

    Integrates game mechanics, encounter generation,
    and sophisticated dynamic language processing.
    """

    def __init__(self,
                 database_path: str = "Databases",
                 language_service_url: str = "http://localhost:8000",
                 log_level: int = logging.INFO,
                 lazy_loading: bool = False):
        """
        Initialize the enhanced Dungeon Master AI system.

        Args:
            database_path: Path to game databases
            language_service_url: URL for language generation service
            log_level: Logging verbosity level
            lazy_loading: Whether to load components on demand (True) or at startup (False)
        """
        # Configure logging
        logger.setLevel(log_level)
        logger.info("Initializing Enhanced Dungeon Master AI...")

        # Set core paths and configurations
        self.database_path = database_path
        self.language_service_url = language_service_url
        self.lazy_loading = lazy_loading

        # Thread safety
        self.lock = Lock()

        # Component tracking dict to support lazy loading
        self._components = {}

        # Initialize core systems (always loaded)
        self._init_data_management()

        # Initialize other systems (lazy or eager loading)
        if not lazy_loading:
            self._init_all_components()

        # Initialize game state tracking (always loaded)
        self._init_game_state()

        # Campaign and world configuration settings
        self.campaign_settings = {
            "difficulty": "medium",  # easy, medium, hard, deadly
            "narrative_style": "balanced",  # combat-focused, narrative-focused, balanced
            "magic_level": "standard",  # low, standard, high
            "allow_homebrew": False,
            "advancement_style": "milestone",  # milestone or xp

            # Enhanced narrative style settings
            "dialogue_verbosity": "medium",  # terse, medium, verbose
            "description_detail": "medium",  # minimal, medium, vivid
            "narrative_tone": "neutral"  # grim, neutral, lighthearted
        }

        logger.info("Enhanced Dungeon Master AI initialized successfully")

        # CoreAI2.py - CHUNK 2
        # Component initialization and centralized error handling

        def _init_all_components(self):
            """Initialize all system components at once."""
            self._init_combat_engine()
            self._init_encounter_engine()
            self._init_narrative_engine()

        def _get_component(self, component_name, init_method):
            """
            Get a component, initializing it if needed (lazy loading support).

            Args:
                component_name: Name of the component
                init_method: Method to call to initialize the component

            Returns:
                The requested component
            """
            with self.lock:
                if component_name not in self._components or self._components[component_name] is None:
                    # Need to initialize the component
                    logger.debug(f"Lazy loading component: {component_name}")
                    init_method()
                return self._components.get(component_name)

        def _handle_error(self, error, component, fallback_creator=None):
            """
            Centralized error handler for component initialization.

            Args:
                error: The exception that occurred
                component: The component that failed to initialize
                fallback_creator: Optional function to create a fallback implementation

            Returns:
                Fallback implementation if provided, otherwise None
            """
            logger.error(f"Error initializing {component}: {error}")

            if fallback_creator:
                logger.warning(f"Using fallback implementation for {component}")
                return fallback_creator()
            return None

        def _init_data_management(self):
            """Initialize data management components."""
            logger.info("Initializing data management components...")

            try:
                # Initialize database loader
                self.database_loader = DatabaseLoader(self.database_path)
                self._components['database_loader'] = self.database_loader

                # Load essential databases
                self.monster_db = self.database_loader.load_database("monsters")
                self.spell_db = self.database_loader.load_database("spells")

                # Initialize monster and entity processors
                self.monster_data = MonsterData()
                self.monster_data.load_monsters(self.monster_db)
                self._components['monster_data'] = self.monster_data

                self.entity_converter = EntityConverter()
                self._components['entity_converter'] = self.entity_converter

                # Load supplemental databases
                self.databases = {
                    "races": self.database_loader.load_database("races"),
                    "classes": self.database_loader.load_database("classes"),
                    "backgrounds": self.database_loader.load_database("backgrounds"),
                    "magic_items": self.database_loader.load_database("magic_items")
                }
                self._components['databases'] = self.databases

                logger.info("Databases loaded successfully")

            except Exception as e:
                self._handle_error(e, "data management")
                # Data management is critical, so raise the error
                raise

        def _init_combat_engine(self):
            """
            Initialize combat system components.
            Provides advanced combat management and tracking.
            """
            logger.info("Initializing combat engine components...")

            try:
                # Core combat management systems
                self.combat_manager = CombatManager(self)
                self._components['combat_manager'] = self.combat_manager

                self.initiative_tracker = InitiativeTracker()
                self._components['initiative_tracker'] = self.initiative_tracker

                self.action_resolver = ActionResolver()
                self._components['action_resolver'] = self.action_resolver

                self.spell_system = SpellSystem()
                self._components['spell_system'] = self.spell_system

                self.condition_tracker = ConditionTracker()
                self._components['condition_tracker'] = self.condition_tracker

                logger.info("Combat engine components initialized successfully")

            except Exception as e:
                self._handle_error(e, "combat engine")
                # Create fallbacks for non-critical components
                self._components['combat_manager'] = self._create_stub_combat_manager()

        def _init_encounter_engine(self):
            """
            Initialize encounter generation and management systems.
            Provides dynamic and balanced encounter creation.
            """
            logger.info("Initializing encounter engine components...")

            try:
                # Encounter generation and environment management
                self.encounter_generator = EncounterGenerator()
                self._components['encounter_generator'] = self.encounter_generator

                self.environment_manager = EnvironmentManager()
                self._components['environment_manager'] = self.environment_manager

                self.treasure_generator = TreasureGenerator()
                self._components['treasure_generator'] = self.treasure_generator

                # Configure monster database
                if self.monster_db:
                    # Properly initialize encounter generator with monster database
                    self.encounter_generator.load_monster_database(self.monster_db)

                logger.info("Encounter engine components initialized successfully")

            except Exception as e:
                self._handle_error(e, "encounter engine")
                # Create fallbacks for non-critical components
                self._components['encounter_generator'] = self._create_stub_encounter_generator()

        # CoreAI2.py - CHUNK 3
        # Narrative Engine and Game State Management

        def _init_narrative_engine(self):
            """
            Initialize advanced narrative generation components.
            Integrates language processing for rich storytelling.
            """
            logger.info("Initializing narrative language processing...")

            try:
                # Context file path for persistent narrative memory
                context_file = os.path.join(self.database_path, "narrative_context.json")

                # Initialize language integration services
                self.language_client = LanguageServiceClient(self.language_service_url)
                self._components['language_client'] = self.language_client

                # Create text generation adapter with data and cache directories
                data_folder = os.path.join(self.database_path, "NarrativeEngine", "Corpus")
                cache_dir = os.path.join(self.database_path, "NarrativeEngine", "Cache")

                self.text_generation_adapter = TextGenerationAdapter(
                    data_folder=data_folder,
                    cache_dir=cache_dir
                )
                self._components['text_generation_adapter'] = self.text_generation_adapter

                # Initialize language integration with context management
                self.language_integration = LanguageIntegration(
                    service_url=self.language_service_url,
                    context_file=context_file
                )
                self._components['language_integration'] = self.language_integration

                # Verify language services are operational
                if not self.language_client.is_connected():
                    logger.warning("Language service client not connected. Using enhanced fallback.")
                    self._components['language_integration'] = self._create_dynamic_language_service()

                logger.info("Narrative language processing initialized successfully")

            except Exception as e:
                fallback = self._handle_error(e, "narrative engine", self._create_dynamic_language_service)
                self._components['language_integration'] = fallback

        def _create_dynamic_language_service(self):
            """Create a more dynamic fallback language service."""

            class DynamicLanguageService:
                """Enhanced stub implementation providing more dynamic language services."""

                def __init__(self):
                    self.npcs = {}
                    self.locations = {}
                    self.party_data = []
                    self.mood_vocabulary = {
                        "happy": ["cheerfully", "with enthusiasm", "with a bright smile"],
                        "sad": ["glumly", "with a sigh", "sorrowfully"],
                        "angry": ["harshly", "with a scowl", "through gritted teeth"],
                        "afraid": ["nervously", "with a tremble", "hesitantly"],
                        "neutral": ["calmly", "evenly", "simply"]
                    }
                    self.time_effects = {
                        "dawn": "soft light illuminates",
                        "day": "bright sunlight reveals",
                        "dusk": "fading light casts long shadows on",
                        "night": "darkness shrouds"
                    }
                    self.weather_effects = {
                        "clear": "under clear skies",
                        "rain": "as rain patters around you",
                        "fog": "through swirling mist",
                        "snow": "while snowflakes drift down"
                    }
                    # History tracking for continuity
                    self.dialogue_history = {}
                    self.scene_history = []
                    self.interaction_history = []

                def _get_npc_mood(self, npc_id):
                    """Get an NPC's current mood if available."""
                    npc = self.npcs.get(npc_id, {})
                    return npc.get('mood', 'neutral')

                def _get_time_phrase(self):
                    """Get a phrase based on the current time of day."""
                    time_of_day = self.party_data.get('time_of_day', 'day')
                    return self.time_effects.get(time_of_day, "the present moment shows")

                def _get_weather_phrase(self):
                    """Get a phrase based on the current weather."""
                    weather = self.party_data.get('weather', 'clear')
                    return self.weather_effects.get(weather, "in the ambient conditions")

                def generate_dialogue(self, npc_id, player_text, topic=None):
                    """Generate a dynamic dialogue response."""
                    # Track dialogue for continuity
                    if npc_id not in self.dialogue_history:
                        self.dialogue_history[npc_id] = []

                    # Get NPC data
                    npc = self.npcs.get(npc_id, {"name": "the person"})
                    name = npc.get("name", "the person")
                    npc_type = npc.get("type", "stranger")
                    mood = self._get_npc_mood(npc_id)
                    manner = random.choice(self.mood_vocabulary.get(mood, self.mood_vocabulary["neutral"]))

                    # Create contextual response based on topic and history
                    if topic:
                        topic_responses = {
                            "quest": f"{name} {manner} discusses the task at hand.",
                            "rumor": f"{name} {manner} shares some local gossip.",
                            "trade": f"{name} {manner} haggles over prices.",
                            "lore": f"{name} {manner} recounts an old tale."
                        }
                        response = topic_responses.get(topic, f"{name} {manner} responds to your question.")
                    else:
                        # Check dialogue history for continuity
                        if self.dialogue_history[npc_id]:
                            last_exchange = self.dialogue_history[npc_id][-1]
                            if "quest" in last_exchange or "task" in last_exchange:
                                response = f"{name} {manner} continues discussing the quest details."
                            elif "personal" in last_exchange:
                                response = f"{name} {manner} shares more about their past."
                            else:
                                response = f"{name} {manner} acknowledges your words."
                        else:
                            response = f"{name} {manner} greets you as a {npc_type}."

                    # Store this exchange
                    exchange = {"player": player_text, "npc": response, "topic": topic}
                    self.dialogue_history[npc_id].append(exchange)

                    return {"text": response}

                def generate_description(self, location_id=None, **kwargs):
                    """Generate a dynamic location description."""
                    # Get location data
                    location = self.locations.get(location_id, {"name": "the area", "type": "location"})
                    location_name = location.get("name", "the area")
                    location_type = location.get("type", "location")

                    # Use time and weather for atmosphere
                    time_phrase = self._get_time_phrase()
                    weather_phrase = self._get_weather_phrase()

                    # Check if we've been here before
                    visited = any(loc == location_id for loc in self.scene_history)
                    visit_phrase = "once again " if visited else ""

                    # Create dynamic description
                    description = f"You {visit_phrase}find yourself in {location_name}, a {location_type}. The {time_phrase} the surroundings {weather_phrase}."

                    # Add location-specific details
                    if location_type == "forest":
                        description += " Trees tower above you, their leaves rustling in the breeze."
                    elif location_type == "dungeon":
                        description += " Stone walls surround you, with passages leading into darkness."
                    elif location_type == "town":
                        description += " Buildings line the streets, with people going about their business."

                    # Add to scene history
                    self.scene_history.append(location_id)

                    return {"text": description}

                def generate_combat(self, **kwargs):
                    """Generate a dynamic combat description."""
                    action_type = kwargs.get('action_type', 'attack')
                    attacker = kwargs.get('attacker', 'The attacker')
                    defender = kwargs.get('defender', 'the target')
                    outcome = kwargs.get('outcome', 'hit')
                    weapon = kwargs.get('weapon', 'weapon')
                    damage = kwargs.get('damage_amount', 0)
                    critical = kwargs.get('critical', False)

                    # Create varied combat descriptions
                    action_verbs = {
                        "attack": ["swings at", "strikes at", "lunges toward", "assaults"],
                        "cast": ["casts a spell at", "conjures magic targeting",
                                 "unleashes arcane energy toward"],
                        "defend": ["blocks", "parries", "deflects", "evades"],
                        "move": ["maneuvers around", "circles", "advances on", "retreats from"]
                    }

                    # Select appropriate verb
                    verb_options = action_verbs.get(action_type, action_verbs["attack"])
                    verb = random.choice(verb_options)

                    # Build dynamic description
                    if action_type == "attack":
                        if critical:
                            description = f"{attacker} critically {verb} {defender} with {weapon}, dealing {damage} devastating damage!"
                        elif outcome == "hit":
                            description = f"{attacker} {verb} {defender} with {weapon}, dealing {damage} damage."
                        else:
                            description = f"{attacker} {verb} {defender} with {weapon}, but misses."
                    elif action_type == "cast":
                        spell = kwargs.get('spell', 'a spell')
                        if outcome == "hit":
                            description = f"{attacker} {verb} {defender} with {spell}, causing {damage} damage."
                        else:
                            description = f"{attacker} {verb} {defender} with {spell}, but they resist the effect."
                    else:
                        description = f"{attacker} {verb} {defender}."

                    return {"text": description}

                def register_npc(self, npc_id, npc_data):
                    self.npcs[npc_id] = npc_data
                    return {"text": f"NPC {npc_data.get('name', 'Unknown')} registered."}

                def register_location(self, location_id, location_data):
                    self.locations[location_id] = location_data
                    return {"text": f"Location {location_id} registered."}

                def update_party(self, party_data):
                    self.party_data = party_data
                    return {"text": "Party information updated."}

                def generate_quest(self, **kwargs):
                    import json
                    quest_data = {
                        "title": "Simple Quest",
                        "description": "A basic quest for adventurers.",
                    }
                    return {"text": json.dumps(quest_data)}

                def generate_transition(self, from_scene, to_scene, **kwargs):
                    return {"text": f"The party travels from {from_scene} to {to_scene}."}

                def update_world_state(self, **kwargs):
                    return {"text": "World state updated."}

                def add_interaction(self, **kwargs):
                    return {"text": "Interaction recorded."}

                def save_context(self, filepath=None):
                    return True

                def load_context(self, filepath=None):
                    return True

            return DynamicLanguageService()
        # CoreAI2.py - CHUNK 4
        # Game State and Character Generation

    def _init_game_state(self):
        """
        Initialize comprehensive game state tracking.
        Provides persistent world and narrative context.
        """
        self.game_state = {
            # Player party management
            "player_party": [],
            "party_resources": {
                "gold": 0,
                "supplies": {},
                "magical_items": []
            },

            # Narrative and world tracking
            "current_location": None,
            "world_time": {
                "day": 1,
                "time_of_day": "day",
                "weather": "clear",
                "month": "Hammer",  # Default Forgotten Realms calendar
                "year": 1500  # Default starting year
            },
            "active_quests": [],
            "completed_quests": [],

            # Narrative context
            "world_events": [],
            "notable_npcs": {},
            "faction_relations": {},

            # Dynamic state tracking
            "exploration_state": {
                "discovered_locations": set(),
                "unexplored_regions": set()
            },

            # Narrative memory
            "story_beats": [],
            "significant_encounters": []
        }

        # Link game state with language integration context
        if self._components.get('language_integration'):
            try:
                self.language_integration.update_party(self.game_state["player_party"])
                self.language_integration.update_world_state(
                    self.game_state["world_time"]["time_of_day"],
                    self.game_state["world_time"]["weather"]
                )
            except Exception as e:
                logger.error(f"Error updating party in language context: {e}")

    def generate_character(self, character_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive character with enhanced generation capabilities.

        Args:
            character_config: Configuration dictionary for character creation

        Returns:
            Fully generated character dictionary
        """
        logger.info(f"Generating character with config: {character_config}")

        try:
            # Validate and prepare base character configuration
            race = character_config.get('race', 'human').lower()
            character_class = character_config.get('class', 'fighter').lower()
            background = character_config.get('background', 'adventurer').lower()
            level = character_config.get('level', 1)
            generation_method = character_config.get('method', 'standard_array')

            # Validate inputs against databases
            race = self._validate_race(race)
            character_class = self._validate_class(character_class)
            background = self._validate_background(background)

            # Calculate proficiency bonus based on level
            proficiency_bonus = (level - 1) // 4 + 2

            # Create base character structure
            character = {
                'id': f'char_{random.randint(1000, 9999)}',
                'name': character_config.get('name') or self._generate_character_name(race),
                'race': race,
                'class': character_class,
                'background': background,
                'level': level,
                'experience': 0,
                'alignment': character_config.get('alignment', 'neutral'),
                'proficiency_bonus': proficiency_bonus,

                # Core attributes
                'abilities': {},
                'saving_throws': {},
                'skills': {},

                # Derived stats
                'hit_points': 0,
                'armor_class': 10,
                'speed': 30,  # Default movement speed

                # Character progression
                'proficiencies': [],
                'features': [],
                'languages': [],

                # Equipment and inventory
                'equipment': [],
                'currency': {
                    'copper': 0,
                    'silver': 0,
                    'electrum': 0,
                    'gold': 10,  # Starting gold
                    'platinum': 0
                },

                # Magic and spellcasting
                'spellcasting': {
                    'cantrips': [],
                    'spell_slots': {},
                    'prepared_spells': []
                },

                # For more dynamic character interactions
                'personality': {
                    'traits': [],
                    'ideals': [],
                    'bonds': [],
                    'flaws': [],
                    'mood': 'neutral',
                    'relationship_scores': {}
                }
            }

            # Generate ability scores
            character['abilities'] = self._generate_ability_scores(
                method=generation_method,
                character_class=character_class
            )

            # Apply racial modifiers
            character['abilities'] = self._apply_racial_ability_modifiers(
                character['abilities'],
                race
            )

            # Calculate derived stats
            character['hit_points'] = self._calculate_hit_points(character)
            character['armor_class'] = self._calculate_armor_class(character)

            # Add racial traits
            racial_traits = self._get_racial_traits(race)
            character['features'].extend(racial_traits.get('features', []))
            character['languages'].extend(racial_traits.get('languages', []))
            character['speed'] = racial_traits.get('speed', 30)

            # Add class features and proficiencies
            class_features = self._get_class_features(
                character_class,
                level
            )
            character['features'].extend(class_features.get('features', []))
            character['proficiencies'].extend(class_features.get('proficiencies', []))

            # Generate equipment
            character['equipment'] = self._generate_starting_equipment(character)

            # Generate spells if applicable
            character['spellcasting'] = self._generate_spells(character)

            # Add background details including personality traits
            background_details = self._apply_background_details(character)
            character.update(background_details)

            # Generate dynamic backstory
            character['backstory'] = self._generate_character_backstory(character)

            # Log character generation
            logger.info(f"Character generated: {character['name']} - {character['race']} {character['class']}")

            # Add to game state
            self._add_character_to_game_state(character)

            return character

        except Exception as e:
            logger.error(f"Character generation failed: {e}")
            raise

    # CoreAI2.py - CHUNK 5
    # Character Generation Helper Methods

    def _validate_race(self, race: str) -> str:
        """Validate and normalize race input."""
        # Convert race to lowercase for consistent comparison
        race = race.lower()

        # Check if race exists directly in database
        if race in self.databases['races']:
            return race

        # Common races for fallback
        generic_races = {
            'elf': True, 'dwarf': True, 'halfling': True, 'human': True,
            'gnome': True, 'half-elf': True, 'half-orc': True,
            'tiefling': True, 'dragonborn': True
        }

        # Check for generic race
        if race in generic_races:
            return race

        # Try partial match
        for race_key in self.databases['races'].keys():
            if race in race_key.lower() or race_key.lower() in race:
                return race_key

        # Default to human if no match found
        logger.warning(f"Race '{race}' not found, defaulting to human")
        return 'human'

    def _validate_class(self, character_class: str) -> str:
        """Validate and normalize class input."""
        character_class = character_class.lower()

        # Check direct match
        if character_class in self.databases['classes']:
            return character_class

        # Core classes for fallback
        core_classes = {
            'fighter': True, 'wizard': True, 'rogue': True, 'cleric': True,
            'barbarian': True, 'bard': True, 'druid': True, 'monk': True,
            'paladin': True, 'ranger': True, 'sorcerer': True, 'warlock': True
        }

        if character_class in core_classes:
            return character_class

        # Try partial match
        for class_key in self.databases['classes'].keys():
            if character_class in class_key.lower() or class_key.lower() in character_class:
                return class_key

        logger.warning(f"Class '{character_class}' not found, defaulting to fighter")
        return 'fighter'

    def _generate_character_name(self, race: str) -> str:
        """Generate a dynamic character name based on race."""
        try:
            # Use language integration if available
            if self._components.get('language_integration'):
                try:
                    name_prompt = f"Generate a unique {race} character name that reflects their heritage"
                    name_response = self.text_generation_adapter.generate_text(name_prompt, max_length=20)
                    generated_name = name_response.strip()

                    if len(generated_name) > 2 and len(generated_name) < 30:
                        return generated_name
                except Exception:
                    pass

            # Enhanced fallback name generation with more varied options
            name_sets = {
                'human': ['Aldric', 'Elena', 'Marcus', 'Sophia', 'Rowan', 'Lyra'],
                'elf': ['Aerith', 'Legolas', 'Arwen', 'Theren', 'Erevan', 'Elindra'],
                'dwarf': ['Thorin', 'Bardin', 'Helga', 'Durgan', 'Grimmir', 'Ingra'],
                'halfling': ['Peregrin', 'Rosie', 'Bilbo', 'Lily', 'Milo', 'Poppy'],
                'gnome': ['Fizban', 'Trinket', 'Willow', 'Gimble', 'Nissa', 'Breena'],
                'tiefling': ['Lucian', 'Mephi', 'Zariel', 'Aza', 'Lilith', 'Dante']
            }

            # Get base race for lookup (e.g., 'high elf' -> 'elf')
            base_race = race.split()[0] if ' ' in race else race
            names = name_sets.get(base_race, name_sets['human'])

            # Add some randomness by combining name parts
            if random.random() < 0.3 and len(names) >= 2:
                first_part = random.choice(names)[:3]
                second_part = random.choice(names)[2:]
                return first_part + second_part

            return random.choice(names)

        except Exception as e:
            logger.warning(f"Name generation failed: {e}")
            return "Adventurer"

        # CoreAI2.py - CHUNK 6
        # More Character Generation Methods

        def _generate_ability_scores(self, method: str = 'standard_array', character_class: str = None) -> Dict[
            str, int]:
            """
            Generate ability scores using various methods.

            Args:
                method: Score generation method
                character_class: Character's class for optimization

            Returns:
                Dictionary of ability scores
            """
            if method == 'standard_array':
                # Standard array: 15, 14, 13, 12, 10, 8
                scores = [15, 14, 13, 12, 10, 8]
                random.shuffle(scores)
            elif method == 'point_buy':
                # Point-buy system with 27 points
                scores = self._point_buy_generation()
            elif method == 'roll':
                # 4d6 drop lowest method
                scores = self._roll_ability_scores()
            else:
                # Fallback to standard array
                scores = [15, 14, 13, 12, 10, 8]

            # Convert to dictionary with default order
            abilities = {
                'strength': scores[0],
                'dexterity': scores[1],
                'constitution': scores[2],
                'intelligence': scores[3],
                'wisdom': scores[4],
                'charisma': scores[5]
            }

            # Optimize for class if specified
            if character_class:
                abilities = self._optimize_abilities_for_class(abilities, character_class)

            return abilities

        def _roll_ability_scores(self) -> List[int]:
            """Roll 4d6 drop lowest for ability scores."""
            scores = []
            for _ in range(6):
                # Roll 4d6
                rolls = [random.randint(1, 6) for _ in range(4)]
                # Drop lowest
                rolls.remove(min(rolls))
                # Sum remaining
                scores.append(sum(rolls))
            # Sort descending
            return sorted(scores, reverse=True)

        def _point_buy_generation(self) -> List[int]:
            """
            Generate ability scores using point-buy method.

            Returns:
                List of ability scores
            """
            points = 27
            abilities = [8, 8, 8, 8, 8, 8]

            # Cost table: cost to raise from score to score+1
            cost_table = {
                8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
                13: 1, 14: 2, 15: 2
            }

            # Try to allocate points intelligently
            while points > 0:
                # Choose a random ability to improve
                ability_index = random.randint(0, 5)
                current_score = abilities[ability_index]

                # Check if we can improve this ability
                if current_score < 15 and points >= cost_table.get(current_score, 100):
                    cost = cost_table.get(current_score, 100)
                    abilities[ability_index] += 1
                    points -= cost

            return abilities

        def _optimize_abilities_for_class(self, abilities: Dict[str, int], character_class: str) -> Dict[str, int]:
            """
            Optimize ability scores for a specific class.

            Args:
                abilities: Current ability scores
                character_class: Character's class

            Returns:
                Optimized ability scores
            """
            # Prioritized ability scores for each class
            class_priorities = {
                'barbarian': ['strength', 'constitution', 'dexterity'],
                'bard': ['charisma', 'dexterity', 'constitution'],
                'cleric': ['wisdom', 'constitution', 'strength'],
                'druid': ['wisdom', 'constitution', 'dexterity'],
                'fighter': ['strength', 'constitution', 'dexterity'],
                'monk': ['dexterity', 'wisdom', 'constitution'],
                'paladin': ['strength', 'charisma', 'constitution'],
                'ranger': ['dexterity', 'wisdom', 'constitution'],
                'rogue': ['dexterity', 'intelligence', 'constitution'],
                'sorcerer': ['charisma', 'constitution', 'dexterity'],
                'warlock': ['charisma', 'constitution', 'dexterity'],
                'wizard': ['intelligence', 'constitution', 'dexterity']
            }

            # Use fighter as default if class not found
            priorities = class_priorities.get(character_class.lower(), class_priorities['fighter'])

            # Sort current abilities from highest to lowest
            sorted_scores = sorted(abilities.values(), reverse=True)
            optimized_abilities = {}

            # Assign scores based on class priorities
            for ability in priorities:
                if ability not in optimized_abilities:
                    optimized_abilities[ability] = sorted_scores.pop(0)

            # Assign remaining scores to remaining abilities
            remaining_abilities = [a for a in abilities.keys() if a not in optimized_abilities]

            for ability in remaining_abilities:
                if sorted_scores:
                    optimized_abilities[ability] = sorted_scores.pop(0)
                else:
                    # Fallback to 8 if no scores left
                    optimized_abilities[ability] = 8

            return optimized_abilities

        def _apply_racial_ability_modifiers(self, abilities: Dict[str, int], race: str) -> Dict[str, int]:
            """
            Apply racial ability score modifiers.

            Args:
                abilities: Base ability scores
                race: Character's race

            Returns:
                Ability scores with racial modifiers
            """
            # Racial ability score modifiers (expanded for more races)
            racial_modifiers = {
                'human': {
                    'strength': 1, 'dexterity': 1, 'constitution': 1,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 1
                },
                'hill dwarf': {'constitution': 2, 'wisdom': 1},
                'mountain dwarf': {'strength': 2, 'constitution': 2},
                'high elf': {'dexterity': 2, 'intelligence': 1},
                'wood elf': {'dexterity': 2, 'wisdom': 1},
                'dark elf': {'dexterity': 2, 'charisma': 1},
                'lightfoot halfling': {'dexterity': 2, 'charisma': 1},
                'stout halfling': {'dexterity': 2, 'constitution': 1},
                'forest gnome': {'intelligence': 2, 'dexterity': 1},
                'rock gnome': {'intelligence': 2, 'constitution': 1},
                'half-elf': {'charisma': 2, 'intelligence': 1, 'wisdom': 1},
                'half-orc': {'strength': 2, 'constitution': 1},
                'tiefling': {'charisma': 2, 'intelligence': 1},
                'dragonborn': {'strength': 2, 'charisma': 1},
                # Generic types
                'dwarf': {'constitution': 2},
                'elf': {'dexterity': 2},
                'halfling': {'dexterity': 2},
                'gnome': {'intelligence': 2}
            }

            # Normalize race input (handle variations)
            normalized_race = race.lower()

            # Find the appropriate modifiers
            modifiers = None
            for key in racial_modifiers.keys():
                if key.lower() == normalized_race or key.lower() in normalized_race:
                    modifiers = racial_modifiers[key]
                    break

            # Default to no modifiers if not found
            if not modifiers:
                modifiers = {}

            # Apply modifiers
            modified_abilities = abilities.copy()
            for ability, modifier in modifiers.items():
                modified_abilities[ability] += modifier

            return modified_abilities

    # CoreAI2.py - CHUNK 7
    # Race, Class and Background Features

    def _get_racial_traits(self, race: str) -> Dict[str, Any]:
        """
        Retrieve racial traits for a given race.

        Args:
            race: Character's race

        Returns:
            Dictionary of racial traits
        """
        # Comprehensive racial traits
        racial_traits = {
            'human': {
                'features': ['Versatility', 'Extra Language'],
                'languages': ['Common', 'One extra language of choice'],
                'speed': 30
            },
            'hill dwarf': {
                'features': [
                    'Darkvision', 'Dwarven Resilience',
                    'Dwarven Weapon Training', 'Dwarven Toughness'
                ],
                'languages': ['Common', 'Dwarvish'],
                'speed': 25
            },
            'high elf': {
                'features': [
                    'Darkvision', 'Keen Senses', 'Fey Ancestry',
                    'Trance', 'Elf Weapon Training', 'Cantrip'
                ],
                'languages': ['Common', 'Elvish'],
                'speed': 30
            },
            'lightfoot halfling': {
                'features': [
                    'Lucky', 'Brave', 'Halfling Nimbleness', 'Naturally Stealthy'
                ],
                'languages': ['Common', 'Halfling'],
                'speed': 25
            },
            'rock gnome': {
                'features': [
                    'Darkvision', 'Gnome Cunning', 'Artificer\'s Lore', 'Tinker'
                ],
                'languages': ['Common', 'Gnomish'],
                'speed': 25
            },
            'half-orc': {
                'features': [
                    'Darkvision', 'Menacing', 'Relentless Endurance', 'Savage Attacks'
                ],
                'languages': ['Common', 'Orc'],
                'speed': 30
            },
            'tiefling': {
                'features': [
                    'Darkvision', 'Hellish Resistance', 'Infernal Legacy'
                ],
                'languages': ['Common', 'Infernal'],
                'speed': 30
            },
            'dragonborn': {
                'features': [
                    'Draconic Ancestry', 'Breath Weapon', 'Damage Resistance'
                ],
                'languages': ['Common', 'Draconic'],
                'speed': 30
            },
            # Generic traits for base races
            'dwarf': {
                'features': ['Darkvision', 'Dwarven Resilience', 'Dwarven Combat Training'],
                'languages': ['Common', 'Dwarvish'],
                'speed': 25
            },
            'elf': {
                'features': ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance'],
                'languages': ['Common', 'Elvish'],
                'speed': 30
            },
            'halfling': {
                'features': ['Lucky', 'Brave', 'Halfling Nimbleness'],
                'languages': ['Common', 'Halfling'],
                'speed': 25
            },
            'gnome': {
                'features': ['Darkvision', 'Gnome Cunning'],
                'languages': ['Common', 'Gnomish'],
                'speed': 25
            }
        }

        # Normalize race input
        normalized_race = race.lower()

        # Try to find an exact match
        if normalized_race in racial_traits:
            return racial_traits[normalized_race]

        # Try to find a partial match
        for key in racial_traits.keys():
            if key in normalized_race:
                return racial_traits[key]

        # Default to human traits if race not found
        return racial_traits['human']

    def _get_class_features(self, character_class: str, level: int) -> Dict[str, List[str]]:
        """
        Retrieve class features for a given class and level.

        Args:
            character_class: Character's class
            level: Character's current level

        Returns:
            Dictionary of class features and proficiencies
        """
        # Comprehensive class features by level
        class_features = {
            'barbarian': {
                1: {
                    'features': ['Rage', 'Unarmored Defense'],
                    'proficiencies': [
                        'Light Armor', 'Medium Armor', 'Shields',
                        'Simple Weapons', 'Martial Weapons',
                        'Strength Saving Throws', 'Constitution Saving Throws'
                    ]
                },
                2: {
                    'features': ['Reckless Attack', 'Danger Sense'],
                    'proficiencies': []
                },
                3: {
                    'features': ['Primal Path', 'Path Feature'],
                    'proficiencies': []
                }
            },
            'fighter': {
                1: {
                    'features': ['Fighting Style', 'Second Wind'],
                    'proficiencies': [
                        'All Armor', 'Shields',
                        'Simple Weapons', 'Martial Weapons',
                        'Strength Saving Throws', 'Constitution Saving Throws'
                    ]
                },
                2: {
                    'features': ['Action Surge'],
                    'proficiencies': []
                },
                3: {
                    'features': ['Martial Archetype', 'Archetype Feature'],
                    'proficiencies': []
                }
            },
            'wizard': {
                1: {
                    'features': ['Spellcasting', 'Arcane Recovery'],
                    'proficiencies': [
                        'Daggers', 'Darts', 'Slings',
                        'Quarterstaffs', 'Light Crossbows',
                        'Intelligence Saving Throws', 'Wisdom Saving Throws'
                    ]
                },
                2: {
                    'features': ['Arcane Tradition', 'Tradition Feature'],
                    'proficiencies': []
                },
                3: {
                    'features': ['Cantrip Formulas'],
                    'proficiencies': []
                }
            },
            'rogue': {
                1: {
                    'features': ['Expertise', 'Sneak Attack', 'Thieves\' Cant'],
                    'proficiencies': [
                        'Light Armor', 'Simple Weapons', 'Hand Crossbows',
                        'Longswords', 'Rapiers', 'Shortswords',
                        'Dexterity Saving Throws', 'Intelligence Saving Throws'
                    ]
                },
                2: {
                    'features': ['Cunning Action'],
                    'proficiencies': []
                },
                3: {
                    'features': ['Roguish Archetype', 'Archetype Feature'],
                    'proficiencies': []
                }
            }
        }

        # Normalize class input
        normalized_class = character_class.lower()

        # Create default empty result
        collected_features = {
            'features': [],
            'proficiencies': []
        }

        # Get features for the specific class if available
        class_data = class_features.get(normalized_class, {})

        # If class not found in our data, return empty
        if not class_data:
            return collected_features

        # Collect features up to the current level
        for current_level in range(1, min(level + 1, 4)):  # Cap at level 3 for our dataset
            level_features = class_data.get(current_level, {})
            collected_features['features'].extend(level_features.get('features', []))
            collected_features['proficiencies'].extend(level_features.get('proficiencies', []))

        return collected_features

    def _apply_background_details(self, character):
        """Apply background details and personality traits."""
        # Get background from database
        background = character['background'].lower()

        # Initialize personality traits
        personality = {
            'traits': [],
            'ideals': [],
            'bonds': [],
            'flaws': []
        }

        # Add background features based on background
        background_details = {
            'acolyte': {
                'feature': 'Shelter of the Faithful',
                'description': 'You command the respect of those who share your faith',
                'trait': 'I quote sacred texts and proverbs in almost every situation.',
                'ideal': 'Tradition. The ancient traditions must be preserved and upheld.',
                'bond': 'Everything I do is for the common people.',
                'flaw': 'I am suspicious of strangers and suspect the worst of them.'
            },
            'criminal': {
                'feature': 'Criminal Contact',
                'description': 'You have a reliable contact in the criminal underworld',
                'trait': 'I always have a plan for what to do when things go wrong.',
                'ideal': 'Freedom. Chains are meant to be broken, as are those who would forge them.',
                'bond': 'I\'m trying to pay off an old debt I owe to a generous benefactor.',
                'flaw': 'When I see something valuable, I can\'t think about anything but how to steal it.'
            },
            'folk hero': {
                'feature': 'Rustic Hospitality',
                'description': 'People of your home region regard you with warmth',
                'trait': 'I judge people by their actions, not their words.',
                'ideal': 'Sincerity. There\'s no good in pretending to be something I\'m not.',
                'bond': 'I protect those who cannot protect themselves.',
                'flaw': 'I have a weakness for the vices of the city, especially hard drink.'
            },
            'noble': {
                'feature': 'Position of Privilege',
                'description': 'People are inclined to think the best of you',
                'trait': 'I take great pains to always look my best and follow the latest fashions.',
                'ideal': 'Responsibility. It is my duty to respect the authority of those above me.',
                'bond': 'I will face any challenge to win the approval of my family.',
                'flaw': 'I secretly believe that everyone is beneath me.'
            },
            'soldier': {
                'feature': 'Military Rank',
                'description': 'You have a military rank from your career as a soldier',
                'trait': 'I\'m always polite and respectful.',
                'ideal': 'Greater Good. Our lot is to lay down our lives in defense of others.',
                'bond': 'I fight for those who cannot fight for themselves.',
                'flaw': 'I made a terrible mistake in battle that cost many lives.'
            }
        }

        # Use default background if not found
        if background not in background_details:
            background = 'folk hero'

        # Add background details
        details = background_details[background]
        personality_update = {
            'feature': details['feature'],
            'feature_description': details['description'],
            'personality': {
                'traits': [details['trait']],
                'ideals': [details['ideal']],
                'bonds': [details['bond']],
                'flaws': [details['flaw']]
            }
        }

        # Update character with background details
        character['personality'].update(personality_update['personality'])

        return details

        # CoreAI2.py - CHUNK 8
        # Equipment, Spells, and Backstory Generation

        def _generate_starting_equipment(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
            """
            Generate starting equipment based on character's class and background.

            Args:
                character: Character dictionary

            Returns:
                List of equipment items
            """
            # Starting equipment by class
            class_equipment = {
                'barbarian': [
                    {'name': 'Greataxe', 'type': 'weapon', 'category': 'martial'},
                    {'name': 'Handaxe', 'type': 'weapon', 'category': 'simple', 'quantity': 2},
                    {'name': 'Explorer\'s Pack', 'type': 'gear', 'category': 'adventuring'},
                    {'name': 'Javelin', 'type': 'weapon', 'category': 'simple', 'quantity': 4}
                ],
                'fighter': [
                    {'name': 'Chain Mail', 'type': 'armor', 'category': 'heavy'},
                    {'name': 'Longsword', 'type': 'weapon', 'category': 'martial'},
                    {'name': 'Shield', 'type': 'armor', 'category': 'shield'},
                    {'name': 'Light Crossbow', 'type': 'weapon', 'category': 'ranged'},
                    {'name': 'Crossbow Bolts', 'type': 'ammunition', 'quantity': 20}
                ],
                'wizard': [
                    {'name': 'Quarterstaff', 'type': 'weapon', 'category': 'simple'},
                    {'name': 'Component Pouch', 'type': 'spellcasting gear'},
                    {'name': 'Spellbook', 'type': 'spellcasting gear'},
                    {'name': 'Scholar\'s Pack', 'type': 'gear', 'category': 'adventuring'}
                ],
                'rogue': [
                    {'name': 'Rapier', 'type': 'weapon', 'category': 'martial'},
                    {'name': 'Shortbow', 'type': 'weapon', 'category': 'ranged'},
                    {'name': 'Arrows', 'type': 'ammunition', 'quantity': 20},
                    {'name': 'Burglar\'s Pack', 'type': 'gear', 'category': 'adventuring'},
                    {'name': 'Leather Armor', 'type': 'armor', 'category': 'light'},
                    {'name': 'Dagger', 'type': 'weapon', 'category': 'simple', 'quantity': 2}
                ]
            }

            # Starting equipment by background
            background_equipment = {
                'acolyte': [
                    {'name': 'Holy Symbol', 'type': 'holy symbol'},
                    {'name': 'Prayer Book', 'type': 'book'},
                    {'name': 'Incense', 'type': 'religious item', 'quantity': 5},
                    {'name': 'Vestments', 'type': 'clothing'}
                ],
                'criminal': [
                    {'name': 'Crowbar', 'type': 'tool'},
                    {'name': 'Dark Common Clothes', 'type': 'clothing'},
                    {'name': 'Thieves\' Tools', 'type': 'tool'}
                ],
                'folk_hero': [
                    {'name': 'Artisan\'s Tools', 'type': 'tool'},
                    {'name': 'Shovel', 'type': 'tool'},
                    {'name': 'Iron Pot', 'type': 'gear'}
                ]
            }

            # Normalize inputs
            character_class = character['class'].lower()
            background = character['background'].lower().replace(' ', '_')

            # Generate equipment list
            equipment = []

            # Add class equipment
            class_items = class_equipment.get(character_class, [])
            if not class_items:
                # Fallback for classes not explicitly defined
                class_items = [
                    {'name': 'Simple Weapon', 'type': 'weapon', 'category': 'simple'},
                    {'name': 'Explorer\'s Pack', 'type': 'gear', 'category': 'adventuring'}
                ]
            equipment.extend(class_items)

            # Add background equipment
            background_items = background_equipment.get(background, [])
            if not background_items:
                # Fallback for backgrounds not explicitly defined
                background_items = [
                    {'name': 'Common Clothes', 'type': 'clothing'},
                    {'name': 'Small Trinket', 'type': 'trinket'}
                ]
            equipment.extend(background_items)

            # Add starting gold based on background
            gold_by_background = {
                'acolyte': 15, 'criminal': 15, 'folk_hero': 10,
                'noble': 25, 'sage': 10, 'soldier': 10
            }
            starting_gold = gold_by_background.get(background, 10)
            character['currency']['gold'] = starting_gold

            return equipment

        def _generate_spells(self, character: Dict[str, Any]) -> Dict[str, Any]:
            """
            Generate spells for spellcasting classes.

            Args:
                character: Character dictionary

            Returns:
                Dictionary of spellcasting information
            """
            # Spellcasting classes and their spell lists
            spellcasting_classes = {
                'wizard': {
                    'spell_ability': 'intelligence',
                    'cantrips': 3,
                    'first_level_spells': 6,
                    'cantrip_list': [
                        'Mage Hand', 'Minor Illusion', 'Prestidigitation',
                        'Ray of Frost', 'Fire Bolt', 'Light', 'Shocking Grasp'
                    ],
                    'first_level_spell_list': [
                        'Burning Hands', 'Detect Magic', 'Mage Armor',
                        'Magic Missile', 'Shield', 'Sleep', 'Thunderwave'
                    ]
                },
                'cleric': {
                    'spell_ability': 'wisdom',
                    'cantrips': 3,
                    'first_level_spells': 'wisdom_mod',
                    'cantrip_list': [
                        'Guidance', 'Light', 'Sacred Flame', 'Spare the Dying',
                        'Thaumaturgy'
                    ],
                    'first_level_spell_list': [
                        'Bless', 'Cure Wounds', 'Detect Magic', 'Healing Word',
                        'Inflict Wounds', 'Shield of Faith'
                    ]
                }
            }

            # Check if character's class is a spellcaster
            character_class = character['class'].lower()
            if character_class not in spellcasting_classes or character['level'] < 1:
                return {
                    'is_spellcaster': False,
                    'cantrips': [],
                    'prepared_spells': [],
                    'spell_slots': {}
                }

            # Get spellcasting info for the class
            spell_info = spellcasting_classes[character_class]

            # Calculate spell ability modifier
            spell_ability = spell_info['spell_ability']
            ability_modifier = (character['abilities'][spell_ability] - 10) // 2

            # Determine number of cantrips and prepared spells
            cantrips_known = spell_info['cantrips']

            # Select cantrips
            cantrip_list = spell_info['cantrip_list']
            cantrips = random.sample(cantrip_list, min(cantrips_known, len(cantrip_list)))

            # Determine prepared spells
            if spell_info['first_level_spells'] == 'wisdom_mod':
                prepared_spell_count = max(1, ability_modifier + character['level'])
            else:
                prepared_spell_count = spell_info['first_level_spells']

            # Select prepared spells
            spell_list = spell_info['first_level_spell_list']
            prepared_spells = random.sample(
                spell_list,
                min(prepared_spell_count, len(spell_list))
            )

            # Calculate spell slots based on class and level
            spell_slots = self._calculate_spell_slots(character_class, character['level'])

            return {
                'is_spellcaster': True,
                'spell_ability': spell_ability,
                'spell_save_dc': 8 + ability_modifier + character['proficiency_bonus'],
                'spell_attack_modifier': ability_modifier + character['proficiency_bonus'],
                'cantrips': cantrips,
                'prepared_spells': prepared_spells,
                'spell_slots': spell_slots
            }
        # CoreAI2.py - CHUNK 9
        # Spell Slots and Backstory Generation

    def _calculate_spell_slots(self, character_class: str, level: int) -> Dict[str, int]:
        """
        Calculate spell slots for a given class and level.

        Args:
            character_class: Character's class
            level: Character's level

        Returns:
            Dictionary of spell slots by level
        """
        # Spell slot progression by class
        spell_slot_progression = {
            'wizard': {
                1: {1: 2},
                2: {1: 3},
                3: {1: 4, 2: 2},
                4: {1: 4, 2: 3},
                5: {1: 4, 2: 3, 3: 2}
            },
            'cleric': {
                1: {1: 2},
                2: {1: 3},
                3: {1: 4, 2: 2},
                4: {1: 4, 2: 3},
                5: {1: 4, 2: 3, 3: 2}
            }
        }

        # Normalize class input
        character_class = character_class.lower()

        # Get spell slots for the specific class and level
        class_progression = spell_slot_progression.get(character_class, {})
        level_slots = class_progression.get(min(level, 5), {})

        return level_slots

    def _generate_character_backstory(self, character: Dict[str, Any]) -> str:
        """
        Generate a rich backstory for the character using language integration.

        Args:
            character: Character dictionary

        Returns:
            Generated backstory text
        """
        try:
            # Use language integration if available
            language_integration = self._components.get('language_integration')
            if language_integration:
                try:
                    # Create a detailed prompt based on character attributes
                    race = character['race']
                    char_class = character['class']
                    background = character['background']
                    level = character['level']
                    personality = character.get('personality', {})
                    traits = personality.get('traits', [])

                    # Include dynamic elements in backstory generation
                    core_traits = []
                    if 'strength' in character['abilities'] and character['abilities']['strength'] >= 16:
                        core_traits.append("physically powerful")
                    elif 'strength' in character['abilities'] and character['abilities']['strength'] <= 8:
                        core_traits.append("physically weak")

                    if 'intelligence' in character['abilities'] and character['abilities']['intelligence'] >= 16:
                        core_traits.append("highly intelligent")
                    elif 'intelligence' in character['abilities'] and character['abilities']['intelligence'] <= 8:
                        core_traits.append("simple-minded")

                    # Add personality traits to prompt
                    if traits:
                        trait_desc = ", ".join(traits[:2])  # Use first two traits
                    else:
                        trait_desc = "mysterious past"

                    # Build prompt with character details
                    backstory_prompt = (
                        f"Generate a compelling backstory for a {race} {char_class} from a {background} "
                        f"background who is {trait_desc}. The character is level {level}. "
                        f"Include their motivation for adventuring, a key formative event, and "
                        f"potential future character development. Make the backstory unique and detailed."
                    )

                    if core_traits:
                        backstory_prompt += f" The character is {' and '.join(core_traits)}."

                    # Generate backstory using language system
                    text_gen = self._components.get('text_generation_adapter')
                    if text_gen:
                        backstory = text_gen.generate_text(
                            backstory_prompt,
                            max_length=300,
                            character_role="storyteller"
                        )
                        return backstory

                    # Fallback to basic narrative generation
                    response = language_integration.generate_description(
                        location_type="character_backstory",
                        specific_features=[race, char_class, background, f"Level {level}"]
                    )
                    return response.get('text', self._generate_fallback_backstory(character))

                except Exception as e:
                    logger.warning(f"Error using language integration for backstory: {e}")
                    return self._generate_fallback_backstory(character)
            else:
                return self._generate_fallback_backstory(character)

        except Exception as e:
            logger.warning(f"Backstory generation failed: {e}")
            return self._generate_fallback_backstory(character)

    def _generate_fallback_backstory(self, character: Dict[str, Any]) -> str:
        """
        Generate a more dynamic fallback backstory when language integration is unavailable.

        Args:
            character: Character dictionary

        Returns:
            Generated backstory text
        """
        race = character['race']
        char_class = character['class']
        background = character['background']

        # Get random personality traits for more variety
        personality = character.get('personality', {})
        traits = personality.get('traits', [])
        ideal = personality.get('ideals', ['seeking adventure'])
        bond = personality.get('bonds', ['mysterious heritage'])
        flaw = personality.get('flaws', ['trust issues'])

        # Character name for personalization
        name = character.get('name', 'The character')

        # Key background elements based on class and background
        class_elements = {
            'fighter': ['martial training', 'military service', 'combat prowess', 'battlefield experience'],
            'wizard': ['arcane studies', 'magical discovery', 'scholarly pursuits', 'ancient knowledge'],
            'rogue': ['street smarts', 'shadowy past', 'criminal connections', 'stealth expertise'],
            'cleric': ['divine calling', 'religious devotion', 'spiritual awakening', 'temple service'],
            'bard': ['musical talent', 'storytelling', 'artistic expression', 'performance'],
            'barbarian': ['tribal upbringing', 'wilderness survival', 'primal rage', 'physical might']
        }

        background_elements = {
            'acolyte': ['religious upbringing', 'spiritual guidance', 'temple service', 'divine intervention'],
            'criminal': ['troubled past', 'underworld connections', 'daring heists', 'narrow escapes'],
            'folk_hero': ['humble beginnings', 'heroic deed', 'standing against tyranny', 'community support'],
            'noble': ['privileged upbringing', 'family obligations', 'political intrigues', 'high expectations'],
            'soldier': ['military discipline', 'battlefield horrors', 'unit camaraderie', 'strategic thinking']
        }

        # Get random elements
        class_element = random.choice(class_elements.get(char_class.lower(), ['adventurous spirit']))
        bg_element = random.choice(background_elements.get(background.lower(), ['interesting past']))

        # Build a more dynamic backstory template
        templates = [
            f"{name} was born among the {race}s with {class_element}. {bg_element.capitalize()} shaped their early life. {random.choice(traits) if traits else 'They have always been resourceful'}. {name} seeks {random.choice(ideal) if isinstance(ideal, list) else ideal}, but struggles with {random.choice(flaw) if isinstance(flaw, list) else flaw}. Above all, {random.choice(bond) if isinstance(bond, list) else bond} drives them forward.",

            f"As a {race}, {name} had always felt {class_element} calling to them. {bg_element.capitalize()} was just the beginning of their journey. Their greatest strength is that {random.choice(traits) if traits else 'they never give up'}, though {random.choice(flaw) if isinstance(flaw, list) else flaw} sometimes holds them back. {name} dreams of {random.choice(ideal) if isinstance(ideal, list) else ideal}.",

            f"The story of {name} begins with {bg_element}. Being a {race} with {class_element} set them apart. {random.choice(traits) if traits else 'Their unique perspective'} has served them well in their adventures. Their deepest motivation is {random.choice(bond) if isinstance(bond, list) else bond}, though {random.choice(flaw) if isinstance(flaw, list) else flaw} remains a personal challenge.",

            f"{bg_element.capitalize()} marked {name}'s early years. Growing up as a {race}, they discovered {class_element} and knew they had found their calling. {random.choice(traits) if traits else 'Their determination'} has brought them far, and {random.choice(ideal) if isinstance(ideal, list) else ideal} keeps them going despite the obstacles.",

            f"{name} wasn't always a {char_class}. Their path began with {bg_element}, typical for many {race}s. However, {class_element} revealed their true potential. Now they venture forth guided by {random.choice(bond) if isinstance(bond, list) else bond}, striving to overcome {random.choice(flaw) if isinstance(flaw, list) else flaw}."
        ]

        return random.choice(templates)

    def _add_character_to_game_state(self, character: Dict[str, Any]) -> None:
        """
        Add the generated character to the game state.

        Args:
            character: Character dictionary to add
        """
        # Add to player party
        self.game_state['player_party'].append(character)

        # Update language integration context
        if self._components.get('language_integration'):
            try:
                self.language_integration.update_party(self.game_state['player_party'])
            except Exception as e:
                logger.error(f"Error updating party in language context: {e}")

        # Log character addition
        logger.info(f"Added {character['name']} to player party")
        # CoreAI2.py - CHUNK 10
        # Quest Generation and Encounter Methods

    def generate_quest(self, quest_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive quest using advanced language integration.

        Args:
            quest_parameters: Optional parameters to guide quest generation

        Returns:
            Generated quest dictionary
        """
        # Default quest parameters
        default_params = {
            'quest_type': None,  # Allows for random quest generation
            'difficulty': 'medium',
            'level': self._calculate_average_party_level(),
            'location': self.game_state.get('current_location', 'unknown'),
            'giver': None,
            'party_info': self._prepare_party_quest_context()
        }

        # Merge provided parameters with defaults
        if quest_parameters:
            default_params.update(quest_parameters)

        try:
            # Ensure language integration is available (lazy loading)
            if self.lazy_loading and not self._components.get('language_integration'):
                self._init_narrative_engine()

            # Use language integration to generate quest
            if self._components.get('language_integration'):
                quest_response = self.language_integration.generate_quest(
                    quest_type=default_params['quest_type'],
                    difficulty=default_params['difficulty'],
                    level=default_params['level'],
                    location=default_params['location'],
                    giver=default_params['giver'],
                    party_info=default_params['party_info']
                )

                # Parse quest JSON
                try:
                    quest_data = json.loads(quest_response.get('text', '{}'))
                except json.JSONDecodeError:
                    # Fallback to structured quest if JSON parsing fails
                    quest_data = {
                        'title': 'Mysterious Quest',
                        'description': quest_response.get('text', 'An undefined quest awaits'),
                        'type': default_params['quest_type'] or 'investigation',
                        'difficulty': default_params['difficulty'],
                        'level': default_params['level']
                    }
            else:
                # Create a dynamic quest without language integration
                quest_data = self._generate_fallback_quest(default_params)

            # Add additional quest metadata
            quest_data['id'] = f"quest_{len(self.game_state['active_quests']) + 1}"
            quest_data['status'] = 'active'
            quest_data['created_at'] = time.time()
            quest_data['location'] = default_params['location']

            # Add quest to game state
            self.game_state['active_quests'].append(quest_data)

            # Log quest generation
            logger.info(f"Generated quest: {quest_data['title']}")

            return quest_data

        except Exception as e:
            logger.error(f"Quest generation failed: {e}")
            return self._generate_fallback_quest(default_params)

    def _prepare_party_quest_context(self) -> Dict[str, Any]:
        """Prepare context about the party for quest generation."""
        # Get basic party information
        party = self.game_state["player_party"]

        if not party:
            return {}

        # Summarize party composition
        classes = {}
        races = {}
        level_sum = 0

        for character in party:
            # Count classes
            char_class = character.get('class', 'unknown')
            classes[char_class] = classes.get(char_class, 0) + 1

            # Count races
            race = character.get('race', 'unknown')
            races[race] = races.get(race, 0) + 1

            # Sum levels
            level_sum += character.get('level', 1)

        # Create party summary
        party_info = {
            'size': len(party),
            'average_level': level_sum / max(1, len(party)),
            'composition': {
                'classes': classes,
                'races': races
            },
            'resources': self.game_state.get('party_resources', {})
        }

        return party_info

    def _generate_fallback_quest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a dynamic fallback quest without language integration."""
        # Quest types with associated elements
        quest_types = {
            'retrieval': {
                'targets': ['ancient artifact', 'magical tome', 'rare herb', 'lost heirloom', 'stolen treasure'],
                'locations': ['deep cave', 'forgotten ruin', 'dense forest', 'abandoned temple', 'enemy stronghold'],
                'obstacles': ['dangerous monsters', 'puzzling traps', 'rival seekers', 'harsh environment',
                              'time limit']
            },
            'rescue': {
                'targets': ['kidnapped noble', 'lost child', 'captured merchant', 'imprisoned ally',
                            'stranded explorer'],
                'locations': ['bandit camp', 'monster lair', 'enemy fortress', 'wilderness', 'dungeon'],
                'obstacles': ['heavily guarded', 'maze-like layout', 'hostage situation', 'stealth required',
                              'tough negotiation']
            },
            'investigation': {
                'targets': ['mysterious disappearance', 'strange phenomenon', 'series of thefts', 'conspiracy',
                            'ancient mystery'],
                'locations': ['small town', 'noble quarter', 'wizard tower', 'merchant district', 'rural village'],
                'obstacles': ['reluctant witnesses', 'misleading clues', 'powerful suspects', 'time pressure',
                              'dangerous truth']
            },
            'protection': {
                'targets': ['important caravan', 'village elder', 'magical site', 'diplomatic envoy', 'rare creature'],
                'locations': ['trade route', 'village', 'sacred grove', 'border crossing', 'mountain pass'],
                'obstacles': ['planned ambush', 'betrayal from within', 'environmental hazards', 'multiple threats',
                              'limited resources']
            }
        }

        # Select quest type
        quest_type = params.get('quest_type')
        if not quest_type or quest_type not in quest_types:
            quest_type = random.choice(list(quest_types.keys()))

        # Get quest elements based on type
        elements = quest_types[quest_type]
        target = random.choice(elements['targets'])
        location = random.choice(elements['locations'])
        obstacle = random.choice(elements['obstacles'])

        # Determine difficulty-appropriate rewards
        difficulty = params.get('difficulty', 'medium')
        level = params.get('level', 1)

        if difficulty == 'easy':
            gold_reward = level * 25
            xp_reward = level * 50
        elif difficulty == 'medium':
            gold_reward = level * 50
            xp_reward = level * 100
        elif difficulty == 'hard':
            gold_reward = level * 100
            xp_reward = level * 200
        else:  # deadly
            gold_reward = level * 200
            xp_reward = level * 400

        # Chance for magic item based on difficulty
        magic_item = None
        magic_item_chance = {'easy': 0.1, 'medium': 0.3, 'hard': 0.5, 'deadly': 0.8}
        if random.random() < magic_item_chance.get(difficulty, 0.3):
            items = ['potion of healing', 'scroll of identify', '+1 weapon', 'bag of holding', 'cloak of protection']
            magic_item = random.choice(items)

        # Create rewards list
        rewards = ['Experience', f'{gold_reward} gold']
        if magic_item:
            rewards.append(magic_item)

        # Generate title
        title_templates = [
            f"The {target} of {location.title()}",
            f"{target.title()} in Peril",
            f"Danger and the {target.title()}",
            f"The {obstacle.title()}",
            f"A Quest for the {target.title()}"
        ]
        title = random.choice(title_templates)

        # Generate description
        description_templates = [
            f"You must find the {target} in the {location} despite {obstacle}.",
            f"The {target} has been spotted in the {location}. Be wary of {obstacle}.",
            f"Your quest involves the {target} within the {location}. Prepare to face {obstacle}.",
            f"Journey to the {location} to deal with the {target}, but beware of {obstacle}.",
            f"The {target} awaits in the {location}, but first you must overcome {obstacle}."
        ]
        description = random.choice(description_templates)

        # Create complete quest
        fallback_quest = {
            'title': title,
            'description': description,
            'type': quest_type,
            'difficulty': difficulty,
            'level': level,
            'rewards': rewards,
            'target': target,
            'location': params.get('location', location),
            'obstacle': obstacle,
            'status': 'active',
            'created_at': time.time()
        }

        # Add quest giver if provided
        if params.get('giver'):
            fallback_quest['giver'] = params['giver']

        return fallback_quest

    def generate_encounter(self, encounter_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a balanced and contextually appropriate encounter.

        Args:
            encounter_parameters: Optional parameters to guide encounter generation

        Returns:
            Generated encounter dictionary
        """
        # Default encounter parameters
        default_params = {
            'location_type': self.game_state.get('current_location', 'wilderness'),
            'difficulty': 'medium',
            'party_level': self._calculate_average_party_level(),
            'environment': None,
            'mood': 'neutral'
        }

        # Merge provided parameters with defaults
        if encounter_parameters:
            default_params.update(encounter_parameters)

        try:
            # Ensure needed components are loaded (lazy loading)
            if self.lazy_loading:
                if not self._components.get('language_integration'):
                    self._init_narrative_engine()
                if not self._components.get('encounter_generator'):
                    self._init_encounter_engine()

            # Generate encounter description using language integration
            description_response = {}
            if self._components.get('language_integration'):
                description_response = self.language_integration.generate_description(
                    location_id=default_params['location_type'],
                    time_of_day=self.game_state['world_time'].get('time_of_day', 'day'),
                    weather=self.game_state['world_time'].get('weather', 'clear'),
                    atmosphere=default_params['mood']
                )

            # Generate combat encounter using encounter generator
            combat_encounter = {}
            if self._components.get('encounter_generator'):
                combat_encounter = self.encounter_generator.create_encounter(
                    party_level=default_params['party_level'],
                    location_type=default_params['location_type'],
                    difficulty=default_params['difficulty']
                )
            else:
                # Fallback encounter generation
                combat_encounter = self._generate_fallback_encounter(default_params)

            # Combine description and encounter details
            description_text = description_response.get('text',
                                                        f"You encounter danger in this {default_params['location_type']}.")

            full_encounter = {
                'id': f"encounter_{len(self.game_state.get('encounter_history', [])) + 1}",
                'location': default_params['location_type'],
                'difficulty': default_params['difficulty'],
                'description': description_text,
                'environment_features': combat_encounter.get('environment_features', []),
                'monsters': combat_encounter.get('monsters', []),
                'treasure': combat_encounter.get('treasure', []),
                'experience_reward': combat_encounter.get('experience_reward', 0),
                'created_at': time.time(),
                'status': 'pending'
            }

            # Add to encounter history
            if 'encounter_history' not in self.game_state:
                self.game_state['encounter_history'] = []
            self.game_state['encounter_history'].append(full_encounter)

            # Log encounter generation
            logger.info(f"Generated encounter in {default_params['location_type']}")

            return full_encounter

        except Exception as e:
            logger.error(f"Encounter generation failed: {e}")
            # Fall back to basic encounter
            return self._generate_fallback_encounter(default_params)
        # CoreAI2.py - CHUNK 11
        # Fallback Encounter and Narrative Functions

    def _generate_fallback_encounter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback encounter when the encounter generator fails."""
        # Basic monster templates by challenge rating
        monster_templates = {
            'easy': {
                'hp': 10,
                'ac': 12,
                'attack_bonus': 3,
                'damage': '1d6+1',
                'xp': 25
            },
            'medium': {
                'hp': 30,
                'ac': 14,
                'attack_bonus': 4,
                'damage': '1d8+2',
                'xp': 100
            },
            'hard': {
                'hp': 60,
                'ac': 16,
                'attack_bonus': 6,
                'damage': '2d6+3',
                'xp': 450
            },
            'deadly': {
                'hp': 120,
                'ac': 18,
                'attack_bonus': 8,
                'damage': '3d8+4',
                'xp': 1100
            }
        }

        # Monster types by environment
        environment_monsters = {
            'forest': ['Wolf', 'Bandit', 'Bear', 'Giant Spider', 'Goblin'],
            'mountain': ['Eagle', 'Ogre', 'Orc', 'Hill Giant', 'Griffon'],
            'dungeon': ['Skeleton', 'Zombie', 'Ghoul', 'Goblin', 'Orc'],
            'urban': ['Bandit', 'Cultist', 'Spy', 'Thug', 'Guard'],
            'coastal': ['Merfolk', 'Sahuagin', 'Pirate', 'Giant Crab', 'Reef Shark'],
            'desert': ['Dust Mephit', 'Gnoll', 'Giant Scorpion', 'Mummy', 'Vulture'],
            'grassland': ['Goblin', 'Hobgoblin', 'Gnoll', 'Lion', 'Ogre'],
            'swamp': ['Lizardfolk', 'Bullywug', 'Crocodile', 'Troll', 'Black Dragon']
        }

        # Environment features
        environment_features = {
            'forest': ['Dense Foliage', 'Fallen Tree', 'Thick Undergrowth', 'Stream', 'Clearing'],
            'mountain': ['Rocky Terrain', 'Steep Slope', 'Narrow Ledge', 'Cave Entrance', 'Boulder Field'],
            'dungeon': ['Narrow Corridor', 'Pit Trap', 'Ancient Statue', 'Locked Door', 'Strange Symbols'],
            'urban': ['Market Stall', 'Alleyway', 'Fountain', 'Building', 'Sewers'],
            'coastal': ['Rocky Shore', 'Tidal Pool', 'Fishing Net', 'Shipwreck', 'Cliff Face'],
            'desert': ['Sand Dune', 'Oasis', 'Ruins', 'Mirage', 'Quicksand'],
            'grassland': ['Tall Grass', 'Small Hill', 'Campfire', 'Grazing Animals', 'Ancient Stone'],
            'swamp': ['Murky Water', 'Twisted Tree', 'Patch of Quicksand', 'Fog', 'Rotting Vegetation']
        }

        # Get parameters
        location_type = params.get('location_type', 'forest')
        difficulty = params.get('difficulty', 'medium')
        party_level = params.get('party_level', 1)
        party_size = len(self.game_state.get('player_party', [])) or 4

        # Normalize location type
        if location_type not in environment_monsters:
            location_type = 'forest'

        # Determine number of monsters based on difficulty
        if difficulty == 'easy':
            num_monsters = max(1, party_size - 1)
        elif difficulty == 'medium':
            num_monsters = party_size
        elif difficulty == 'hard':
            num_monsters = party_size + 1
        else:  # deadly
            num_monsters = party_size + 2

        # Scale based on party level
        if party_level >= 5:
            num_monsters = max(1, num_monsters - 1)  # Fewer but stronger monsters

        # Get monster template based on difficulty
        monster_template = monster_templates.get(difficulty, monster_templates['medium'])

        # Generate monsters
        monsters = []
        monster_types = environment_monsters.get(location_type, environment_monsters['forest'])
        total_xp = 0

        for _ in range(num_monsters):
            monster_type = random.choice(monster_types)

            # Scale monster stats based on party level
            level_multiplier = max(1, party_level / 3)

            monster = {
                'name': monster_type,
                'hp': int(monster_template['hp'] * level_multiplier),
                'ac': monster_template['ac'],
                'attack_bonus': monster_template['attack_bonus'],
                'damage': monster_template['damage'],
                'xp': int(monster_template['xp'] * level_multiplier),
                'environment': location_type
            }

            monsters.append(monster)
            total_xp += monster['xp']

        # Generate environment features
        features = []
        available_features = environment_features.get(location_type, [])
        if available_features:
            num_features = random.randint(1, 3)
            features = random.sample(available_features, min(num_features, len(available_features)))

        # Generate simple treasure
        treasure = []
        if difficulty in ['medium', 'hard', 'deadly'] or random.random() < 0.3:
            gold_amount = party_level * 10 * {'easy': 1, 'medium': 2, 'hard': 5, 'deadly': 10}[difficulty]
            treasure.append({'type': 'gold', 'amount': gold_amount})

            # Chance for a magic item
            if difficulty in ['hard', 'deadly'] or (difficulty == 'medium' and random.random() < 0.2):
                magic_items = ['Potion of Healing', 'Scroll of Magic Missile', '+1 Ammunition']
                treasure.append({'type': 'magic_item', 'item': random.choice(magic_items)})

        # Create complete encounter
        encounter = {
            'monsters': monsters,
            'environment_features': features,
            'treasure': treasure,
            'experience_reward': total_xp,
            'difficulty': difficulty,
            'location_type': location_type
        }

        return encounter

    def advance_narrative(self, narrative_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Advance the game's narrative with contextually rich progression.

        Args:
            narrative_parameters: Optional parameters to guide narrative progression

        Returns:
            Narrative progression details
        """
        # Default narrative parameters
        default_params = {
            'from_scene': self.game_state.get('current_location', 'unknown'),
            'to_scene': None,  # Allow for dynamic scene selection
            'mood': 'neutral',
            'time_passed': 'immediate'
        }

        # Merge provided parameters with defaults
        if narrative_parameters:
            default_params.update(narrative_parameters)

        try:
            # Ensure language integration is available (lazy loading)
            if self.lazy_loading and not self._components.get('language_integration'):
                self._init_narrative_engine()

            # Determine destination scene if not specified
            if not default_params['to_scene']:
                default_params['to_scene'] = self._select_next_narrative_scene()

            # Generate narrative transition
            transition_response = {}
            if self._components.get('language_integration'):
                transition_response = self.language_integration.generate_transition(
                    from_scene=default_params['from_scene'],
                    to_scene=default_params['to_scene'],
                    mood=default_params['mood'],
                    time_passed=default_params['time_passed']
                )
            else:
                # Create a basic transition response
                transition_response = {
                    'text': self._generate_fallback_transition(
                        default_params['from_scene'],
                        default_params['to_scene'],
                        default_params['mood'],
                        default_params['time_passed']
                    )
                }

            # Prepare narrative progression details
            narrative_progression = {
                'id': f"narrative_{len(self.game_state['story_beats']) + 1}",
                'from_scene': default_params['from_scene'],
                'to_scene': default_params['to_scene'],
                'description': transition_response.get('text', 'The story advances...'),
                'mood': default_params['mood'],
                'time_passed': default_params['time_passed'],
                'created_at': time.time()
            }

            # Update game state
            self.game_state['current_location'] = default_params['to_scene']
            self.game_state['story_beats'].append(narrative_progression)

            # Log narrative progression
            logger.info(f"Narrative advanced from {default_params['from_scene']} to {default_params['to_scene']}")

            return narrative_progression

        except Exception as e:
            logger.error(f"Narrative advancement failed: {e}")

            # Fallback narrative progression
            fallback_progression = {
                'id': f"narrative_{len(self.game_state['story_beats']) + 1}",
                'from_scene': default_params['from_scene'],
                'to_scene': default_params['to_scene'] or 'unknown destination',
                'description': self._generate_fallback_transition(
                    default_params['from_scene'],
                    default_params['to_scene'] or 'unknown destination',
                    default_params['mood'],
                    default_params['time_passed']
                ),
                'mood': default_params['mood'],
                'time_passed': default_params['time_passed'],
                'created_at': time.time()
            }

            self.game_state['story_beats'].append(fallback_progression)
            return fallback_progression

    def _select_next_narrative_scene(self) -> str:
        """Dynamically select the next narrative scene based on game state."""
        # Check for active quests with locations
        for quest in self.game_state['active_quests']:
            if 'location' in quest and quest['location'] != self.game_state.get('current_location'):
                return quest['location']

        # Check unexplored regions
        unexplored = self.game_state['exploration_state']['unexplored_regions']
        if unexplored:
            return random.choice(list(unexplored))

        # Fallback to a generic location
        generic_locations = ['village', 'forest', 'dungeon', 'mountain', 'road']
        return random.choice(generic_locations)

    def _generate_fallback_transition(self, from_scene: str, to_scene: str,
                                      mood: str, time_passed: str) -> str:
        """Generate a fallback narrative transition when language services are unavailable."""
        # Mood-based transition phrases
        mood_phrases = {
            'happy': ['joyfully', 'with high spirits', 'eagerly', 'with renewed energy'],
            'tense': ['cautiously', 'with watchful eyes', 'on high alert', 'with weapons ready'],
            'sad': ['solemnly', 'with heavy hearts', 'reluctantly', 'with lingering sorrow'],
            'mysterious': ['curiously', 'with growing intrigue', 'following cryptic signs', 'drawn by strange forces'],
            'urgent': ['hastily', 'racing against time', 'with urgent purpose', 'wasting no moment'],
            'neutral': ['steadily', 'with purpose', 'at a measured pace', 'deliberately']
        }

        # Time passage phrases
        time_phrases = {
            'immediate': ['immediately set out for', 'directly proceed to', 'waste no time heading to'],
            'short': ['soon arrive at', 'journey briefly to', 'make their way to'],
            'medium': ['spend several hours traveling to', 'journey through the day to reach', 'trek to'],
            'long': ['after a long journey arrive at', 'spend several days traveling to',
                     'endure a lengthy expedition to']
        }

        # Location type descriptions
        location_types = {
            'village': 'a small settlement of simple buildings and friendly faces',
            'town': 'a bustling town with shops and inns along cobbled streets',
            'forest': 'a dense woodland where sunlight filters through the canopy',
            'mountain': 'rugged terrain with steep paths and breathtaking vistas',
            'dungeon': 'a dark labyrinth of stone corridors and ancient secrets',
            'castle': 'a formidable structure with high walls and imposing towers',
            'cave': 'a natural formation of winding tunnels and echoing chambers',
            'road': 'a well-traveled path connecting distant places',
            'ruins': 'crumbling structures reclaimed by nature, hiding forgotten history',
            'swamp': 'a boggy wetland with murky waters and twisted vegetation'
        }

        # Extract location types from scene names
        from_type = from_scene.split('_')[0] if '_' in from_scene else from_scene
        to_type = to_scene.split('_')[0] if '_' in to_scene else to_scene

        # Get appropriate phrases
        mood_phrase = random.choice(mood_phrases.get(mood, mood_phrases['neutral']))
        time_phrase = random.choice(time_phrases.get(time_passed, time_phrases['short']))

        # Build transition
        from_desc = location_types.get(from_type, f"the area known as {from_scene}")
        to_desc = location_types.get(to_type, f"the destination called {to_scene}")

        # Party reference
        party_size = len(self.game_state.get('player_party', []))
        if party_size == 1:
            party_ref = "adventurer"
        elif party_size == 2:
            party_ref = "pair of adventurers"
        else:
            party_ref = "party"

        # Create varied transitions
        templates = [
            f"Leaving {from_desc}, the {party_ref} {mood_phrase} {time_phrase} {to_desc}.",
            f"The {party_ref} departs from {from_desc} and {mood_phrase} {time_phrase} {to_desc}.",
            f"Having concluded their business in {from_desc}, the {party_ref} {mood_phrase} {time_phrase} {to_desc}.",
            f"{mood_phrase.capitalize()}, the {party_ref} leaves {from_desc} behind and {time_phrase} {to_desc}.",
            f"The journey from {from_desc} to {to_desc} finds the {party_ref} traveling {mood_phrase}."
        ]

        return random.choice(templates)

        # CoreAI2.py - CHUNK 12
        # Game State Management and Utilities

        def _calculate_average_party_level(self) -> int:
            """
            Calculate the average level of the party.

            Returns:
                Average level (rounded)
            """
            party = self.game_state["player_party"]

            if not party:
                return 1

            total_level = sum(character.get('level', 1) for character in party)
            average = total_level / len(party)

            return max(1, round(average))

        def _calculate_hit_points(self, character: Dict[str, Any]) -> int:
            """
            Calculate a character's hit points.

            Args:
                character: Character dictionary

            Returns:
                Hit point total
            """
            # Get character data
            level = character.get('level', 1)
            char_class = character.get('class', 'fighter').lower()
            constitution = character.get('abilities', {}).get('constitution', 10)
            con_modifier = (constitution - 10) // 2

            # Hit dice by class
            hit_dice = {
                'barbarian': 12,
                'fighter': 10, 'paladin': 10, 'ranger': 10,
                'cleric': 8, 'druid': 8, 'monk': 8, 'rogue': 8, 'bard': 8,
                'sorcerer': 6, 'wizard': 6, 'warlock': 8
            }

            # Get hit die for class, default to d8 if not found
            hit_die = hit_dice.get(char_class, 8)

            # First level gets maximum hit points
            first_level_hp = hit_die + con_modifier

            # Remaining levels roll hit die (simplified: use average)
            average_roll = (hit_die // 2) + 1  # Average roll on a die
            remaining_levels_hp = (level - 1) * (average_roll + con_modifier)

            return max(1, first_level_hp + remaining_levels_hp)

        def _calculate_armor_class(self, character: Dict[str, Any]) -> int:
            """
            Calculate a character's armor class.

            Args:
                character: Character dictionary

            Returns:
                Armor Class (AC) value
            """
            # Get dexterity modifier
            dexterity = character.get('abilities', {}).get('dexterity', 10)
            dex_modifier = (dexterity - 10) // 2

            # Base AC is 10 + dex modifier
            base_ac = 10 + dex_modifier

            # Check for armor in equipment
            equipment = character.get('equipment', [])
            armor_types = {
                'Leather Armor': 11 + dex_modifier,
                'Studded Leather': 12 + dex_modifier,
                'Hide Armor': 12 + min(2, dex_modifier),
                'Chain Shirt': 13 + min(2, dex_modifier),
                'Scale Mail': 14 + min(2, dex_modifier),
                'Chain Mail': 16,
                'Plate': 18
            }

            # Check for shield (adds +2 AC)
            has_shield = any(item.get('name') == 'Shield' for item in equipment)
            shield_bonus = 2 if has_shield else 0

            # Find best armor
            ac = base_ac
            for item in equipment:
                item_name = item.get('name', '')
                if item_name in armor_types:
                    ac = max(ac, armor_types[item_name])

            # Check for class-specific AC calculations
            char_class = character.get('class', '').lower()

            # Barbarian unarmored defense: 10 + DEX + CON
            if char_class == 'barbarian' and ac == base_ac:
                con_modifier = (character.get('abilities', {}).get('constitution', 10) - 10) // 2
                ac = 10 + dex_modifier + con_modifier

            # Monk unarmored defense: 10 + DEX + WIS
            elif char_class == 'monk' and ac == base_ac:
                wis_modifier = (character.get('abilities', {}).get('wisdom', 10) - 10) // 2
                ac = 10 + dex_modifier + wis_modifier

            # Add shield bonus
            ac += shield_bonus

            return ac

        def save_campaign_state(self, filepath: Optional[str] = None) -> bool:
            """
            Save the current campaign state to a file.

            Args:
                filepath: Path to save the campaign state (defaults to auto-generated path)

            Returns:
                Boolean indicating successful save
            """
            try:
                # Generate default filepath if not provided
                if not filepath:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filepath = os.path.join(
                        self.database_path,
                        f"campaign_state_{timestamp}.json"
                    )

                # Prepare comprehensive save state
                save_state = {
                    'metadata': {
                        'timestamp': time.time(),
                        'campaign_version': '2.0',
                        'game_system': 'D&D 5e'
                    },
                    'game_state': self.game_state,
                    'campaign_settings': self.campaign_settings
                }

                # Attempt to save language integration context
                try:
                    if self._components.get('language_integration'):
                        context_filepath = filepath.replace('.json', '_context.json')
                        self.language_integration.save_context(context_filepath)
                        save_state['metadata']['context_file'] = context_filepath
                except Exception as e:
                    logger.warning(f"Could not save language context: {e}")

                # Write to file
                with open(filepath, 'w') as f:
                    json.dump(save_state, f, indent=2)

                logger.info(f"Campaign state saved to {filepath}")
                return True

            except Exception as e:
                logger.error(f"Failed to save campaign state: {e}")
                return False

        def load_campaign_state(self, filepath: str) -> bool:
            """
            Load a previously saved campaign state.

            Args:
                filepath: Path to the campaign state file

            Returns:
                Boolean indicating successful load
            """
            try:
                # Validate file exists
                if not os.path.exists(filepath):
                    logger.error(f"Campaign state file not found: {filepath}")
                    return False

                # Read campaign state
                with open(filepath, 'r') as f:
                    save_state = json.load(f)

                # Restore game state
                self.game_state = save_state.get('game_state', {})

                # Restore campaign settings
                self.campaign_settings.update(save_state.get('campaign_settings', {}))

                # Attempt to load language integration context
                context_file = save_state.get('metadata', {}).get('context_file')
                if context_file and os.path.exists(context_file):
                    try:
                        # Ensure language integration is loaded
                        if self.lazy_loading and not self._components.get('language_integration'):
                            self._init_narrative_engine()

                        if self._components.get('language_integration'):
                            self.language_integration.load_context(context_file)
                    except Exception as e:
                        logger.warning(f"Could not load language context: {e}")

                # Reinitialize components with loaded state
                self._reinitialize_game_state()

                logger.info(f"Campaign state loaded from {filepath}")
                return True

            except Exception as e:
                logger.error(f"Failed to load campaign state: {e}")
                return False

        def _reinitialize_game_state(self):
            """
            Reinitialize game components after loading a saved state.
            Ensures all components are properly synchronized.
            """
            # Reinitialize player party
            if self.game_state.get('player_party'):
                try:
                    # Update language integration with loaded party
                    if self._components.get('language_integration'):
                        self.language_integration.update_party(self.game_state['player_party'])
                except Exception as e:
                    logger.warning(f"Could not update party in language context: {e}")

            # Restore world time
            world_time = self.game_state.get('world_time', {})
            try:
                if self._components.get('language_integration'):
                    self.language_integration.update_world_state(
                        time_of_day=world_time.get('time_of_day', 'day'),
                        weather=world_time.get('weather', 'clear')
                    )
            except Exception as e:
                logger.warning(f"Could not update world state: {e}")

        def update_world_state(self,
                               time_of_day: Optional[str] = None,
                               weather: Optional[str] = None,
                               significant_events: Optional[List[str]] = None) -> None:
            """
            Update the game world's state with new information.

            Args:
                time_of_day: Current time of day
                weather: Current weather conditions
                significant_events: List of notable events
            """
            try:
                # Update world time in game state
                current_time = self.game_state['world_time']

                if time_of_day:
                    current_time['time_of_day'] = time_of_day

                if weather:
                    current_time['weather'] = weather

                # Track significant events
                if significant_events:
                    if 'world_events' not in self.game_state:
                        self.game_state['world_events'] = []

                    self.game_state['world_events'].extend(significant_events)

                # Update language integration
                try:
                    if self._components.get('language_integration'):
                        self.language_integration.update_world_state(
                            time_of_day=time_of_day,
                            weather=weather
                        )
                except Exception as e:
                    logger.warning(f"Could not update language integration world state: {e}")

                # Log world state changes
                logger.info(f"World state updated: {time_of_day or 'unchanged'}, {weather or 'unchanged'}")

            except Exception as e:
                logger.error(f"Failed to update world state: {e}")
        # CoreAI2.py - CHUNK 13
        # Action Processing and Utility Methods

    def process_player_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a player's action with comprehensive system integration.

        Args:
            action: Dictionary describing the player's action

        Returns:
            Result of the action processing
        """
        # Validate input
        if not isinstance(action, dict):
            logger.error(f"Invalid action type: {type(action)}")
            return {
                'status': 'error',
                'message': "Action must be a dictionary"
            }

        try:
            # Validate action type
            action_type = action.get('type', '').lower()

            # Define valid action types
            valid_action_types = {
                'combat': self._process_combat_action,
                'skill_check': self._process_skill_check,
                'dialogue': self._process_dialogue_action,
                'exploration': self._process_exploration_action,
                'quest': self._process_quest_action
            }

            # Process action using appropriate method
            if action_type in valid_action_types:
                # Ensure required components are loaded (lazy loading)
                if self.lazy_loading:
                    if action_type == 'combat' and not self._components.get('combat_manager'):
                        self._init_combat_engine()
                    elif action_type == 'dialogue' and not self._components.get('language_integration'):
                        self._init_narrative_engine()

                # Process the action
                return valid_action_types[action_type](action)
            else:
                logger.warning(f"Unhandled action type: {action_type}")
                return {
                    'status': 'error',
                    'message': f"Unknown action type: {action_type}. "
                               f"Valid types are: {', '.join(valid_action_types.keys())}"
                }

        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Error processing player action: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Unexpected error processing action: {str(e)}"
            }

    def _process_combat_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a combat-related action.

        Args:
            action: Combat action details

        Returns:
            Combat action resolution
        """
        try:
            # Use combat manager to resolve action
            combat_manager = self._components.get('combat_manager')
            if combat_manager:
                result = combat_manager.process_action(action)
            else:
                return {
                    'status': 'error',
                    'message': "Combat system not available"
                }

            # Generate narrative description using language integration
            language_integration = self._components.get('language_integration')
            if language_integration:
                try:
                    narrative_description = language_integration.generate_combat(
                        action_type=action.get('action_type', 'attack'),
                        outcome=action.get('outcome', 'unknown'),
                        attacker=action.get('attacker', 'Character'),
                        defender=action.get('defender', 'Enemy'),
                        weapon=action.get('weapon'),
                        damage_amount=action.get('damage')
                    )
                    result['narrative_description'] = narrative_description.get('text', '')
                except Exception as e:
                    logger.warning(f"Could not generate combat narrative: {e}")
                    # Create a basic combat description
                    result['narrative_description'] = self._create_basic_combat_description(action)

            return result

        except Exception as e:
            logger.error(f"Combat action processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _create_basic_combat_description(self, action: Dict[str, Any]) -> str:
        """Create a basic combat description when language integration fails."""
        attacker = action.get('attacker', 'The character')
        defender = action.get('defender', 'the enemy')
        action_type = action.get('action_type', 'attack')
        outcome = action.get('outcome', 'unknown')
        weapon = action.get('weapon', 'weapon')
        damage = action.get('damage', 0)

        # Basic description templates
        if action_type == 'attack':
            if outcome == 'hit':
                return f"{attacker} strikes {defender} with their {weapon}, dealing {damage} damage."
            else:
                return f"{attacker} attacks {defender} with their {weapon}, but misses."
        elif action_type == 'spell':
            spell = action.get('spell', 'spell')
            if outcome == 'hit':
                return f"{attacker} casts {spell} at {defender}, dealing {damage} damage."
            else:
                return f"{attacker} casts {spell} at {defender}, but it has no effect."
        elif action_type == 'ability':
            ability = action.get('ability', 'special ability')
            return f"{attacker} uses {ability} against {defender}."
        else:
            return f"{attacker} performs a combat action against {defender}."

    def _process_skill_check(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a skill check action.

        Args:
            action: Skill check action details

        Returns:
            Skill check resolution
        """
        try:
            # Ensure action resolver is available
            action_resolver = self._components.get('action_resolver')
            if not action_resolver:
                if self.lazy_loading:
                    self._init_combat_engine()
                    action_resolver = self._components.get('action_resolver')
                else:
                    return {
                        'status': 'error',
                        'message': "Action resolver not available"
                    }

            # Get skill check parameters
            character_id = action.get('character_id')
            skill = action.get('skill', 'perception')
            difficulty = action.get('difficulty', 10)
            advantage = action.get('advantage', False)
            disadvantage = action.get('disadvantage', False)

            # Find character
            character = None
            for char in self.game_state['player_party']:
                if char.get('id') == character_id:
                    character = char
                    break

            if not character:
                return {
                    'status': 'error',
                    'message': f"Character with ID {character_id} not found"
                }

            # Resolve skill check
            result = action_resolver.resolve_skill_check(
                character, skill, difficulty, advantage, disadvantage
            )

            # Add narrative description
            if self._components.get('language_integration'):
                try:
                    # Determine success/failure and skill type for better description
                    success = result.get('success', False)
                    critical_success = result.get('critical_success', False)
                    critical_failure = result.get('critical_failure', False)

                    # Create context for more dynamic description
                    context = {
                        'character': character.get('name', 'The character'),
                        'skill': skill,
                        'roll': result.get('roll', 0),
                        'total': result.get('total', 0),
                        'difficulty': difficulty,
                        'success': success,
                        'critical_success': critical_success,
                        'critical_failure': critical_failure
                    }

                    # Generate description based on language integration
                    narrative = self._generate_skill_check_narrative(context)
                    result['narrative'] = narrative
                except Exception as e:
                    logger.warning(f"Could not generate skill check narrative: {e}")

            return result

        except Exception as e:
            logger.error(f"Skill check processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _generate_skill_check_narrative(self, context: Dict[str, Any]) -> str:
        """Generate a narrative description for a skill check result."""
        character = context.get('character', 'The character')
        skill = context.get('skill', 'the skill')
        roll = context.get('roll', 0)
        total = context.get('total', 0)
        difficulty = context.get('difficulty', 10)
        success = context.get('success', False)
        critical_success = context.get('critical_success', False)
        critical_failure = context.get('critical_failure', False)

        # Skill-specific verbs for more varied descriptions
        skill_verbs = {
            'acrobatics': ['tumbles', 'flips', 'maneuvers'],
            'animal handling': ['calms', 'approaches', 'interacts with'],
            'arcana': ['studies', 'analyzes', 'examines'],
            'athletics': ['climbs', 'jumps', 'lifts'],
            'deception': ['lies', 'deceives', 'misleads'],
            'history': ['recalls', 'remembers', 'recollects'],
            'insight': ['reads', 'understands', 'interprets'],
            'intimidation': ['threatens', 'intimidates', 'pressures'],
            'investigation': ['searches', 'examines', 'investigates'],
            'medicine': ['treats', 'examines', 'diagnoses'],
            'nature': ['identifies', 'recognizes', 'understands'],
            'perception': ['notices', 'spots', 'observes'],
            'performance': ['entertains', 'performs', 'impresses'],
            'persuasion': ['convinces', 'persuades', 'sways'],
            'religion': ['recalls', 'remembers', 'understands'],
            'sleight of hand': ['manipulates', 'pilfers', 'conceals'],
            'stealth': ['hides', 'sneaks', 'moves silently'],
            'survival': ['tracks', 'navigates', 'forages']
        }

        # Get appropriate verb for the skill
        verbs = skill_verbs.get(skill.lower(), ['attempts'])
        verb = random.choice(verbs)

        # Generate description based on outcome
        if critical_success:
            descriptions = [
                f"{character} masterfully {verb} with exceptional skill, rolling a natural 20 for a total of {total}!",
                f"With incredible finesse, {character} {verb} flawlessly, achieving a critical success!",
                f"An outstanding display of skill as {character} {verb} perfectly, rolling a natural 20!"
            ]
        elif critical_failure:
            descriptions = [
                f"{character} catastrophically fails to {verb}, rolling a natural 1!",
                f"Despite their best efforts, {character} fails miserably as they attempt to {verb}, rolling a natural 1!",
                f"It couldn't have gone worse as {character} critically fails to {verb}!"
            ]
        elif success:
            descriptions = [
                f"{character} successfully {verb}, rolling a {roll} for a total of {total}, meeting the DC of {difficulty}.",
                f"With skill and precision, {character} {verb} successfully with a total of {total}.",
                f"{character}'s attempt to {verb} succeeds with a total of {total} against a DC of {difficulty}."
            ]
        else:
            descriptions = [
                f"{character} fails to {verb}, rolling a {roll} for a total of {total}, not meeting the DC of {difficulty}.",
                f"Despite their efforts, {character} fails to {verb} with a total of {total}.",
                f"{character}'s attempt to {verb} falls short with a total of {total} against a DC of {difficulty}."
            ]

        return random.choice(descriptions)

    # CoreAI2.py - CHUNK 14
    # More Action Processing Methods

    def _process_dialogue_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dialogue interaction.

        Args:
            action: Dialogue action details

        Returns:
            Dialogue interaction result
        """
        try:
            # Ensure language integration is available
            language_integration = self._components.get('language_integration')
            if not language_integration:
                if self.lazy_loading:
                    self._init_narrative_engine()
                    language_integration = self._components.get('language_integration')
                else:
                    return {
                        'status': 'error',
                        'message': "Dialogue system not available"
                    }

            # Get dialogue parameters
            npc_id = action.get('npc_id')
            message = action.get('message', '')
            topic = action.get('topic')

            # Check if NPC exists
            if npc_id not in language_integration.context.npcs:
                # Check if NPC is in game state
                npc_found = False
                for npc_data in self.game_state.get('notable_npcs', {}).values():
                    if npc_data.get('id') == npc_id:
                        # Register NPC with language integration
                        language_integration.register_npc(npc_id, npc_data)
                        npc_found = True
                        break

                if not npc_found:
                    # Create a basic NPC if not found
                    new_npc = {
                        'id': npc_id,
                        'name': action.get('npc_name', f"NPC-{npc_id}"),
                        'type': action.get('npc_type', 'commoner'),
                        'race': action.get('npc_race', 'human'),
                        'attitude': action.get('npc_attitude', 'neutral'),
                        'current_location': self.game_state.get('current_location')
                    }
                    language_integration.register_npc(npc_id, new_npc)

                    # Add to game state
                    if 'notable_npcs' not in self.game_state:
                        self.game_state['notable_npcs'] = {}
                    self.game_state['notable_npcs'][npc_id] = new_npc

            # Generate dialogue response
            dialogue_response = language_integration.generate_dialogue(
                npc_id=npc_id,
                player_text=message,
                topic=topic
            )

            # Extract response
            response_text = dialogue_response.get('text', f"The NPC responds to your message.")

            # Add interaction to game state
            self._add_interaction("dialogue", f"Conversation with {npc_id} about {topic or 'general topics'}", [npc_id])

            return {
                'status': 'success',
                'dialogue': response_text,
                'npc_id': npc_id,
                'topic': topic
            }

        except Exception as e:
            logger.error(f"Dialogue action processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _add_interaction(self, interaction_type: str, description: str, entities_involved: List[str] = None) -> None:
        """Add an interaction to the game state."""
        if entities_involved is None:
            entities_involved = []

        # Create interaction record
        interaction = {
            'type': interaction_type,
            'description': description,
            'entities': entities_involved,
            'location': self.game_state.get('current_location'),
            'time': time.time()
        }

        # Add to interaction history
        if 'interaction_history' not in self.game_state:
            self.game_state['interaction_history'] = []
        self.game_state['interaction_history'].append(interaction)

        # Update language integration
        if self._components.get('language_integration'):
            try:
                self.language_integration.add_interaction(
                    interaction_type,
                    description,
                    entities_involved
                )
            except Exception as e:
                logger.warning(f"Failed to add interaction to language context: {e}")

    def _process_exploration_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an exploration-related action.

        Args:
            action: Exploration action details

        Returns:
            Exploration action resolution
        """
        try:
            # Ensure language integration is available
            language_integration = self._components.get('language_integration')
            if not language_integration:
                if self.lazy_loading:
                    self._init_narrative_engine()
                    language_integration = self._components.get('language_integration')
                else:
                    return {
                        'status': 'error',
                        'message': "Exploration system not available"
                    }

            # Get exploration parameters
            location = action.get('location', self.game_state.get('current_location', 'unknown'))
            exploration_type = action.get('exploration_type', 'observe')  # observe, search, interact
            target = action.get('target')  # Specific feature to explore

            # Generate description based on exploration type
            description_response = None

            if exploration_type == 'observe':
                # General observation of the area
                description_response = language_integration.generate_description(
                    location_id=location,
                    time_of_day=self.game_state['world_time'].get('time_of_day', 'day'),
                    weather=self.game_state['world_time'].get('weather', 'clear')
                )

            elif exploration_type == 'search':
                # Detailed search of the area or specific feature
                specific_features = [target] if target else None
                atmosphere = 'investigative'

                description_response = language_integration.generate_description(
                    location_id=location,
                    time_of_day=self.game_state['world_time'].get('time_of_day', 'day'),
                    weather=self.game_state['world_time'].get('weather', 'clear'),
                    specific_features=specific_features,
                    atmosphere=atmosphere
                )

                # Add chance to discover something
                discovery = self._generate_random_discovery(location, target)
                if discovery:
                    # Add discovery to response
                    description_text = description_response.get('text', '')
                    description_response['text'] = f"{description_text}\n\n{discovery}"

            elif exploration_type == 'interact':
                # Interaction with a specific feature
                if not target:
                    return {
                        'status': 'error',
                        'message': "No target specified for interaction"
                    }

                # Create context for interaction
                specific_features = [target]
                atmosphere = 'focused'

                description_response = language_integration.generate_description(
                    location_id=location,
                    time_of_day=self.game_state['world_time'].get('time_of_day', 'day'),
                    weather=self.game_state['world_time'].get('weather', 'clear'),
                    specific_features=specific_features,
                    atmosphere=atmosphere
                )

                # Check for special interactions
                interaction_result = self._handle_special_interaction(location, target)
                if interaction_result:
                    # Add interaction result to response
                    description_text = description_response.get('text', '')
                    description_response['text'] = f"{description_text}\n\n{interaction_result}"

            # Extract description
            description_text = description_response.get('text', f"You explore the {location}.")

            # Mark location as discovered if not already
            if 'discovered_locations' not in self.game_state['exploration_state']:
                self.game_state['exploration_state']['discovered_locations'] = set()
            self.game_state['exploration_state']['discovered_locations'].add(location)

            # Remove from unexplored if it was there
            if location in self.game_state['exploration_state'].get('unexplored_regions', set()):
                self.game_state['exploration_state']['unexplored_regions'].remove(location)

            # Add exploration to interaction history
            self._add_interaction("exploration",
                                  f"Explored {location}" + (f" - {target}" if target else ""),
                                  [])

            return {
                'status': 'success',
                'description': description_text,
                'location': location,
                'exploration_type': exploration_type,
                'target': target
            }

        except Exception as e:
            logger.error(f"Exploration action processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _generate_random_discovery(self, location: str, target: str = None) -> Optional[str]:
        """Generate a random discovery when searching an area."""
        # Chance of discovery based on location type
        location_type = location.split('_')[0] if '_' in location else location

        # Discovery chance by location type
        discovery_chances = {
            'dungeon': 0.6,
            'ruins': 0.5,
            'cave': 0.5,
            'forest': 0.4,
            'mountain': 0.3,
            'town': 0.2,
            'village': 0.2,
            'road': 0.1
        }

        discovery_chance = discovery_chances.get(location_type, 0.3)

        # Increase chance if searching a specific target
        if target:
            discovery_chance += 0.2

        # Roll for discovery
        if random.random() > discovery_chance:
            return None

        # Types of discoveries by location
        discovery_types = {
            'dungeon': ['hidden door', 'secret compartment', 'ancient inscription', 'trap', 'hidden treasure'],
            'ruins': ['buried artifact', 'hidden chamber', 'faded mural', 'ancient coins', 'broken statue'],
            'cave': ['unusual rock formation', 'mineral deposit', 'small underground spring', 'fossilized remains',
                     'hidden crevice'],
            'forest': ['rare herb', 'animal tracks', 'unusual plant', 'abandoned shelter', 'hidden clearing'],
            'mountain': ['cave entrance', 'unusual rock formation', 'abandoned mine', 'scenic vista',
                         'mountain spring'],
            'town': ['dropped coin', 'useful information', 'discarded item', 'hidden alley', 'unusual shop'],
            'village': ['local gossip', 'useful tool', 'friendly animal', 'hidden garden', 'forgotten shrine'],
            'road': ['dropped item', 'fresh tracks', 'road marker', 'abandoned cart', 'roadside shrine']
        }

        # Get available discoveries for this location
        available_discoveries = discovery_types.get(location_type,
                                                    ['unusual item', 'hidden feature', 'interesting detail'])

        # Select a discovery
        discovery_type = random.choice(available_discoveries)

        # Generate description
        discovery_descriptions = [
            f"Your search reveals {discovery_type}.",
            f"Hidden from casual observation, you discover {discovery_type}.",
            f"Your careful search uncovers {discovery_type}.",
            f"You find {discovery_type} that others have overlooked."
        ]

        return random.choice(discovery_descriptions)

    def _handle_special_interaction(self, location: str, target: str) -> Optional[str]:
        """Handle special interactions with specific objects."""
        # Some objects might trigger special events or provide information
        special_targets = {
            'ancient statue': [
                "As you examine the statue, you notice strange symbols etched into its base.",
                "The statue seems to be pointing in a specific direction, perhaps indicating something important.",
                "You find a small hidden compartment in the statue's base."
            ],
            'bookshelf': [
                "Among the dusty tomes, you find a book that stands out from the rest.",
                "A loose book reveals a secret compartment behind the shelf.",
                "One of the books contains a folded map tucked between its pages."
            ],
            'fountain': [
                "The water in the fountain has a strange, magical shimmer.",
                "You notice unusual coins at the bottom of the fountain.",
                "The fountain bears inscriptions describing its magical properties."
            ],
            'altar': [
                "The altar radiates a faint magical energy.",
                "Ancient religious symbols cover the altar's surface.",
                "You feel a strange compulsion when touching the altar."
            ],
            'mysterious door': [
                "The door is locked, but you notice strange markings around the frame.",
                "You feel a cold draft coming from behind the door.",
                "The door seems to be magically sealed."
            ]
        }

        normalized_target = target.lower()

        # Check for special target
        for special_target, responses in special_targets.items():
            if special_target in normalized_target:
                return random.choice(responses)

        # Generic interactions for common objects
        generic_targets = {
            'door': ["The door is {door_state}.", "You examine the door's construction."],
            'chest': ["The chest is {chest_state}.", "You inspect the chest carefully."],
            'table': ["Various items are scattered across the table.", "The table is {table_state}."],
            'window': ["Through the window, you can see {window_view}.", "The window is {window_state}."],
            'bed': ["The bed is {bed_state}.", "You examine the bed and surrounding area."],
            'chair': ["The chair is {chair_state}.", "It's a fairly ordinary chair."],
            'painting': ["The painting depicts {painting_subject}.", "You study the painting closely."],
            'book': ["The book contains information about {book_subject}.", "You flip through some pages of the book."]
        }

        # Fill in template variables
        for generic_target, templates in generic_targets.items():
            if generic_target in normalized_target:
                template = random.choice(templates)

                # Replace template variables
                if '{door_state}' in template:
                    door_states = ['locked', 'unlocked', 'slightly ajar', 'firmly shut', 'stuck', 'reinforced']
                    template = template.replace('{door_state}', random.choice(door_states))

                if '{chest_state}' in template:
                    chest_states = ['locked', 'unlocked', 'empty', 'filled with old clothes', 'trapped',
                                    'partially damaged']
                    template = template.replace('{chest_state}', random.choice(chest_states))

                if '{table_state}' in template:
                    table_states = ['dusty', 'clean', 'sturdy', 'wobbly', 'ornately carved', 'simple and functional']
                    template = template.replace('{table_state}', random.choice(table_states))

                if '{window_view}' in template:
                    location_type = location.split('_')[0] if '_' in location else location
                    views = {
                        'dungeon': ['darkness', 'another chamber', 'a corridor'],
                        'town': ['busy streets', 'other buildings', 'a marketplace'],
                        'forest': ['dense trees', 'a clearing', 'wildlife'],
                        'mountain': ['rocky slopes', 'a valley below', 'other peaks']
                    }
                    view_options = views.get(location_type, ['the surrounding area'])
                    template = template.replace('{window_view}', random.choice(view_options))

                if '{window_state}' in template:
                    window_states = ['open', 'closed', 'broken', 'stained glass', 'barred', 'dusty']
                    template = template.replace('{window_state}', random.choice(window_states))

                if '{bed_state}' in template:
                    bed_states = ['neatly made', 'unmade', 'dusty', 'comfortable-looking', 'old and worn',
                                  'recently used']
                    template = template.replace('{bed_state}', random.choice(bed_states))

                if '{chair_state}' in template:
                    chair_states = ['wooden', 'comfortable', 'broken', 'ornately carved', 'simple', 'padded']
                    template = template.replace('{chair_state}', random.choice(chair_states))

                if '{painting_subject}' in template:
                    subjects = ['a landscape', 'a portrait', 'a battle scene', 'a mythological scene',
                                'abstract shapes', 'a still life']
                    template = template.replace('{painting_subject}', random.choice(subjects))

                if '{book_subject}' in template:
                    subjects = ['history', 'magic', 'local legends', 'flora and fauna', 'religious teachings', 'poetry']
                    template = template.replace('{book_subject}', random.choice(subjects))

                return template

        # Default response if no special interaction found
        return None
        # CoreAI2.py - CHUNK 15
        # Quest Actions and Final Methods

    def _process_quest_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a quest-related action.

        Args:
            action: Quest action details

        Returns:
            Quest action resolution
        """
        try:
            quest_action = action.get('action', '').lower()

            if quest_action == 'accept':
                # Generate a new quest
                quest_params = action.get('parameters', {})
                new_quest = self.generate_quest(quest_params)
                return {
                    'status': 'success',
                    'quest': new_quest
                }

            elif quest_action == 'complete':
                # Mark quest as completed
                quest_id = action.get('quest_id')
                completed = False

                for quest in self.game_state['active_quests']:
                    if quest['id'] == quest_id:
                        quest['status'] = 'completed'

                        # Move to completed quests
                        self.game_state['completed_quests'].append(quest)
                        self.game_state['active_quests'].remove(quest)

                        # Award rewards if specified
                        self._award_quest_rewards(quest)

                        completed = True
                        break

                if completed:
                    return {
                        'status': 'success',
                        'message': f"Quest {quest_id} completed"
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"Quest {quest_id} not found"
                    }

            elif quest_action == 'abandon':
                # Abandon a quest
                quest_id = action.get('quest_id')
                abandoned = False

                for quest in self.game_state['active_quests']:
                    if quest['id'] == quest_id:
                        quest['status'] = 'abandoned'

                        # Remove from active quests
                        self.game_state['active_quests'].remove(quest)

                        abandoned = True
                        break

                if abandoned:
                    return {
                        'status': 'success',
                        'message': f"Quest {quest_id} abandoned"
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"Quest {quest_id} not found"
                    }

            elif quest_action == 'update':
                # Update quest progress
                quest_id = action.get('quest_id')
                progress = action.get('progress', 0)
                note = action.get('note', '')

                for quest in self.game_state['active_quests']:
                    if quest['id'] == quest_id:
                        # Update progress
                        quest['progress'] = progress

                        # Add note if provided
                        if note:
                            if 'notes' not in quest:
                                quest['notes'] = []
                            quest['notes'].append({
                                'text': note,
                                'timestamp': time.time()
                            })

                        return {
                            'status': 'success',
                            'message': f"Quest {quest_id} updated"
                        }

                return {
                    'status': 'error',
                    'message': f"Quest {quest_id} not found"
                }

            elif quest_action == 'list':
                # List active quests
                active_quests = self.game_state['active_quests']
                return {
                    'status': 'success',
                    'active_quests': active_quests
                }

            elif quest_action == 'details':
                # Get details of a specific quest
                quest_id = action.get('quest_id')

                # Search in active quests
                for quest in self.game_state['active_quests']:
                    if quest['id'] == quest_id:
                        return {
                            'status': 'success',
                            'quest': quest
                        }

                # Search in completed quests
                for quest in self.game_state.get('completed_quests', []):
                    if quest['id'] == quest_id:
                        return {
                            'status': 'success',
                            'quest': quest
                        }

                return {
                    'status': 'error',
                    'message': f"Quest {quest_id} not found"
                }
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown quest action: {quest_action}"
                }

        except Exception as e:
            logger.error(f"Quest action processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _award_quest_rewards(self, quest: Dict[str, Any]) -> None:
        """Award rewards for completing a quest."""
        # Get rewards
        rewards = quest.get('rewards', [])

        for reward in rewards:
            if isinstance(reward, str):
                # Parse the reward string
                if 'gold' in reward.lower():
                    # Extract gold amount
                    try:
                        amount = int(''.join(c for c in reward if c.isdigit()))
                        self.game_state['party_resources']['gold'] = self.game_state['party_resources'].get('gold',
                                                                                                            0) + amount
                        logger.info(f"Awarded {amount} gold for quest {quest['id']}")
                    except:
                        # Couldn't parse gold amount, add default
                        self.game_state['party_resources']['gold'] = self.game_state['party_resources'].get('gold',
                                                                                                            0) + 50
                        logger.info(f"Awarded default 50 gold for quest {quest['id']}")

                elif 'experience' in reward.lower() or 'xp' in reward.lower():
                    # Award XP to all party members
                    # Extract XP amount if available
                    try:
                        amount = int(''.join(c for c in reward if c.isdigit()))
                    except:
                        # Default based on quest difficulty
                        difficulty = quest.get('difficulty', 'medium')
                        level = quest.get('level', 1)

                        # XP by difficulty and level
                        xp_multipliers = {'easy': 50, 'medium': 100, 'hard': 200, 'deadly': 400}
                        amount = level * xp_multipliers.get(difficulty, 100)

                    # Award XP to all party members
                    for character in self.game_state['player_party']:
                        character['experience'] = character.get('experience', 0) + amount

                    logger.info(f"Awarded {amount} XP per character for quest {quest['id']}")

                elif 'item' in reward.lower() or any(item_type in reward.lower() for item_type in
                                                     ['potion', 'scroll', 'weapon', 'armor', 'ring', 'wand']):
                    # Add item to party resources
                    if 'magical_items' not in self.game_state['party_resources']:
                        self.game_state['party_resources']['magical_items'] = []

                    self.game_state['party_resources']['magical_items'].append(reward)
                    logger.info(f"Awarded item '{reward}' for quest {quest['id']}")
            elif isinstance(reward, dict):
                # Handle structured rewards
                reward_type = reward.get('type', '').lower()

                if reward_type == 'gold':
                    amount = reward.get('amount', 50)
                    self.game_state['party_resources']['gold'] = self.game_state['party_resources'].get('gold',
                                                                                                        0) + amount
                    logger.info(f"Awarded {amount} gold for quest {quest['id']}")

                elif reward_type == 'experience' or reward_type == 'xp':
                    amount = reward.get('amount', 100)

                    # Award XP to all party members
                    for character in self.game_state['player_party']:
                        character['experience'] = character.get('experience', 0) + amount

                    logger.info(f"Awarded {amount} XP per character for quest {quest['id']}")

                elif reward_type == 'item':
                    item = reward.get('item', 'Unknown Item')

                    # Add item to party resources
                    if 'magical_items' not in self.game_state['party_resources']:
                        self.game_state['party_resources']['magical_items'] = []

                    self.game_state['party_resources']['magical_items'].append(item)
                    logger.info(f"Awarded item '{item}' for quest {quest['id']}")

    def _create_stub_combat_manager(self):
        """Create a stub combat manager for fallback functionality."""

        class StubCombatManager:
            def __init__(self):
                self.combat_state = None

            def start_combat(self, players, enemies, environment=None):
                return {"status": "combat_started", "message": "Combat started in fallback mode"}

            def process_action(self, action_data):
                action_type = action_data.get("action_type", "attack")
                attacker = action_data.get("attacker", "Character")
                defender = action_data.get("defender", "Enemy")

                # Create a basic response
                if action_type == "attack":
                    hit = random.choice([True, False])
                    damage = random.randint(1, 8) + 2 if hit else 0

                    return {
                        "status": "success",
                        "hit": hit,
                        "damage": damage,
                        "message": f"{attacker} {'hits' if hit else 'misses'} {defender}" + (
                            f" for {damage} damage" if hit else "")
                    }
                else:
                    return {"status": "success", "message": f"{attacker} performs a {action_type} action"}

            def end_combat(self, reason="unknown"):
                return {"status": "combat_ended", "reason": reason}

        return StubCombatManager()

    def _create_stub_encounter_generator(self):
        """Create a stub encounter generator for fallback functionality."""

        class StubEncounterGenerator:
            def __init__(self):
                pass

            def create_encounter(self, party_level, location_type, difficulty):
                # Create a basic encounter based on inputs
                monsters = []

                # Number of monsters based on difficulty
                monster_count = {"easy": 1, "medium": 2, "hard": 3, "deadly": 4}.get(difficulty, 2)

                # Generic monster based on location
                monster_types = {
                    "forest": ["Wolf", "Bandit", "Goblin"],
                    "mountain": ["Eagle", "Ogre", "Orc"],
                    "dungeon": ["Skeleton", "Zombie", "Goblin"],
                    "urban": ["Bandit", "Cultist", "Guard"],
                    "coastal": ["Pirate", "Giant Crab", "Sahuagin"]
                }.get(location_type, ["Monster"])

                for _ in range(monster_count):
                    monster_type = random.choice(monster_types)

                    monsters.append({
                        "name": monster_type,
                        "hp": party_level * 8,
                        "ac": 12 + (party_level // 3),
                        "xp": party_level * 50
                    })

                # Simple environment features
                features = ["Difficult Terrain", "Cover", "Narrow Passage"]

                return {
                    "monsters": monsters,
                    "environment_features": features,
                    "treasure": [{"type": "gold", "amount": party_level * 20}],
                    "experience_reward": party_level * 100
                }

            def load_monster_database(self, monster_db):
                pass

        return StubEncounterGenerator()

    @classmethod
    def initialize_dungeon_master_ai(
            cls,
            database_path: str = "Databases",
            language_service_url: str = "http://localhost:8000",
            lazy_loading: bool = False
    ):
        """
        Convenience class method to initialize the Dungeon Master AI.

        Args:
            database_path: Path to game databases
            language_service_url: URL for language generation service
            lazy_loading: Whether to load components on demand

        Returns:
            DungeonMasterAI instance
        """
        return cls(
            database_path=database_path,
            language_service_url=language_service_url,
            lazy_loading=lazy_loading
        )

    def __repr__(self) -> str:
        """
        Provide a string representation of the Dungeon Master AI.

        Returns:
            String description of the AI's current state
        """
        # Get party size and active components
        party_size = len(self.game_state.get('player_party', []))
        loaded_components = [name for name, component in self._components.items() if component is not None]

        return (
            f"Enhanced Dungeon Master AI (v2.0)\n"
            f"Current Location: {self.game_state.get('current_location', 'Not set')}\n"
            f"Party Size: {party_size}\n"
            f"Active Quests: {len(self.game_state.get('active_quests', []))}\n"
            f"Story Beats: {len(self.game_state.get('story_beats', []))}\n"
            f"Loaded Components: {len(loaded_components)}/{len(self._components)}"
        )


# Utilities/common.py
# Shared utility functions for the DungeonMasterAI system

import random
import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

# Set up logging
logger = logging.getLogger("utilities")


def roll_dice(dice_str: str) -> int:
    """
    Roll dice based on standard RPG dice notation (e.g., '3d6', '1d20+5').

    Args:
        dice_str: Dice notation string

    Returns:
        Result of the dice roll
    """
    # Handle empty or invalid input
    if not dice_str or not isinstance(dice_str, str):
        return 0

    # Handle simple modifiers (no dice)
    if dice_str.isdigit():
        return int(dice_str)

    # Parse dice notation
    try:
        # Handle modifiers
        modifier = 0
        if '+' in dice_str:
            dice_part, mod_part = dice_str.split('+', 1)
            modifier = int(mod_part)
        elif '-' in dice_str:
            dice_part, mod_part = dice_str.split('-', 1)
            modifier = -int(mod_part)
        else:
            dice_part = dice_str

        # Handle multiple dice sets (e.g., "2d6+1d4")
        if '+' in dice_part and 'd' in dice_part.split('+', 1)[1]:
            dice_sets = dice_part.split('+')
            total = modifier

            for dice_set in dice_sets:
                num_dice, die_size = map(int, dice_set.split('d'))
                for _ in range(num_dice):
                    total += random.randint(1, die_size)

            return total

        # Standard single dice set
        num_dice, die_size = map(int, dice_part.split('d'))

        # Roll dice and sum results
        total = modifier
        for _ in range(num_dice):
            total += random.randint(1, die_size)

        return total
    except Exception as e:
        logger.warning(f"Error rolling dice '{dice_str}': {e}")
        return 0


def calculate_modifier(ability_score: int) -> int:
    """
    Calculate ability modifier from ability score using D&D 5e rules.

    Args:
        ability_score: Ability score value

    Returns:
        Ability modifier
    """
    return (ability_score - 10) // 2


def load_resource(resource_path: str, default_value=None):
    """
    Load a resource file (JSON, text, etc.) with error handling.

    Args:
        resource_path: Path to the resource file
        default_value: Default value to return if loading fails

    Returns:
        Loaded resource or default value
    """
    try:
        # Check if file exists
        if not os.path.exists(resource_path):
            logger.warning(f"Resource not found: {resource_path}")
            return default_value

        # Load based on file extension
        ext = os.path.splitext(resource_path)[1].lower()

        if ext == '.json':
            with open(resource_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif ext in ['.txt', '.md']:
            with open(resource_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Try to load as JSON first, then as text
            try:
                with open(resource_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                with open(resource_path, 'r', encoding='utf-8') as f:
                    return f.read()
    except Exception as e:
        logger.error(f"Error loading resource '{resource_path}': {e}")
        return default_value


def generate_unique_id(prefix: str = '', length: int = 4) -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part

    Returns:
        Unique ID string
    """
    chars = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Removed confusing chars like I, O
    random_part = ''.join(random.choice(chars) for _ in range(length))

    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def normalize_name(name: str) -> str:
    """
    Normalize a name for consistent lookup.

    Args:
        name: Name to normalize

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Remove special characters, convert to lowercase
    return ''.join(c.lower() for c in name if c.isalnum() or c.isspace())


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"


def safe_get(obj: Dict[str, Any], path: str, default=None) -> Any:
    """
    Safely get a nested value from a dictionary using dot notation.

    Args:
        obj: Dictionary to get value from
        path: Path to value using dot notation (e.g., 'stats.abilities.strength')
        default: Default value to return if path not found

    Returns:
        Value at path or default
    """
    if not obj or not isinstance(obj, dict):
        return default

    parts = path.split('.')
    current = obj

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default

    return current


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any],
                override_existing: bool = True) -> Dict[str, Any]:
    """
    Merge two dictionaries with nested structure.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (values override first if overlap)
        override_existing: Whether to override existing values

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_dicts(result[key], value, override_existing)
        elif key not in result or override_existing:
            # Add or override value
            result[key] = value

    return result
