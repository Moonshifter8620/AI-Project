import os
import xml.etree.ElementTree as ET
import json
import re


class DatabaseLoader:
    """Loads and parses database files for D&D 5e content."""

    def __init__(self, database_path):
        """
        Initialize the database loader.

        Args:
            database_path: Path to the database files
        """
        self.database_path = database_path
        self.databases = {}

    def load_database(self, database_name):
        """
        Load a database by name.

        Args:
            database_name: Name of the database to load

        Returns:
            Dictionary containing the database contents
        """
        # Check if already loaded
        if database_name in self.databases:
            return self.databases[database_name]

        # File mapping
        database_files = {
            "monsters": "Bestiary Compendium.xml",
            "backgrounds": "Backgrounds.xml",
            "classes": "Classes.xml",
            "feats": "Feats.xml",
            "races": "Races.xml",
            "magic_items": "Magic Items.xml",
            "mundane_items": "Mundane items.xml",
            "spells": "Spells compendium.xml"
        }

        # Check if database exists
        if database_name not in database_files:
            print(f"Unknown database: {database_name}")
            return {}

        file_name = database_files[database_name]
        file_path = os.path.join(self.database_path, file_name)

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Database file not found: {file_path}")
            return self._create_mock_database(database_name)

        # Load the database based on file type
        if file_name.endswith(".xml"):
            try:
                return self._load_xml_database(file_path, database_name)
            except Exception as e:
                print(f"Error loading XML database: {e}")
                return self._create_mock_database(database_name)
        elif file_name.endswith(".json"):
            try:
                return self._load_json_database(file_path)
            except Exception as e:
                print(f"Error loading JSON database: {e}")
                return self._create_mock_database(database_name)
        else:
            print(f"Unsupported file format: {file_name}")
            return self._create_mock_database(database_name)

    def _load_xml_database(self, file_path, database_name):
        """Load and parse an XML database."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if database_name == "monsters":
                return self._parse_monsters(root)
            elif database_name == "spells":
                return self._parse_spells(root)
            else:
                return self._xml_to_dict(root)
        except Exception as e:
            print(f"Error parsing XML database: {e}")
            return self._create_mock_database(database_name)

    def _load_json_database(self, file_path):
        """Load and parse a JSON database."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_monsters(self, root):
        """Parse monster database into dictionary format."""
        monsters = {}

        for monster_elem in root.findall('./monster'):
            try:
                name_elem = monster_elem.find('name')
                if name_elem is not None:
                    name = name_elem.text.strip()

                    # Convert monster to dictionary
                    monster_dict = {}

                    # Handle common elements
                    for elem_name in ['size', 'type', 'alignment', 'ac', 'hp', 'speed']:
                        elem = monster_elem.find(elem_name)
                        if elem is not None:
                            monster_dict[elem_name] = elem.text

                    # Handle ability scores
                    for ability in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                        ability_elem = monster_elem.find(ability)
                        if ability_elem is not None:
                            monster_dict[ability] = ability_elem.text

                    # Handle CR
                    cr_elem = monster_elem.find('cr')
                    if cr_elem is not None:
                        cr_text = cr_elem.text
                        if '/' in cr_text:
                            # Handle fractions like '1/2'
                            num, denom = cr_text.split('/')
                            monster_dict['cr'] = float(num) / float(denom)
                        else:
                            monster_dict['cr'] = float(cr_text)

                    # Add name to dictionary
                    monster_dict['name'] = name

                    # Infer environment
                    monster_dict['environments'] = self._infer_monster_environments(monster_dict)

                    monsters[name] = monster_dict
            except Exception as e:
                print(f"Error parsing monster: {e}")
                continue

        return monsters

    def _parse_spells(self, root):
        """Parse spell database into dictionary format."""
        spells = {}

        for spell_elem in root.findall('./spell'):
            try:
                name_elem = spell_elem.find('name')
                if name_elem is not None:
                    name = name_elem.text.strip()

                    # Convert spell to dictionary
                    spell_dict = {}

                    # Handle common elements
                    for elem_name in ['level', 'school', 'time', 'range', 'components', 'duration', 'classes', 'text']:
                        elem = spell_elem.find(elem_name)
                        if elem is not None:
                            spell_dict[elem_name] = elem.text

                    # Add name to dictionary
                    spell_dict['name'] = name

                    spells[name] = spell_dict
            except Exception as e:
                print(f"Error parsing spell: {e}")
                continue

        return spells

    def _xml_to_dict(self, element):
        """Generic conversion of XML element to dictionary."""
        result = {}

        for child in element:
            if len(child) > 0:
                # Element has children
                if child.tag not in result:
                    result[child.tag] = []
                result[child.tag].append(self._xml_to_dict(child))
            else:
                # Element has no children
                if child.tag not in result:
                    result[child.tag] = child.text
                else:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child.text)

        return result

    def _infer_monster_environments(self, monster):
        """Infer suitable environments for a monster based on its type and traits."""
        environments = []

        # Environment mappings based on type
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

        # Get monster type
        monster_type = monster.get('type', '').lower()

        # Check for type keywords
        for type_key, env_list in type_environment_map.items():
            if type_key in monster_type:
                environments.extend(env_list)

        # If no environments found, assume it can be anywhere
        if not environments:
            environments = ["any"]

        return environments

    def _create_mock_database(self, database_name):
        """Create a mock database for testing."""
        if database_name == "monsters":
            return {
                "Goblin": {"name": "Goblin", "cr": 0.25, "type": "humanoid", "hp": 7,
                           "environments": ["forest", "mountain", "dungeon"]},
                "Orc": {"name": "Orc", "cr": 0.5, "type": "humanoid", "hp": 15,
                        "environments": ["forest", "mountain", "dungeon"]},
                "Troll": {"name": "Troll", "cr": 5, "type": "giant", "hp": 84,
                          "environments": ["mountain", "forest", "dungeon"]},
                "Wolf": {"name": "Wolf", "cr": 0.25, "type": "beast", "hp": 11,
                         "environments": ["forest", "mountain", "grassland"]},
                "Zombie": {"name": "Zombie", "cr": 0.25, "type": "undead", "hp": 22,
                           "environments": ["dungeon", "graveyard", "urban"]}
            }
        elif database_name == "spells":
            return {
                "Fireball": {"name": "Fireball", "level": "3", "school": "Evocation"},
                "Cure Wounds": {"name": "Cure Wounds", "level": "1", "school": "Evocation"},
                "Magic Missile": {"name": "Magic Missile", "level": "1", "school": "Evocation"}
            }
        else:
            return {}