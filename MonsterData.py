# DataManager/MonsterData.py
import re
from typing import Dict, List, Any, Optional


class MonsterData:
    """Handles monster data processing and conversion."""

    def __init__(self):
        """Initialize the monster data manager."""
        self.monsters = {}
        self.environment_mappings = self.initialize_environment_mappings()

    def load_monsters(self, monster_data):
        """
        Load monster data.

        Args:
            monster_data: Dictionary of monster data
        """
        self.monsters = monster_data

    def filter_monsters_by_environment(self, environment):
        """
        Filter monsters by suitable environment.

        Args:
            environment: Environment type to filter by

        Returns:
            List of monsters suitable for the environment
        """
        filtered = []

        for monster_name, monster in self.monsters.items():
            # Check if monster has environment data
            environments = monster.get('inferred_environments', [])
            if not environments and 'environment' in monster:
                environments = monster['environment']

            if environment in environments or "any" in environments:
                filtered.append(monster)

        return filtered

    def filter_monsters_by_cr(self, min_cr, max_cr):
        """
        Filter monsters by challenge rating range.

        Args:
            min_cr: Minimum challenge rating
            max_cr: Maximum challenge rating

        Returns:
            List of monsters within the CR range
        """
        filtered = []

        for monster_name, monster in self.monsters.items():
            # Check if monster has CR data
            if "cr" in monster:
                cr = monster["cr"]
                if min_cr <= cr <= max_cr:
                    filtered.append(monster)

        return filtered

    def get_monster_by_name(self, name):
        """
        Get a monster by name.

        Args:
            name: Monster name

        Returns:
            Monster data or None if not found
        """
        return self.monsters.get(name)

    @staticmethod
    def parse_monsters(root) -> Dict:
        """
        Parse monster database into more accessible format with environment inference.

        Args:
            root: XML root element

        Returns:
            Dict of monsters indexed by name
        """
        monsters = {}

        # Create environment mappings for later use
        environment_mappings = MonsterData.initialize_environment_mappings()
        type_environment_map = environment_mappings["type_environment_map"]
        keyword_environment_map = environment_mappings["keyword_environment_map"]

        for monster_elem in root.findall('./monster'):
            try:
                name_elem = monster_elem.find('name')
                if name_elem is not None:
                    name = name_elem.text

                    # Convert monster to dictionary
                    monster_dict = {}

                    # Specifically parse challenge rating from <cr> tag
                    cr_elem = monster_elem.find('cr')
                    if cr_elem is not None:
                        try:
                            # Handle potential fractional CR values
                            if cr_elem.text and '/' in cr_elem.text:
                                # Fractional CR like '1/2', '1/4', '1/8'
                                numerator, denominator = cr_elem.text.split('/')
                                monster_dict['cr'] = float(numerator) / float(denominator)
                            else:
                                # Standard numeric CR
                                monster_dict['cr'] = float(cr_elem.text or "1")
                        except (ValueError, TypeError):
                            print(f"Warning: Could not parse CR for {name}: {cr_elem.text}")
                            monster_dict['cr'] = 1.0  # Default to 1 if parsing fails
                    else:
                        monster_dict['cr'] = 1.0  # Default to 1 if no CR tag found

                    # Convert monster to dictionary
                    for child in monster_elem:
                        if child.tag in ['trait', 'action', 'legendary']:
                            if child.tag not in monster_dict:
                                monster_dict[child.tag] = []

                            trait_dict = {}
                            for trait_child in child:
                                trait_dict[trait_child.tag] = trait_child.text or ''
                            monster_dict[child.tag].append(trait_dict)
                        else:
                            monster_dict[child.tag] = child.text or ''

                    # Infer environments from monster traits and types
                    inferred_environments = MonsterData.infer_monster_environments(
                        monster_dict, type_environment_map, keyword_environment_map)
                    monster_dict['inferred_environments'] = inferred_environments

                    monsters[name] = monster_dict
            except Exception as e:
                print(f"Error parsing monster: {e}")
                continue

        return monsters

    @staticmethod
    def initialize_environment_mappings() -> Dict:
        """
        Initialize mappings to infer monster environments based on types and traits.

        Returns:
            Dict containing environment mapping dictionaries
        """
        # Type-to-environment mappings
        type_environment_map = {
            "beast": ["forest", "mountain", "grassland", "coastal"],
            "dragon": ["mountain", "forest", "coastal", "urban", "dungeon"],
            "aberration": ["dungeon", "underdark"],
            "celestial": ["celestial_plane", "mountain"],
            "construct": ["dungeon", "urban"],
            "elemental": ["elemental_plane", "mountain", "coastal"],
            "fey": ["forest", "fey_wilds"],
            "fiend": ["abyss", "nine_hells", "dungeon"],
            "giant": ["mountain", "hill", "coastal"],
            "humanoid": ["urban", "forest", "mountain", "coastal", "grassland", "desert"],
            "monstrosity": ["dungeon", "mountain", "forest", "underdark"],
            "ooze": ["dungeon", "underdark", "sewers"],
            "plant": ["forest", "swamp", "grassland"],
            "undead": ["dungeon", "graveyard", "urban", "swamp"]
        }

        # Keyword-to-environment mappings for traits and abilities
        keyword_environment_map = {
            "swim": ["coastal", "underwater", "swamp", "river"],
            "aquatic": ["coastal", "underwater", "river"],
            "fly": ["mountain", "forest", "aerial"],
            "burrow": ["desert", "mountain", "underdark", "grassland"],
            "amphibious": ["coastal", "swamp", "river"],
            "snow": ["arctic", "mountain"],
            "ice": ["arctic", "mountain"],
            "fire": ["volcanic", "elemental_plane", "desert"],
            "desert": ["desert"],
            "forest": ["forest"],
            "mountain": ["mountain"],
            "dark": ["underdark", "dungeon", "night"],
            "shadow": ["shadowfell", "dungeon", "night"],
            "water": ["coastal", "river", "underwater"],
            "swamp": ["swamp"],
            "jungle": ["jungle"],
            "underdark": ["underdark"],
            "underground": ["underdark", "dungeon"],
            "urban": ["urban"],
            "ethereal": ["ethereal_plane"],
            "astral": ["astral_plane"]
        }

        # Default fallback monsters for each environment
        default_environment_monsters = {
            "forest": ["Wolf", "Bandit", "Goblin", "Dire Wolf", "Owlbear"],
            "mountain": ["Eagle", "Ogre", "Orc", "Hill Giant", "Griffon"],
            "dungeon": ["Skeleton", "Zombie", "Ghoul", "Goblin", "Orc", "Hobgoblin"],
            "urban": ["Bandit", "Cultist", "Spy", "Thug", "Guard"],
            "coastal": ["Merfolk", "Sahuagin", "Pirate", "Giant Crab", "Reef Shark"],
            "desert": ["Dust Mephit", "Gnoll", "Giant Scorpion", "Mummy"],
            "grassland": ["Goblin", "Hobgoblin", "Gnoll", "Lion", "Ogre"],
            "arctic": ["Wolf", "Polar Bear", "Ice Mephit", "Yeti"],
            "underdark": ["Drow", "Quaggoth", "Mind Flayer", "Umber Hulk", "Beholder"],
            "swamp": ["Lizardfolk", "Bullywug", "Crocodile", "Hydra", "Black Dragon"]
        }

        return {
            "type_environment_map": type_environment_map,
            "keyword_environment_map": keyword_environment_map,
            "default_environment_monsters": default_environment_monsters
        }

    @staticmethod
    def infer_monster_environments(monster_data: Dict, type_map: Dict, keyword_map: Dict) -> List[str]:
        """
        Infer what environments a monster might be found in based on its traits and type.

        Args:
            monster_data: Monster dictionary data
            type_map: Type to environment mapping dictionary
            keyword_map: Keyword to environment mapping dictionary

        Returns:
            List of inferred environments
        """
        inferred_environments = set()

        # Extract creature type
        monster_type = monster_data.get('type', '').lower()

        # Infer from creature type
        for type_keyword in type_map:
            if type_keyword in monster_type:
                inferred_environments.update(type_map[type_keyword])

        # Check movement types
        speed = monster_data.get('speed', '').lower()
        if 'swim' in speed:
            inferred_environments.update(keyword_map['swim'])
        if 'fly' in speed:
            inferred_environments.update(keyword_map['fly'])
        if 'burrow' in speed:
            inferred_environments.update(keyword_map['burrow'])

        # Check traits and actions
        for trait_list_name in ['trait', 'action', 'legendary']:
            if trait_list_name in monster_data and isinstance(monster_data[trait_list_name], list):
                for trait in monster_data[trait_list_name]:
                    if 'name' in trait and trait['name']:
                        trait_name = trait['name'].lower()
                        # Check trait name for environment keywords
                        for keyword, environments in keyword_map.items():
                            if keyword in trait_name:
                                inferred_environments.update(environments)

                    if 'text' in trait and trait['text']:
                        trait_text = trait['text'].lower()
                        # Check trait description for environment keywords
                        for keyword, environments in keyword_map.items():
                            if keyword in trait_text:
                                inferred_environments.update(environments)

        # Default fallback if no environments inferred
        if not inferred_environments:
            inferred_environments.add("any")

        return list(inferred_environments)

    @staticmethod
    def get_monster_stat_block(monster_name: str, monster_db: Dict) -> Dict:
        """
        Get a formatted monster stat block from the database.

        Args:
            monster_name: Name of the monster to retrieve
            monster_db: Monster database dictionary

        Returns:
            Dict containing monster stats or empty dict if not found
        """
        if monster_name in monster_db:
            monster = monster_db[monster_name]

            # Calculate derived stats
            hp = MonsterData.parse_hp(monster.get('hp', '10'))

            # Format stat block
            stat_block = {
                "name": monster_name,
                "size": monster.get('size', 'Medium'),
                "type": monster.get('type', 'Creature'),
                "alignment": monster.get('alignment', 'Neutral'),
                "ac": monster.get('ac', '10'),
                "hp": hp,
                "speed": monster.get('speed', '30 ft.'),
                "abilities": {
                    "str": int(monster.get('str', 10)),
                    "dex": int(monster.get('dex', 10)),
                    "con": int(monster.get('con', 10)),
                    "int": int(monster.get('int', 10)),
                    "wis": int(monster.get('wis', 10)),
                    "cha": int(monster.get('cha', 10)),
                },
                "cr": monster.get('cr', 1.0),
                "environment": monster.get('inferred_environments', ['any']),
                "traits": monster.get('trait', []),
                "actions": monster.get('action', []),
                "legendary_actions": monster.get('legendary', [])
            }

            return stat_block

        return {}

    @staticmethod
    def parse_hp(hp_text: str) -> int:
        """
        Parse HP text like '45 (7d8+14)' to get the actual HP value.

        Args:
            hp_text: HP text from the monster stat block

        Returns:
            Integer HP value
        """
        if not hp_text:
            return 10

        # Extract the numeric part before any parentheses
        match = re.match(r'(\d+)', hp_text)
        if match:
            return int(match.group(1))
        return 10