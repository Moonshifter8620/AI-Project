#!/usr/bin/env python3
import os
import re
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

class LanguageManager:
    """
    Manages natural language generation for the D&D 5e AI Dungeon Master.
    Handles NPC dialogue, narrative descriptions, and fantasy language generation.
    """

    def __init__(self, database_path="C:\\DnD 5e Project\\Databases", log_level=logging.INFO):
        """Initialize the language manager with access to D&D databases."""
        # Setup logging
        logging.basicConfig(level=log_level,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("LanguageManager")
        self.logger.info("Initializing LanguageManager...")

        # Set database path and books path
        self.database_path = database_path
        self.books_path = os.path.join(database_path, "Books")
        self.logger.info(f"Database path: {database_path}")
        self.logger.info(f"Books path: {self.books_path}")

        # NPC dialogue patterns and templates
        self.dialogue_templates = self._load_dialogue_templates()

        # Environment description templates
        self.environment_templates = self._load_environment_templates()

        # Combat description templates
        self.combat_templates = self._load_combat_templates()

        # Vocabulary replacements for different races/backgrounds
        self.race_vocabulary = self._load_race_vocabulary()

        # Speech patterns for different races/backgrounds
        self.race_speech_patterns = self._load_race_speech_patterns()

        # Load fantasy name patterns for NPCs and locations
        self.name_patterns = self._load_name_patterns()

        # Load fantasy phrases and idioms
        self.fantasy_phrases = self._load_fantasy_phrases()

        # Modern term replacement dictionary
        self.modern_terms = self._load_modern_replacements()

        # Track NPC dialogue history for consistency
        self.npc_dialogue_history = {}

        # Load story hooks and plot elements
        self.story_hooks = self._load_story_hooks()

        self.logger.info("LanguageManager initialized successfully")

    def _normalize_race(self, race: str) -> str:
        """Normalize race name to match name pattern keys."""
        race_map = {
            "human": "human",
            "dwarf": "dwarf",
            "dwarven": "dwarf",
            "mountain dwarf": "dwarf",
            "hill dwarf": "dwarf",
            "elf": "elf",
            "elven": "elf",
            "high elf": "elf",
            "wood elf": "elf",
            "drow": "elf",
            "halfling": "halfling",
            "gnome": "halfling",
            "orc": "orc",
            "half-orc": "orc",
            "half orc": "orc",
            "dragonborn": "dragon",
            "tiefling": "fiend",
            "aasimar": "celestial"
        }

        # Return normalized race or default to human
        return race_map.get(race.lower(), "human")

    def _generate_inn_name(self) -> str:
        """Generate a random fantasy inn/tavern name."""
        adjectives = [
            "Prancing", "Dancing", "Laughing", "Drunken", "Rusty", "Golden", "Silver",
            "Bronze", "Iron", "Copper", "Brass", "Tin", "Wooden", "Stone", "Crystal",
            "Emerald", "Ruby", "Sapphire", "Diamond", "Bloody", "Broken", "Shattered",
            "Smiling", "Grinning", "Winking", "Slumbering", "Roaring", "Howling",
            "Whispering", "Singing", "Barking", "Leaping", "Charging"
        ]

        nouns = [
            "Pony", "Horse", "Stallion", "Mare", "Mule", "Donkey", "Stag", "Buck", "Doe",
            "Fox", "Wolf", "Bear", "Lion", "Tiger", "Eagle", "Hawk", "Falcon", "Raven",
            "Crow", "Swan", "Goose", "Duck", "Rooster", "Dragon", "Wyvern", "Griffin",
            "Unicorn", "Pegasus", "Boar", "Hog", "Goblin", "Orc", "Troll", "Giant",
            "Dwarf", "Elf", "Gnome", "Halfling", "Ogre", "Minotaur", "Centaur", "Satyr",
            "Nymph", "Mermaid", "Siren", "Witch", "Wizard", "Warlock", "Sorcerer",
            "Bard", "Knight", "Warrior", "Archer", "Ranger", "Rogue", "Thief",
            "Assassin", "Pirate", "Sailor", "Captain", "King", "Queen", "Prince",
            "Princess", "Duke", "Duchess", "Baron", "Baroness", "Count", "Countess",
            "Lord", "Lady", "Maiden", "Virgin", "Harlot", "Wench", "Serving Girl",
            "Barmaid", "Innkeeper", "Traveler", "Wanderer", "Vagabond", "Nomad",
            "Adventurer", "Hero", "Villain", "Necromancer", "Shaman", "Priest",
            "Priestess", "Monk", "Friar", "Nun", "Bishop", "Archbishop", "Pope",
            "Cardinal", "Saint", "Angel", "Demon", "Devil", "Imp", "Fiend", "Sprite",
            "Pixie", "Fairy", "Elf", "Dwarf", "Gnome", "Halfling", "Hobbit"
        ]

        return f"The {random.choice(adjectives)} {random.choice(nouns)}"

    def _generate_fantasy_word(self, syllables: int = 2) -> str:
        """Generate a random fantasy-sounding word with the specified number of syllables."""
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'qu', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
        vowels = ['a', 'e', 'i', 'o', 'u', 'y', 'ae', 'ai', 'au', 'ea', 'ee', 'ei', 'eu', 'ia', 'ie', 'oi', 'oo', 'ou', 'ui']

        # Consonant clusters that can go at the beginning of a syllable
        initial_clusters = ['bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 'pl', 'pr', 'sc', 'sk', 'sl', 'sm', 'sn', 'sp', 'st', 'str', 'sw', 'tr', 'tw', 'wh', 'wr']

        # Consonant clusters that can go at the end of a syllable
        final_clusters = ['ck', 'ft', 'ld', 'lf', 'lk', 'lm', 'lp', 'lt', 'mp', 'nd', 'ng', 'nk', 'nt', 'pt', 'rb', 'rc', 'rd', 'rf', 'rg', 'rk', 'rl', 'rm', 'rn', 'rp', 'rqu', 'rt', 'rth', 'st', 'th']

        word = ''

        for i in range(syllables):
            # Decide on syllable structure
            # CV, CVC, VC, V (C = consonant, V = vowel)
            structure = random.choice(['CV', 'CVC', 'VC', 'V', 'CV', 'CVC'])  # Weight towards CV and CVC

            # Generate syllable
            if structure == 'CV':
                # Use cluster or single consonant
                if random.random() < 0.3 and i == 0:  # 30% chance of cluster at beginning of word
                    word += random.choice(initial_clusters)
                else:
                    word += random.choice(consonants)
                word += random.choice(vowels)
            elif structure == 'CVC':
                # Use cluster or single consonant for initial
                if random.random() < 0.3 and i == 0:  # 30% chance of cluster at beginning of word
                    word += random.choice(initial_clusters)
                else:
                    word += random.choice(consonants)
                word += random.choice(vowels)
                # Use cluster or single consonant for final
                if random.random() < 0.3:  # 30% chance of final cluster
                    word += random.choice(final_clusters)
                else:
                    word += random.choice(consonants)
            elif structure == 'VC':
                word += random.choice(vowels)
                # Use cluster or single consonant
                if random.random() < 0.3:  # 30% chance of final cluster
                    word += random.choice(final_clusters)
                else:
                    word += random.choice(consonants)
            elif structure == 'V':
                word += random.choice(vowels)

        # Capitalize first letter
        return word.capitalize()

    def _generate_quest_title(self, quest_type: str, hook: str) -> str:
        """Generate a title for a quest based on type and hook."""
        # Quest title templates by type
        title_templates = {
            "rescue": [
                "The Rescue of {target}",
                "Saving {target}",
                "{target} in Peril",
                "A Desperate Rescue",
                "The Abduction"
            ],
            "investigation": [
                "The Mystery of {subject}",
                "Strange {subject}",
                "Investigating the {subject}",
                "The Curious Case of {subject}",
                "Uncovering the Truth"
            ],
            "protection": [
                "Defending {target}",
                "The Guardian's Duty",
                "Protection at All Costs",
                "Shield of {target}",
                "The Last Defense"
            ],
            "retrieval": [
                "The Lost {item}",
                "Recovering the {item}",
                "The Hunt for {item}",
                "The Missing {item}",
                "Return of the {item}"
            ],
            "elimination": [
                "The Threat of {enemy}",
                "Hunting the {enemy}",
                "Purge the {enemy}",
                "The {enemy} Menace",
                "Eradication"
            ],
            "escort": [
                "Safe Passage for {target}",
                "Escort to {destination}",
                "The Dangerous Journey",
                "Guarding the {target}",
                "A Perilous Path"
            ],
            "mystery": [
                "The Enigma of {subject}",
                "Unraveling Secrets",
                "The {subject} Conundrum",
                "Hidden Truths",
                "Shadows and Whispers"
            ],
            "intrigue": [
                "Webs of Deceit",
                "The {faction} Conspiracy",
                "Political Pawns",
                "Court of Shadows",
                "Dangerous Alliances"
            ],
            "exploration": [
                "Into the Unknown",
                "The Uncharted {location}",
                "Discovery of {location}",
                "Mapping the Frontier",
                "The Lost Expedition"
            ],
            "defense": [
                "The Siege of {location}",
                "Last Stand at {location}",
                "Defending the {location}",
                "The Approaching Horde",
                "Fortify and Hold"
            ],
            "competition": [
                "The Grand Tournament",
                "Trial of Champions",
                "Contest of {skill}",
                "The {prize} Challenge",
                "Proving Ground"
            ],
            "disaster": [
                "Impending Doom",
                "The {disaster} Crisis",
                "Averting Catastrophe",
                "When Nature Strikes",
                "The Coming Storm"
            ]
        }

        # Extract key elements from hook
        key_elements = self._extract_key_elements(hook)

        # Get templates for this quest type
        templates = title_templates.get(quest_type, ["A Mysterious Quest"])

        # Select a random template
        template = random.choice(templates)

        # Fill in template with key elements
        title = template
        for key, value in key_elements.items():
            title = title.replace(f"{{{key}}}", value)

        # If no replacements were made and {} still exists, remove them
        title = re.sub(r'\{[^}]*\}', '', title)

        # Clean up any extra spaces
        title = re.sub(r'\s+', ' ', title).strip()

        return title

    def _extract_key_elements(self, text: str) -> Dict[str, str]:
        """Extract key elements from text for use in templates."""
        elements = {}

        # Look for potential targets (people, locations)
        target_match = re.search(r'(?:rescue|save|protect|defend)\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if target_match:
            elements["target"] = target_match.group(1).strip()

        # Look for potential items
        item_match = re.search(r'(?:retrieve|recover|find|return|stolen)\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if item_match:
            elements["item"] = item_match.group(1).strip()

        # Look for potential enemies
        enemy_match = re.search(r'(?:defeat|kill|hunt|eliminate)\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if enemy_match:
            elements["enemy"] = enemy_match.group(1).strip()

        # Look for potential locations
        location_match = re.search(r'(?:at|in|to|from)\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if location_match:
            elements["location"] = location_match.group(1).strip()
            elements["destination"] = location_match.group(1).strip()

        # Look for potential subjects of investigation
        subject_match = re.search(r'(?:investigate|study|examine|research)\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if subject_match:
            elements["subject"] = subject_match.group(1).strip()

        # Look for potential factions
        faction_match = re.search(r'(?:faction|guild|organization|group|clan|family)\s+(?:known as|called)?\s+(?:the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if faction_match:
            elements["faction"] = faction_match.group(1).strip()

        # Look for potential skills or contests
        skill_match = re.search(r'(?:contest|competition|tournament|challenge|test) of\s+([^\.,]+)', text, re.IGNORECASE)
        if skill_match:
            elements["skill"] = skill_match.group(1).strip()

        # Look for potential prizes
        prize_match = re.search(r'(?:prize|reward|award|trophy)\s+(?:is|of)?\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if prize_match:
            elements["prize"] = prize_match.group(1).strip()

        # Look for potential disasters
        disaster_match = re.search(r'(?:disaster|catastrophe|calamity|crisis)\s+(?:of)?\s+(?:a|an|the)?\s+([^\.,]+)', text, re.IGNORECASE)
        if disaster_match:
            elements["disaster"] = disaster_match.group(1).strip()

        # Use generics if no elements found
        if not elements.get("target"):
            elements["target"] = "the Innocent"
        if not elements.get("item"):
            elements["item"] = "Artifact"
        if not elements.get("enemy"):
            elements["enemy"] = "Threat"
        if not elements.get("location"):
            elements["location"] = "Wilderness"
            elements["destination"] = "Destination"
        if not elements.get("subject"):
            elements["subject"] = "Phenomenon"
        if not elements.get("faction"):
            elements["faction"] = "Organization"
        if not elements.get("skill"):
            elements["skill"] = "Skill"
        if not elements.get("prize"):
            elements["prize"] = "Champion's"
        if not elements.get("disaster"):
            elements["disaster"] = "Impending"

        return elements

    def _generate_quest_rewards(self, difficulty: str, level: int) -> Dict[str, Any]:
        """Generate appropriate rewards for a quest based on difficulty and level."""
        # Base gold reward by level
        base_gold = {
            "easy": 10 * level,
            "medium": 25 * level,
            "hard": 50 * level,
            "deadly": 100 * level
        }

        # Get base gold for this difficulty
        gold = base_gold.get(difficulty, 25 * level)

        # Add some random variation (±20%)
        gold = int(gold * random.uniform(0.8, 1.2))

        # Determine number of items
        item_counts = {
            "easy": (0 if level < 3 else 1),
            "medium": (1 if level < 5 else 2),
            "hard": (1 if level < 3 else 2),
            "deadly": (2 if level < 5 else 3)
        }

        num_items = item_counts.get(difficulty, 1)

        # Generate items
        items = []
        for _ in range(num_items):
            item_type = random.choice(["weapon", "armor", "potion", "scroll", "wonderous"])
            if level < 5:
                rarity = "common"
            elif level < 10:
                rarity = random.choice(["common", "uncommon"])
            elif level < 15:
                rarity = random.choice(["uncommon", "rare"])
            else:
                rarity = random.choice(["rare", "very rare"])

            item_name = self._generate_magic_item_name(item_type, rarity)
            items.append({"name": item_name, "type": item_type, "rarity": rarity})

        # Combine into rewards dictionary
        rewards = {
            "gold": gold,
            "items": items,
            "experience": self._calculate_quest_xp(difficulty, level)
        }

        return rewards

    def _generate_magic_item_name(self, item_type: str, rarity: str) -> str:
        """Generate a name for a magic item of the specified type and rarity."""
        # Adjectives by rarity
        rarity_adjectives = {
            "common": ["Sturdy", "Reliable", "Useful", "Practical", "Handy", "Solid", "Dependable"],
            "uncommon": ["Remarkable", "Fine", "Quality", "Superior", "Exceptional", "Noteworthy", "Distinguished"],
            "rare": ["Extraordinary", "Impressive", "Magnificent", "Splendid", "Marvelous", "Wondrous", "Superb"],
            "very rare": ["Legendary", "Mythical", "Fabled", "Storied", "Renowned", "Celebrated", "Illustrious"],
            "legendary": ["Mythical", "Godly", "Divine", "Transcendent", "Supreme", "Ultimate", "Cosmic"]
        }

        # Item templates by type
        item_templates = {
            "weapon": [
                "{adjective} {weapon} of {attribute}",
                "{weapon} of {attribute}",
                "{adjective} {weapon}",
                "{attribute} {weapon}",
                "{owner}'s {weapon}"
            ],
            "armor": [
                "{adjective} {armor} of {attribute}",
                "{armor} of {attribute}",
                "{adjective} {armor}",
                "{attribute} {armor}",
                "{owner}'s {armor}"
            ],
            "potion": [
                "Potion of {attribute}",
                "{adjective} Elixir",
                "Vial of {attribute}",
                "{owner}'s Tonic",
                "Draught of {attribute}"
            ],
            "scroll": [
                "Scroll of {spell}",
                "{adjective} Scroll",
                "Parchment of {spell}",
                "{owner}'s Scroll",
                "Magical Transcript of {spell}"
            ],
            "wonderous": [
                "{adjective} {item}",
                "{item} of {attribute}",
                "{attribute} {item}",
                "{owner}'s {item}",
                "Wondrous {item} of {attribute}"
            ]
        }

        # Item components
        weapons = ["Sword", "Axe", "Hammer", "Dagger", "Bow", "Staff", "Mace", "Spear", "Flail", "Wand"]
        armors = ["Armor", "Shield", "Helmet", "Gauntlets", "Boots", "Bracers", "Cloak", "Robe", "Amulet", "Ring"]
        wonderous_items = ["Orb", "Crystal", "Figurine", "Statue", "Lantern", "Mirror", "Compass", "Quill", "Tome", "Horn", "Flute", "Drum", "Bell", "Whistle", "Mask", "Crown", "Circlet", "Brooch", "Pin", "Emblem", "Token", "Charm", "Relic", "Icon", "Idol", "Totem", "Artifact", "Rune", "Censer", "Brazier", "Cauldron", "Chalice", "Goblet", "Cup", "Bowl", "Plate", "Dish", "Tray", "Box", "Chest", "Coffer", "Casket", "Urn", "Vase", "Bottle", "Flask", "Jar", "Jug", "Canteen", "Waterskin", "Sack", "Bag", "Pouch", "Purse", "Backpack", "Pack", "Satchel", "Haversack", "Rucksack", "Knapsack", "Quiver", "Scabbard", "Sheath", "Holster", "Belt", "Sash", "Girdle", "Bandolier", "Harness", "Strap", "Cord", "Rope", "Chain", "Cable", "Line", "Twine", "String", "Thread", "Yarn", "Fiber", "Cloth", "Fabric", "Tapestry", "Carpet", "Rug", "Mat", "Blanket", "Sheet", "Coverlet", "Quilt", "Bedroll", "Hammock", "Tent", "Pavilion", "Canopy", "Awning", "Tarpaulin", "Sail", "Flag", "Banner", "Pennant", "Standard", "Ensign", "Colors", "Device", "Coat of Arms", "Heraldry", "Blazon", "Sigil", "Seal", "Mark", "Glyph", "Symbol", "Sign", "Pattern", "Design", "Motif", "Emblem", "Logo", "Badge", "Insignia", "Medal", "Medallion", "Decoration", "Award", "Trophy", "Prize", "Reward", "Gift", "Offering", "Tribute", "Tithe", "Alms", "Donation", "Contribution", "Fee", "Toll", "Tax", "Levy", "Duty", "Impost", "Tribute", "Tariff", "Customs", "Excise", "Charge", "Price", "Cost", "Value", "Worth", "Merit", "Esteem", "Regard", "Respect", "Honor", "Reverence", "Veneration", "Worship", "Adoration", "Devotion", "Allegiance", "Loyalty", "Fidelity", "Faith", "Trust", "Belief", "Confidence", "Reliance", "Dependence", "Certainty", "Assurance", "Conviction", "Hope", "Expectation", "Anticipation", "Prospect", "Promise", "Pledge", "Vow", "Oath", "Word", "Bond"]
        attributes = ["Power", "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma", "Fire", "Ice", "Lightning", "Acid", "Poison", "Necrotic", "Radiant", "Force", "Thunder", "Healing", "Protection", "Warding", "Shielding", "Deflection", "Defense", "Offense", "Attack", "Striking", "Precision", "Accuracy", "Speed", "Quickness", "Reflexes", "Reaction", "Perception", "Seeing", "Hearing", "Smelling", "Tasting", "Touching", "Feeling", "Sensing", "Knowing", "Understanding", "Comprehending", "Learning", "Teaching", "Guiding", "Leading", "Following", "Commanding", "Obeying", "Serving", "Helping", "Hindering", "Harming", "Hurting", "Healing", "Curing", "Blessing", "Cursing", "Enchanting", "Charming", "Bewitching", "Hypnotizing", "Mesmerizing", "Entrancing", "Fascinating", "Captivating", "Enthralling", "Beguiling", "Persuading", "Convincing", "Deceiving", "Tricking", "Fooling", "Cheating", "Betraying", "Oathbreaking", "Treachery", "Loyalty", "Devotion", "Dedication", "Commitment", "Conviction", "Belief", "Faith", "Trust", "Hope", "Courage", "Bravery", "Valor", "Heroism", "Cowardice", "Fear", "Terror", "Horror", "Dread", "Anxiety", "Worry", "Concern", "Care", "Empathy", "Sympathy", "Compassion", "Mercy", "Cruelty", "Ruthlessness", "Barbarity", "Savagery", "Brutality", "Viciousness", "Ferocity", "Fierceness", "Wildness", "Tameness", "Domestication", "Civilization", "Culture", "Society", "Community", "Isolation", "Solitude", "Loneliness", "Companionship", "Friendship", "Alliance", "Enmity", "Hostility", "Hatred", "Love", "Affection", "Desire", "Lust", "Passion", "Fervor", "Zeal", "Enthusiasm", "Excitement", "Thrill", "Exhilaration", "Ecstasy", "Rapture", "Bliss", "Joy", "Happiness", "Contentment", "Satisfaction", "Fulfillment", "Completion", "Wholeness", "Harmony", "Balance", "Symmetry", "Order", "Chaos", "Entropy", "Disorder", "Confusion", "Clarity", "Insight", "Vision", "Dream", "Nightmare", "Fantasy", "Reality", "Truth", "Falsity", "Lie", "Deception", "Illusion", "Delusion", "Hallucination", "Perception", "Observation", "Examination", "Investigation", "Inquiry", "Research", "Experimentation", "Discovery", "Invention", "Innovation", "Creation", "Destruction", "Ruin", "Devastation", "Apocalypse", "Doom", "Fate", "Destiny", "Fortune", "Luck", "Chance", "Probability", "Likelihood", "Certainty", "Uncertainty", "Doubt", "Skepticism", "Cynicism", "Pessimism", "Optimism", "Hope", "Despair", "Desolation", "Emptiness", "Void", "Abyss", "Depths", "Heights", "Peaks", "Summit", "Pinnacle", "Apex", "Zenith", "Nadir", "Bottom", "Foundation", "Core", "Center", "Periphery", "Edge", "Border", "Boundary", "Frontier", "Threshold", "Doorway", "Gateway", "Portal", "Entrance", "Exit", "Path", "Road", "Trail", "Track", "Route", "Course", "Way", "Passage", "Corridor", "Tunnel", "Bridge", "Crossing", "Fork", "Junction", "Intersection", "Corner", "Turning", "Twist", "Bend", "Curve", "Arc", "Circle", "Sphere", "Globe", "Orb", "Ball", "Disc", "Plate", "Sheet", "Slab", "Block", "Cube", "Box", "Container", "Vessel", "Vehicle", "Transport", "Travel", "Journey", "Voyage", "Expedition", "Quest", "Mission", "Task", "Assignment", "Challenge", "Difficulty", "Hardship", "Ordeal", "Trial", "Test", "Examination", "Assessment", "Evaluation", "Judgment", "Decision", "Choice", "Option", "Alternative", "Possibility", "Potential", "Capability", "Aptitude", "Talent", "Skill", "Ability", "Power", "Might", "Force", "Strength", "Vigor", "Vitality", "Energy", "Stamina", "Endurance", "Resistance", "Immunity", "Protection", "Safety", "Security", "Danger", "Hazard", "Risk", "Threat", "Warning", "Caution", "Care", "Diligence", "Vigilance", "Watchfulness", "Alertness", "Awareness", "Consciousness", "Realization", "Understanding", "Knowledge", "Information", "Data", "Facts", "Truth", "Reality", "Actuality", "Existence", "Being", "Life", "Death", "Sleep", "Wakefulness", "Consciousness", "Dream", "Vision", "Sight", "Seeing", "Blindness", "Light", "Darkness", "Shadow", "Reflection", "Mirror", "Image", "Likeness", "Resemblance", "Similarity", "Difference", "Uniqueness", "Individuality", "Identity", "Self", "Ego", "Persona", "Character", "Personality", "Nature", "Disposition", "Temperament", "Mood", "Emotion", "Feeling", "Sentiment", "Passion", "Desire"]
        owners = ["Arcanist", "Battlemage", "Champion", "Dragon", "Emperor", "Fae", "Gladiator", "Hero", "Immortal", "Justicar", "Knight", "Lich", "Mage", "Necromancer", "Oracle", "Paladin", "Queen", "Ranger", "Sorcerer", "Titan", "Unicorn", "Vampire", "Warlock", "Xenarch", "Zealot"]
        spells = ["Fireball", "Lightning Bolt", "Ice Storm", "Haste", "Invisibility", "Fly", "Teleport", "Heal", "Harm",
                  "Sleep", "Charm", "Dominate", "Hold", "Fear", "Confusion", "Illusion", "Silence", "Darkness", "Light",
                  "Protection", "Shield", "Mage Armor", "Magic Missile", "Detect Magic", "Identify", "Dispel Magic",
                  "Counterspell", "Remove Curse", "True Seeing", "Scrying", "Divination", "Clairvoyance",
                  "Speak with Dead", "Resurrect", "Revivify", "Animate Dead", "Create Undead", "Circle of Death",
                  "Finger of Death", "Disintegrate", "Wish", "Time Stop", "Power Word Kill", "Meteor Swarm", "Gate",
                  "Plane Shift", "Astral Projection", "Etherealness", "True Polymorph", "Shapechange", "Beast Shape",
                  "Elemental Form", "Dragon Form", "Gaseous Form", "Stone Shape", "Wood Shape", "Flesh to Stone",
                  "Stone to Flesh", "Transmute", "Telekinesis", "Levitate", "Fly", "Feather Fall", "Jump",
                  "Spider Climb", "Water Breathing", "Water Walk"]

        # Select appropriate adjectives for the rarity
        adjectives = rarity_adjectives.get(rarity, ["Magical"])
        adjective = random.choice(adjectives)

        # Select appropriate components based on item type
        if item_type == "weapon":
            item_components = {
                "adjective": adjective,
                "weapon": random.choice(weapons),
                "attribute": random.choice(attributes),
                "owner": random.choice(owners)
            }
            template = random.choice(item_templates["weapon"])
        elif item_type == "armor":
            item_components = {
                "adjective": adjective,
                "armor": random.choice(armors),
                "attribute": random.choice(attributes),
                "owner": random.choice(owners)
            }
            template = random.choice(item_templates["armor"])
        elif item_type == "potion":
            item_components = {
                "adjective": adjective,
                "attribute": random.choice(attributes),
                "owner": random.choice(owners)
            }
            template = random.choice(item_templates["potion"])
        elif item_type == "scroll":
            item_components = {
                "adjective": adjective,
                "spell": random.choice(spells),
                "owner": random.choice(owners)
            }
            template = random.choice(item_templates["scroll"])
        elif item_type == "wonderous":
            item_components = {
                "adjective": adjective,
                "item": random.choice(wonderous_items),
                "attribute": random.choice(attributes),
                "owner": random.choice(owners)
            }
            template = random.choice(item_templates["wonderous"])
        else:
            # Default to a generic magic item
            return f"{adjective} Magic Item"

        # Fill in the template
        for key, value in item_components.items():
            template = template.replace(f"{{{key}}}", value)

        return template

    def _generate_quest_enemies(self, difficulty: str, level: int) -> List[Dict[str, Any]]:
        """Generate appropriate enemies for a quest based on difficulty and level."""
        # Determine number of enemy types
        enemy_counts = {
            "easy": 1,
            "medium": random.randint(1, 2),
            "hard": random.randint(1, 3),
            "deadly": random.randint(2, 3)
        }

        num_enemy_types = enemy_counts.get(difficulty, 1)

        # Enemy challenge ratings by player level
        cr_by_level = {
            1: {"easy": 1 / 8, "medium": 1 / 4, "hard": 1 / 2, "deadly": 1},
            2: {"easy": 1 / 4, "medium": 1 / 2, "hard": 1, "deadly": 2},
            3: {"easy": 1 / 2, "medium": 1, "hard": 2, "deadly": 3},
            4: {"easy": 1 / 2, "medium": 1, "hard": 2, "deadly": 3},
            5: {"easy": 1, "medium": 2, "hard": 3, "deadly": 5},
            6: {"easy": 1, "medium": 3, "hard": 4, "deadly": 6},
            7: {"easy": 2, "medium": 4, "hard": 5, "deadly": 7},
            8: {"easy": 2, "medium": 4, "hard": 5, "deadly": 8},
            9: {"easy": 3, "medium": 5, "hard": 7, "deadly": 10},
            10: {"easy": 3, "medium": 6, "hard": 8, "deadly": 11},
            11: {"easy": 4, "medium": 7, "hard": 9, "deadly": 12},
            12: {"easy": 4, "medium": 8, "hard": 10, "deadly": 13},
            13: {"easy": 5, "medium": 9, "hard": 11, "deadly": 14},
            14: {"easy": 5, "medium": 10, "hard": 12, "deadly": 15},
            15: {"easy": 6, "medium": 11, "hard": 13, "deadly": 16},
            16: {"easy": 6, "medium": 12, "hard": 14, "deadly": 17},
            17: {"easy": 7, "medium": 13, "hard": 15, "deadly": 18},
            18: {"easy": 7, "medium": 14, "hard": 16, "deadly": 19},
            19: {"easy": 8, "medium": 15, "hard": 17, "deadly": 20},
            20: {"easy": 8, "medium": 16, "hard": 18, "deadly": 21}
        }

        # Get appropriate CR for this level and difficulty
        level_key = min(max(level, 1), 20)  # Ensure level is between 1 and 20
        cr_options = cr_by_level.get(level_key, {"easy": 1 / 4, "medium": 1 / 2, "hard": 1, "deadly": 2})
        base_cr = cr_options.get(difficulty, cr_options["medium"])

        # Common enemy types by CR range
        cr_enemy_types = {
            (0, 1): ["Goblins", "Kobolds", "Bandits", "Cultists", "Skeletons", "Zombies", "Giant Rats", "Giant Spiders",
                     "Wolves", "Stirges"],
            (1, 3): ["Orcs", "Hobgoblins", "Bugbears", "Ghouls", "Giant Bats", "Giant Snakes", "Worgs", "Dire Wolves",
                     "Sahuagin", "Evil Cultists"],
            (3, 5): ["Ogres", "Trolls", "Ettins", "Wererats", "Werewolves", "Veterans", "Harpies", "Owl Bears",
                     "Phase Spiders", "Water Elementals"],
            (5, 8): ["Giants", "Manticores", "Wyverns", "Young Dragons", "Vampire Spawn", "Wraiths", "Mages",
                     "Chimeras", "Basilisks", "Revenants"],
            (8, 12): ["Adult Dragons", "Medusas", "Mind Flayers", "Beholders", "Night Hags", "Frost Giants",
                      "Fire Giants", "Djinni", "Efreet", "Unicorns"],
            (12, 16): ["Liches", "Storm Giants", "Vampires", "Nagas", "Rakshasa", "Horned Devils", "Hezrou Demons",
                       "Archmages", "Aboleths", "Death Knights"],
            (16, 30): ["Ancient Dragons", "Balors", "Pit Fiends", "Krakens", "Tarrasques", "Demiliches",
                       "Death Tyrants", "Elder Brain", "Empyreans", "Solar Angels"]
        }

        # Determine appropriate CR range for enemies
        cr_range = None
        for cr_min, cr_max in cr_enemy_types:
            if cr_min <= base_cr <= cr_max:
                cr_range = (cr_min, cr_max)
                break

        # Default to lowest CR range if no match found
        if not cr_range:
            cr_range = (0, 1)

        # Generate enemies
        enemies = []
        for _ in range(num_enemy_types):
            # Select enemy type from appropriate CR range
            enemy_options = cr_enemy_types.get(cr_range, cr_enemy_types[(0, 1)])
            enemy_type = random.choice(enemy_options)

            # Determine challenge level relative to quest difficulty
            if difficulty == "easy":
                challenge = "easy"
            elif difficulty == "medium":
                challenge = random.choice(["easy", "medium"])
            elif difficulty == "hard":
                challenge = random.choice(["medium", "hard"])
            else:  # deadly
                challenge = random.choice(["hard", "deadly"])

            enemies.append({"name": enemy_type, "challenge": challenge})

        return enemies

    def _elaborate_quest_description(self, hook: str, quest_type: str, location: str,
                                     enemies: List[Dict[str, Any]]) -> str:
        """Elaborate on a quest hook to create a more detailed description."""
        # Create introduction based on quest type
        intro_templates = {
            "rescue": [
                f"A desperate plea for help has been issued in {location}.",
                f"Urgent assistance is needed in {location} for a rescue mission.",
                f"Time is of the essence for a rescue operation in {location}."
            ],
            "investigation": [
                f"Strange occurrences in {location} require careful investigation.",
                f"Something unusual is happening in {location} that demands scrutiny.",
                f"Mysterious events in {location} have raised concerning questions."
            ],
            "protection": [
                f"A valuable asset in {location} requires protection from impending danger.",
                f"Guards are needed in {location} to ensure safety during a crucial time.",
                f"Defensive measures must be established in {location} before it's too late."
            ],
            "retrieval": [
                f"A precious item must be recovered from {location} before it falls into the wrong hands.",
                f"An important artifact has gone missing in {location} and must be retrieved.",
                f"A difficult recovery mission awaits brave adventurers in {location}."
            ],
            "elimination": [
                f"A dangerous threat has emerged in {location} and must be neutralized.",
                f"The safety of {location} is compromised until a specific menace is eliminated.",
                f"Skilled warriors are needed to remove a deadly hazard from {location}."
            ],
            "escort": [
                f"Safe passage through {location} is required for an important individual.",
                f"A guide and protector is needed for a journey through {location}.",
                f"The roads through {location} are perilous and require armed escorts."
            ],
            "mystery": [
                f"A bewildering phenomenon in {location} defies explanation.",
                f"The truth behind strange events in {location} remains elusive.",
                f"An enigma in {location} has locals baffled and afraid."
            ],
            "intrigue": [
                f"Political machinations are unfolding in {location}, with dangerous implications.",
                f"Rival factions in {location} are engaged in a shadowy contest of wills.",
                f"Careful navigation of complex relationships in {location} will be essential."
            ],
            "exploration": [
                f"Uncharted territories in {location} await brave explorers.",
                f"A significant discovery in {location} requires further exploration.",
                f"The mysteries of {location} have yet to be fully revealed."
            ],
            "defense": [
                f"The people of {location} require immediate aid against an impending attack.",
                f"Strategic defensive positions in {location} must be secured before the enemy arrives.",
                f"The walls of {location} must be held against overwhelming odds."
            ],
            "competition": [
                f"A contest of skill in {location} offers glory and reward to the victorious.",
                f"Champions from across the land gather in {location} to test their mettle.",
                f"The challenge set forth in {location} will determine who is truly the best."
            ],
            "disaster": [
                f"A catastrophe is imminent in {location} unless swift action is taken.",
                f"The people of {location} face annihilation from an approaching calamity.",
                f"Only the most capable heroes can avert the disaster looming over {location}."
            ]
        }

        intro = random.choice(intro_templates.get(quest_type, [f"An opportunity awaits in {location}."]))

        # Add the hook
        description = f"{intro} {hook}"

        # Add enemy information if appropriate for quest type
        if quest_type in ["elimination", "defense", "rescue", "protection", "escort"]:
            enemy_desc = []
            for enemy in enemies:
                if enemy["challenge"] == "easy":
                    enemy_desc.append(
                        f"Reports indicate the presence of {enemy['name'].lower()}, though they should not pose a significant threat to experienced adventurers.")
                elif enemy["challenge"] == "medium":
                    enemy_desc.append(
                        f"Be wary of {enemy['name'].lower()}, as they are known to be formidable opponents.")
                elif enemy["challenge"] == "hard":
                    enemy_desc.append(
                        f"Dangerous {enemy['name'].lower()} have been spotted in the area, and should not be approached without caution.")
                else:  # deadly
                    enemy_desc.append(
                        f"Extremely dangerous {enemy['name'].lower()} lurk in the area—only the most capable heroes should confront them.")

            if enemy_desc:
                description += f" {random.choice(enemy_desc)}"

        # Add urgency or timing information
        urgency_templates = {
            "rescue": ["Time is of the essence.", "Every moment counts.", "Delays could be fatal."],
            "disaster": ["The situation worsens by the hour.", "There's precious little time to act.",
                         "The countdown to catastrophe has begun."],
            "protection": ["The threat approaches swiftly.", "The window of opportunity is closing.",
                           "Preparation time is limited."],
            "defense": ["The attack is imminent.", "Enemy forces are on the move.", "Defenses must be ready soon."]
        }

        urgency = urgency_templates.get(quest_type, [])
        if urgency and random.random() < 0.7:  # 70% chance to add urgency for applicable quest types
            description += f" {random.choice(urgency)}"

        # Add reward hint
        reward_templates = [
            "The reward for success is substantial.",
            "Those who succeed will be well compensated.",
            "Generous payment awaits those who complete this task.",
            "The promised reward reflects the importance of this matter."
        ]

        if random.random() < 0.5:  # 50% chance to mention rewards
            description += f" {random.choice(reward_templates)}"

        return description

    def _calculate_quest_xp(self, difficulty: str, level: int) -> int:
        """Calculate appropriate XP reward for a quest based on difficulty and level."""
        # Base XP thresholds by character level
        xp_thresholds = {
            1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
            2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
            3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
            4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
            5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
            6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
            7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
            8: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
            9: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
            10: {"easy": 600, "medium": 1200, "hard": 1900, "deadly": 2800},
            11: {"easy": 800, "medium": 1600, "hard": 2400, "deadly": 3600},
            12: {"easy": 1000, "medium": 2000, "hard": 3000, "deadly": 4500},
            13: {"easy": 1100, "medium": 2200, "hard": 3400, "deadly": 5100},
            14: {"easy": 1250, "medium": 2500, "hard": 3800, "deadly": 5700},
            15: {"easy": 1400, "medium": 2800, "hard": 4300, "deadly": 6400},
            16: {"easy": 1600, "medium": 3200, "hard": 4800, "deadly": 7200},
            17: {"easy": 2000, "medium": 3900, "hard": 5900, "deadly": 8800},
            18: {"easy": 2100, "medium": 4200, "hard": 6300, "deadly": 9500},
            19: {"easy": 2400, "medium": 4900, "hard": 7300, "deadly": 10900},
            20: {"easy": 2800, "medium": 5700, "hard": 8500, "deadly": 12700}
        }

        # Get XP threshold for this level and difficulty
        level_key = min(max(level, 1), 20)  # Ensure level is between 1 and 20
        difficulty_thresholds = xp_thresholds.get(level_key, {"easy": 100, "medium": 200, "hard": 300, "deadly": 400})

        # Get XP for this difficulty
        xp = difficulty_thresholds.get(difficulty, difficulty_thresholds["medium"])

        # Add some random variation (±10%)
        xp = int(xp * random.uniform(0.9, 1.1))

        return xp

    def _query_corpus(self, query_text, limit=5):
        """
        Query the corpus database for text similar to the query.

        Args:
            query_text: The search query text
            limit: Maximum number of results to return

        Returns:
            List of dictionaries containing matching text
        """
        try:
            # Connect to corpus database if not already connected
            if not hasattr(self, 'corpus_conn') or self.corpus_conn is None:
                corpus_path = os.path.join(self.database_path, "corpus.sqlite")
                self.corpus_conn = sqlite3.connect(corpus_path)
                self.corpus_cursor = self.corpus_conn.cursor()

            # Search for similar text in sentences table
            # Use LIKE for basic pattern matching
            search_terms = query_text.lower().split()

            # Build a query that matches any of the search terms
            query_conditions = []
            query_params = []

            for term in search_terms:
                if len(term) > 3:  # Skip very short words
                    query_conditions.append("LOWER(text) LIKE ?")
                    query_params.append(f'%{term}%')

            if not query_conditions:
                return []

            sql_query = f"""
                SELECT text, is_dialogue, narrative_type 
                FROM sentences 
                WHERE {' OR '.join(query_conditions)}
                ORDER BY RANDOM()
                LIMIT ?
            """
            query_params.append(limit)

            self.corpus_cursor.execute(sql_query, query_params)
            results = self.corpus_cursor.fetchall()

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "text": row[0],
                    "is_dialogue": bool(row[1]),
                    "narrative_type": row[2] if len(row) > 2 else "general"
                })

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error querying corpus: {e}")
            return []

    def _extract_patterns(self, texts, pattern_type="description"):
        """
        Extract language patterns from a list of texts.

        Args:
            texts: List of text strings to extract patterns from
            pattern_type: Type of pattern to extract (description, dialogue, etc.)

        Returns:
            List of pattern strings with placeholders
        """
        patterns = []

        for text in texts:
            if not text or len(text) < 15:  # Skip very short texts
                continue

            # Process based on pattern type
            pattern = text

            if pattern_type == "description":
                # Replace specific location terms with placeholders
                pattern = re.sub(r'\b(forest|woodland|grove|jungle|woods|thicket)\b',
                                 "{location}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(mountain|peak|hill|cliff|ridge|highlands)\b',
                                 "{location}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(dungeon|cave|cavern|tunnel|chamber|crypt|tomb)\b',
                                 "{location}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(castle|fortress|keep|tower|citadel|palace)\b',
                                 "{location}", pattern, flags=re.IGNORECASE)

                # Replace time references
                pattern = re.sub(r'\b(morning|daybreak|sunrise|dawn)\b',
                                 "{time}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(evening|dusk|sunset|twilight)\b',
                                 "{time}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(night|midnight|darkness)\b',
                                 "{time}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(day|daylight|noon|afternoon)\b',
                                 "{time}", pattern, flags=re.IGNORECASE)

                # Replace weather terms
                pattern = re.sub(r'\b(rain|drizzle|shower|downpour|storm|thunderstorm)\b',
                                 "{weather}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(sunny|clear|bright|cloudless|fair)\b',
                                 "{weather}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(cloudy|overcast|gloomy|dim|gray)\b',
                                 "{weather}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(fog|mist|haze|murky)\b',
                                 "{weather}", pattern, flags=re.IGNORECASE)
                pattern = re.sub(r'\b(snow|sleet|ice|frost|frozen|blizzard)\b',
                                 "{weather}", pattern, flags=re.IGNORECASE)

            elif pattern_type == "dialogue":
                # We'll handle dialogue patterns differently
                pass

            # Check if pattern has changed from original text
            if pattern != text and "{" in pattern:
                patterns.append(pattern)

        # If we don't have enough patterns, use whole sentences
        if len(patterns) < 3:
            for text in texts:
                if len(text.split()) >= 5 and len(text.split()) <= 30:
                    patterns.append(text)

        return patterns

    def _fill_pattern(self, pattern, replacements):
        """
        Fill a pattern with specific replacements.

        Args:
            pattern: Pattern string with placeholders
            replacements: Dictionary of replacements (key -> value)

        Returns:
            Filled pattern string
        """
        filled_text = pattern

        # Replace placeholders with provided values
        for key, value in replacements.items():
            if value:
                placeholder = "{" + key + "}"
                filled_text = filled_text.replace(placeholder, str(value))

        # Handle any remaining placeholders with generic text
        remaining_placeholders = re.findall(r'\{([^}]+)\}', filled_text)
        for placeholder in remaining_placeholders:
            if "location" in placeholder:
                filled_text = filled_text.replace("{" + placeholder + "}", "area")
            elif "time" in placeholder:
                filled_text = filled_text.replace("{" + placeholder + "}", "time")
            elif "weather" in placeholder:
                filled_text = filled_text.replace("{" + placeholder + "}", "weather")
            else:
                filled_text = filled_text.replace("{" + placeholder + "}", "")

        # Clean up any double spaces
        filled_text = re.sub(r'\s+', ' ', filled_text).strip()

        return filled_text

    def generate_description(self, location_type, time_of_day="day", weather="clear", specific_features=None):
        """
        Generate an environment description.

        Args:
            location_type: Type of location (e.g. forest, mountain, dungeon)
            time_of_day: Time of day (day, night, dawn, dusk)
            weather: Weather condition (clear, rain, snow, etc.)
            specific_features: Optional list of specific features to include

        Returns:
            A descriptive text for the environment
        """
        # Query corpus for similar location descriptions
        query_text = f"{location_type} {time_of_day} {weather}"
        corpus_results = self._query_corpus(query_text, limit=10)

        # Filter for description-like text (not dialogue)
        descriptions = [result["text"] for result in corpus_results if not result.get("is_dialogue", False)]

        if descriptions:
            # Extract patterns from corpus descriptions
            patterns = self._extract_patterns(descriptions, "description")

            if patterns:
                # Select a random pattern and fill it
                pattern = random.choice(patterns)
                description = self._fill_pattern(pattern, {
                    "location": location_type,
                    "time": time_of_day,
                    "weather": weather,
                    "feature": random.choice(specific_features) if specific_features else None
                })

                # Ensure the description mentions all important elements
                if location_type.lower() not in description.lower():
                    description = f"The {location_type} stretches before you. {description}"

                if (time_of_day.lower() not in description.lower()
                        and weather.lower() not in description.lower()):
                    description += f" The {time_of_day} brings {weather} conditions."

                return description

        # Fall back to template-based generation if corpus approach fails
        try:
            # Get templates for this location type
            location_templates = self.environment_templates.get(location_type.lower(), {})

            # For dungeons and underdark, time of day doesn't matter
            if location_type.lower() in ["dungeon", "underdark"]:
                time_templates = location_templates.get("general", [])
            else:
                # Default to day if time_of_day not available
                time_key = time_of_day.lower() if time_of_day.lower() in location_templates else "day"
                time_templates = location_templates.get(time_key, [])

            # Select a random template if available, otherwise use a generic description
            if time_templates:
                template = random.choice(time_templates)
            else:
                return f"You find yourself in a {location_type}. It is {time_of_day} and the weather is {weather}."

            # Get specific features for this location type
            feature_options = location_templates.get("specific_features", [])

            # If specific features were provided, use those, otherwise select randomly
            if specific_features:
                selected_feature = random.choice(specific_features)
            elif feature_options:
                selected_feature = random.choice(feature_options)
            else:
                selected_feature = f"The {location_type} stretches before you."

            # Replace placeholders in the template
            description = template.replace("{specific_feature}", selected_feature)

            # Add weather effects if not already included
            if weather.lower() not in description.lower() and time_of_day.lower() != "night":
                weather_effects = {
                    "clear": "The sky is clear, with sunlight illuminating the area.",
                    "cloudy": "Gray clouds hang overhead, casting shifting shadows.",
                    "rain": "Rain falls steadily, creating a rhythmic patter and slick surfaces.",
                    "storm": "A fierce storm rages, with lightning flashing and thunder rumbling in the distance.",
                    "snow": "Snowflakes drift down, covering everything in a blanket of white.",
                    "fog": "A thick fog clings to the area, limiting visibility and muffling sounds.",
                    "windy": "Strong winds whip through the area, causing smaller objects to shift and sway."
                }

                weather_desc = weather_effects.get(weather.lower(), f"The weather is {weather}.")

                # Append weather description if not already too long
                if len(description.split()) < 50:
                    description += f" {weather_desc}"

            return description

        except Exception as e:
            self.logger.error(f"Error generating description: {e}")
            return f"You find yourself in a {location_type}. It is {time_of_day} and the weather is {weather}."

    def generate_npc_dialogue(self, npc_type, npc_race, npc_attitude, situation, topic=None, npc_name=None):
        """
        Generate dialogue for an NPC.

        Args:
            npc_type: Type of NPC (e.g. merchant, guard, innkeeper)
            npc_race: Race of the NPC (e.g. human, elf, dwarf)
            npc_attitude: Attitude toward the player (friendly, neutral, hostile)
            situation: Current situation or context
            topic: Optional specific topic being discussed
            npc_name: Optional name of the NPC

        Returns:
            Dialogue text for the NPC
        """
        try:
            # Generate name if not provided
            if not npc_name:
                npc_name = self.generate_name(npc_race)

            # Build query text based on NPC attributes and topic
            query_text = f"{npc_type} {npc_attitude}"
            if topic:
                query_text += f" {topic}"

            # Query corpus for dialogue examples
            corpus_results = self._query_corpus(query_text, limit=15)

            # Filter for dialogue text
            dialogues = []
            for result in corpus_results:
                if result.get("is_dialogue", False):
                    text = result.get("text", "")
                    # Extract actual dialogue (text within quotes)
                    matches = re.findall(r'"([^"]+)"', text)
                    if matches:
                        dialogues.extend(matches)
                    else:
                        dialogues.append(text)

            if dialogues:
                # Choose a dialogue that's not too long or too short
                filtered_dialogues = [d for d in dialogues if 5 <= len(d.split()) <= 30]

                if filtered_dialogues:
                    # Select a random dialogue from the filtered list
                    dialogue = random.choice(filtered_dialogues)

                    # Personalize dialogue with situation and topic
                    if topic and topic.lower() not in dialogue.lower() and random.random() < 0.5:
                        dialogue += f" Speaking of {topic}, what do you think?"

                    if situation and situation.lower() not in dialogue.lower() and random.random() < 0.5:
                        situation_prefixes = [
                            f"In times like these, with {situation},",
                            f"Considering the {situation},",
                            f"With {situation} happening,"
                        ]
                        dialogue = f"{random.choice(situation_prefixes)} {dialogue}"

                    # Apply race-specific vocabulary and speech patterns
                    dialogue = self._apply_race_vocabulary(dialogue, npc_race.lower())
                    dialogue = self._apply_speech_pattern(dialogue, npc_race.lower())

                    # Format with NPC name
                    return f'"{dialogue}" says {npc_name}.'

            # If no suitable corpus dialogue was found, fall back to templates

            # Map NPC type to dialogue category
            type_category_map = {
                "merchant": "merchant",
                "shopkeeper": "merchant",
                "vendor": "merchant",
                "trader": "merchant",
                "guard": "guard",
                "soldier": "guard",
                "watchman": "guard",
                "sentinel": "guard",
                "innkeeper": "innkeeper",
                "barkeeper": "innkeeper",
                "tavernkeeper": "innkeeper",
                "host": "innkeeper",
                "noble": "noble",
                "aristocrat": "noble",
                "lord": "noble",
                "lady": "noble",
                "peasant": "tavernfolk",
                "farmer": "tavernfolk",
                "commoner": "tavernfolk",
                "villager": "tavernfolk",
                "sage": "sage",
                "scholar": "sage",
                "wizard": "sage",
                "mystic": "sage",
                "priest": "religious",
                "cleric": "religious",
                "acolyte": "religious",
                "monk": "religious"
            }

            # Default to tavernfolk if type not found
            dialogue_category = type_category_map.get(npc_type.lower(), "tavernfolk")

            # Map attitude to template subcategory
            attitude_map = {
                "friendly": ["friendly", "welcoming", "enthusiastic"],
                "neutral": ["neutral", "busy", "professional", "shrewd"],
                "hostile": ["hostile", "suspicious", "annoyed", "cautious"],
                "drunk": ["drunk"],
                "mysterious": ["cryptic", "mysterious"]
            }

            subcategories = attitude_map.get(npc_attitude.lower(), ["neutral"])
            subcategory = random.choice(subcategories)

            # Get dialogue templates for this category
            category_templates = self.dialogue_templates.get(dialogue_category, {})
            templates = category_templates.get(subcategory, [])

            # If no templates found, fall back to generic greeting
            if not templates:
                templates = self.dialogue_templates.get("greeting", {}).get("neutral", [])

            # Select a random template
            if templates:
                template = random.choice(templates)
            else:
                template = "Greetings, traveler."

            # Prepare replacements dictionary
            replacements = {
                "location": situation,
                "inn_name": self._generate_inn_name(),
                "amount": str(random.randint(1, 5)),
                "location_feature": f"{random.choice(['market', 'temple', 'square', 'gates', 'palace'])}",
                "illegal_activity": f"{random.choice(['smuggling', 'theft', 'trespassing', 'fighting'])}",
                "local_threat": f"{random.choice(['bandits', 'wolves', 'cultists', 'goblins'])}",
                "local_event": f"{random.choice(['festival', 'execution', 'wedding', 'coronation'])}",
                "rumor_subject": f"{random.choice(['the king', 'the mayor', 'the captain', 'the wizard'])}",
                "rumor_activity": f"{random.choice(['consorting with demons', 'hiding a secret', 'planning something big', 'falling ill'])}",
                "dangerous_location": f"{random.choice(['the old ruins', 'the dark forest', 'the caves', 'the mountains'])}",
                "scholar_name": f"{random.choice(['Azimuth', 'Thaleron', 'Mystara', 'Chronos'])}",
                "lore_snippet": f"{random.choice(['the stars were different in ancient times', 'dragons once ruled this land', 'the old kingdoms fell to a terrible curse', 'magic flows differently through these lands'])}",
                "knowledge_topic": f"{topic if topic else random.choice(['ancient history', 'magical theory', 'divine matters', 'alchemical processes'])}",
                "philosophical_concept": f"{random.choice(['balance', 'destiny', 'the nature of reality', 'the flow of time'])}",
                "evil_plan": f"{random.choice(['the ritual', 'my grand scheme', 'the awakening', 'the summoning'])}",
                "quest_objective": f"{random.choice(['retrieve a stolen artifact', 'rescue a captured merchant', 'investigate strange disappearances', 'deliver a secret message'])}"
            }

            # Perform replacements
            for key, value in replacements.items():
                template = template.replace(f"{{{key}}}", value)

            # Apply race-specific vocabulary and speech patterns
            dialogue = self._apply_race_vocabulary(template, npc_race.lower())
            dialogue = self._apply_speech_pattern(dialogue, npc_race.lower())

            # Format with NPC name if appropriate
            if dialogue_category != "greeting":
                return f'"{dialogue}" says {npc_name}.'
            else:
                return f'{npc_name}: "{dialogue}"'

        except Exception as e:
            self.logger.error(f"Error generating NPC dialogue: {e}")
            return f'{npc_name if npc_name else "The " + npc_type}: "Greetings, traveler."'

    def generate_combat_description(self, action_type, outcome, attacker, defender=None, weapon=None, spell=None,
                                    damage_amount=None):
        """
        Generate description for a combat action.

        Args:
            action_type: Type of combat action (e.g. melee_attack, ranged_attack, spell)
            outcome: Outcome of the action (hit, miss, critical_hit, critical_fail)
            attacker: Name of the attacker
            defender: Optional name of the defender
            weapon: Optional weapon being used
            spell: Optional spell being cast
            damage_amount: Optional amount of damage dealt

        Returns:
            Description of the combat action
        """
        try:
            # Set defaults for missing parameters
            if not defender:
                defender = "the enemy"
            if not weapon and action_type in ["melee_attack", "ranged_attack"]:
                weapon = "weapon" if action_type == "melee_attack" else "arrow"
            if not spell and action_type == "spell_attack":
                spell = "spell"

            # Build query text based on action type and outcome
            query_text = f"{action_type} {outcome} combat"
            if weapon:
                query_text += f" {weapon}"
            if spell:
                query_text += f" {spell}"

            # Query corpus for combat descriptions
            corpus_results = self._query_corpus(query_text, limit=10)

            # Extract combat descriptions from corpus
            combat_texts = []
            for result in corpus_results:
                text = result.get("text", "")
                # Filter for combat-like descriptions
                if re.search(r'\b(attack|hit|strike|swing|cast|spell|slash|stab|dodge|parry|block)\b', text,
                             re.IGNORECASE):
                    combat_texts.append(text)

            if combat_texts:
                # Select a combat description that's not too long or too short
                filtered_texts = [t for t in combat_texts if 10 <= len(t.split()) <= 30]

                if filtered_texts:
                    # Choose a random description
                    description = random.choice(filtered_texts)

                    # Replace names with actual attacker/defender
                    description = re.sub(r'\b[A-Z][a-z]+\b', attacker, description, count=1, flags=re.IGNORECASE)
                    if defender != "the enemy" and re.search(r'\b(enemy|foe|opponent|creature|monster)\b', description,
                                                             re.IGNORECASE):
                        description = re.sub(r'\b(enemy|foe|opponent|creature|monster)\b', defender, description,
                                             count=1, flags=re.IGNORECASE)

                    # Add weapon details if applicable
                    if weapon and weapon.lower() not in description.lower() and action_type in ["melee_attack",
                                                                                                "ranged_attack"]:
                        description = description.replace("weapon", weapon)
                        description = description.replace("blade", weapon)
                        description = description.replace("sword", weapon)

                    # Add spell details if applicable
                    if spell and spell.lower() not in description.lower() and action_type == "spell_attack":
                        description = description.replace("spell", spell)
                        description = description.replace("magic", spell)

                    # Ensure description mentions both attacker and defender
                    if attacker not in description:
                        description = f"{attacker} {description}"
                    if defender not in description and "hit" in outcome:
                        description += f" {defender} recoils from the impact."
                    elif defender not in description and "miss" in outcome:
                        description += f" {defender} evades the attack."

                    # Add damage information if provided
                    if damage_amount and "hit" in outcome:
                        damage_descriptions = [
                            f"dealing {damage_amount} damage",
                            f"inflicting {damage_amount} points of damage",
                            f"causing {damage_amount} damage"
                        ]
                        if "damage" not in description.lower():
                            description += f", {random.choice(damage_descriptions)}."

                    return description

            # Fall back to template-based generation if corpus approach fails

            # Get templates for this action type
            action_templates = self.combat_templates.get(action_type, {})
            outcome_templates = action_templates.get(outcome, [])

            # Fall back to generic templates if specific ones not found
            if not outcome_templates:
                if "hit" in outcome:
                    outcome_templates = action_templates.get("hit", [])
                elif "miss" in outcome or "fail" in outcome:
                    outcome_templates = action_templates.get("miss", [])

            # If still no templates, use a generic description
            if not outcome_templates:
                if "hit" in outcome:
                    return f"{attacker} attacks {defender} and hits."
                else:
                    return f"{attacker} attacks {defender} but misses."

            # Select a random template
            template = random.choice(outcome_templates)

            # Prepare damage description based on amount
            if damage_amount:
                if damage_amount <= 3:
                    damage_desc = "The blow causes only minor injury."
                elif damage_amount <= 7:
                    damage_desc = "The strike leaves a noticeable wound."
                elif damage_amount <= 12:
                    damage_desc = "The impact delivers a significant injury."
                elif damage_amount <= 18:
                    damage_desc = "The powerful attack inflicts a severe wound."
                else:
                    damage_desc = "The devastating blow causes catastrophic damage!"
            else:
                damage_desc = "The attack finds its mark."

            # Generate hit location
            hit_locations = ["head", "chest", "shoulder", "arm", "leg", "side", "back", "torso"]
            hit_location = random.choice(hit_locations)

            # Generate critical effects for critical hits
            critical_effects = [
                "crushing", "shattering", "slicing through", "piercing deeply into",
                "tearing into", "smashing against", "puncturing", "devastating"
            ]
            critical_effect = random.choice(critical_effects)

            # Generate fumble effects for critical fails
            fumble_effects = [
                "loses grip and drops the weapon",
                "stumbles and falls prone",
                "swings wildly, leaving an opening for counterattack",
                "the weapon becomes stuck in a nearby object",
                "accidentally hits an ally standing nearby",
                "strains a muscle, suffering minor damage"
            ]
            fumble_effect = random.choice(fumble_effects)

            # Generate spell elements for spell attacks
            spell_elements = ["fire", "ice", "lightning", "acid", "force", "necrotic", "radiant", "thunderous"]
            element = random.choice(spell_elements)

            # Generate spell backfire effects
            backfire_effects = [
                "causing it to explode prematurely",
                "the energy rebounds and strikes them instead",
                "wild magic surges uncontrollably from their hands",
                "temporarily draining their magical energy",
                "creating a spectacular but harmless light show",
                "leaving them dazed and confused"
            ]
            backfire_effect = random.choice(backfire_effects)

            # Define scenery objects for miss descriptions
            scenery_objects = ["tree", "rock", "wall", "furniture", "pillar", "statue", "ground"]
            scenery = random.choice(scenery_objects)

            # Prepare replacements dictionary
            replacements = {
                "attacker": attacker,
                "defender": defender,
                "weapon": weapon,
                "spell": spell,
                "hit_location": hit_location,
                "damage_desc": damage_desc,
                "critical_effect": critical_effect,
                "fumble_effect": fumble_effect,
                "element": element,
                "backfire_effect": backfire_effect,
                "scenery": scenery
            }

            # Perform replacements
            for key, value in replacements.items():
                template = template.replace(f"{{{key}}}", value)

            return template

        except Exception as e:
            self.logger.error(f"Error generating combat description: {e}")
            if "hit" in outcome:
                return f"{attacker} attacks {defender} and hits."
            else:
                return f"{attacker} attacks {defender} but misses."

        def generate_name(self, race: str, gender: str = None) -> str:
            """
            Generate a name for an NPC of the specified race and gender.

            Args:
                race: Race of the NPC
                gender: Optional gender of the NPC (male, female)

            Returns:
                A randomly generated name
            """
            try:
                # Normalize race to match name pattern keys
                race = self._normalize_race(race)

                # If no gender specified, randomly select one
                if not gender:
                    gender = random.choice(["male", "female"])

                # Get name patterns for this race
                race_patterns = self.name_patterns.get(race, self.name_patterns.get("human", {}))

                # For races with non-gendered names
                if race in ["dragon", "fiend", "celestial"]:
                    first_names = race_patterns.get("names", [])
                    if first_names:
                        return random.choice(first_names)
                    else:
                        return f"The {race}"

                # For races with gendered names
                first_names = race_patterns.get(gender, [])
                surnames = race_patterns.get("surname", [])

                # Generate first name
                if first_names:
                    first_name = random.choice(first_names)
                else:
                    first_name = f"{race.title()}"

                # Add surname for races that typically use them
                if race in ["human", "elf", "dwarf", "halfling"] and surnames:
                    surname = random.choice(surnames)
                    return f"{first_name} {surname}"
                else:
                    return first_name

            except Exception as e:
                self.logger.error(f"Error generating name: {e}")
                return f"The {race}"

        def generate_location_name(self, location_type: str) -> str:
            """
            Generate a name for a location of the specified type.

            Args:
                location_type: Type of location (tavern, city, dungeon, kingdom)

            Returns:
                A randomly generated location name
            """
            try:
                # Normalize location type
                location_type = location_type.lower()

                # Get name patterns for this location type
                location_patterns = self.name_patterns.get("location", {})
                names = location_patterns.get(location_type, [])

                # Return random name if available
                if names:
                    return random.choice(names)

                # Generate a name if no patterns available
                if location_type == "tavern":
                    return self._generate_inn_name()
                elif location_type == "city":
                    prefixes = ["North", "South", "East", "West", "New", "Old", "Great", "High", "Low"]
                    suffixes = ["town", "burg", "bridge", "haven", "port", "ford", "keep", "vale", "fall", "crest"]
                    return f"{random.choice(prefixes)}{random.choice(suffixes)}"
                elif location_type == "dungeon":
                    prefixes = ["Forgotten", "Ancient", "Dark", "Cursed", "Forsaken", "Hidden", "Lost", "Forbidden"]
                    suffixes = ["Tomb", "Crypt", "Cavern", "Ruin", "Pit", "Temple", "Sanctuary", "Vault", "Catacomb"]
                    return f"The {random.choice(prefixes)} {random.choice(suffixes)}"
                elif location_type == "kingdom":
                    prefixes = ["Kingdom of ", "Realm of ", "Empire of ", "Dominion of ", ""]
                    suffixes = ["land", "gard", "mark", "heim", "ia", "or", "ath", "aria", "oria", "elle"]
                    return f"{random.choice(prefixes)}{self._generate_fantasy_word(random.randint(2, 3))}{random.choice(suffixes)}"
                else:
                    return f"The {location_type}"

            except Exception as e:
                self.logger.error(f"Error generating location name: {e}")
                return f"The {location_type}"

        def generate_quest(self, quest_type=None, difficulty="medium", level=1, location=None):
            """
            Generate a quest with details based on type, difficulty, and level.

            Args:
                quest_type: Optional type of quest (rescue, investigation, etc.)
                difficulty: Difficulty level of the quest
                level: Character level the quest is designed for
                location: Optional location for the quest

            Returns:
                Dictionary containing quest details
            """
            try:
                # If no quest type specified, randomly select one
                if not quest_type:
                    quest_types = ["rescue", "investigation", "retrieval", "elimination",
                                   "protection", "escort", "mystery", "intrigue", "exploration"]
                    quest_type = random.choice(quest_types)
                else:
                    # Normalize quest type
                    quest_type = quest_type.lower()

                # Build query based on quest type
                query_text = f"{quest_type} quest mission task"

                # Query corpus for quest descriptions
                corpus_results = self._query_corpus(query_text, limit=15)

                # Extract quest-like descriptions
                quest_texts = []
                for result in corpus_results:
                    text = result.get("text", "")
                    # Filter for quest-like descriptions
                    if len(text.split()) >= 10 and len(text.split()) <= 50:
                        quest_texts.append(text)

                # Generate default hook if no corpus results found
                if not quest_texts:
                    hooks = self.story_hooks.get(quest_type, self.story_hooks.get("rescue", []))
                    if hooks:
                        hook = random.choice(hooks)
                    else:
                        hook = "A mysterious quest awaits brave adventurers."
                else:
                    # Generate hook from corpus
                    hook = random.choice(quest_texts)

                # Generate location if not provided
                if not location:
                    if quest_type in ["investigation", "rescue", "protection"]:
                        location_types = ["tavern", "city", "village", "town"]
                    elif quest_type in ["retrieval", "elimination", "exploration"]:
                        location_types = ["dungeon", "wilderness", "ruin", "cave"]
                    else:
                        location_types = ["tavern", "city", "dungeon", "wilderness"]

                    location_type = random.choice(location_types)
                    location = self.generate_location_name(location_type)

                # Extract key elements from the hook for title generation
                key_elements = self._extract_key_elements(hook)

                # Generate title
                title = self._generate_quest_title(quest_type, hook)

                # Create or enhance description from hook
                description = self._elaborate_quest_description(hook, quest_type, location,
                                                                self._generate_quest_enemies(difficulty, level))

                # Set rewards based on difficulty and level
                rewards = self._generate_quest_rewards(difficulty, level)

                # Generate appropriate enemies based on level
                enemies = self._generate_quest_enemies(difficulty, level)

                # Create quest dictionary
                quest = {
                    "title": title,
                    "hook": hook,
                    "type": quest_type,
                    "difficulty": difficulty,
                    "level": level,
                    "location": location,
                    "giver": self.generate_name("human"),
                    "rewards": rewards,
                    "enemies": enemies,
                    "description": description
                }

                return quest

            except Exception as e:
                self.logger.error(f"Error generating quest: {e}")
                return {
                    "title": "A Simple Task",
                    "hook": "A simple task is requested of brave adventurers.",
                    "type": "retrieval",
                    "difficulty": difficulty,
                    "level": level,
                    "location": location if location else "nearby",
                    "giver": "Village Elder",
                    "rewards": {"gold": 50 * level, "items": []},
                    "enemies": [{"name": "Bandits", "challenge": "easy"}],
                    "description": "The village elder asks for help retrieving a stolen item from bandits in the area."
                }

        def generate_story_hook(self, theme=None, length="medium"):
            """
            Generate a story hook or plot element from the corpus.

            Args:
                theme: Optional theme for the hook (e.g., betrayal, mystery, revenge)
                length: Desired length of the hook (short, medium, long)

            Returns:
                A story hook string
            """
            try:
                # Build query based on theme
                query_text = "quest adventure mission"
                if theme:
                    query_text += f" {theme}"

                # Query corpus for potential hooks
                corpus_results = self._query_corpus(query_text, limit=20)

                # Define desired length in words
                if length == "short":
                    min_words, max_words = 10, 20
                elif length == "long":
                    min_words, max_words = 30, 50
                else:  # medium
                    min_words, max_words = 20, 30

                # Extract sentences of appropriate length
                potential_hooks = []
                for result in corpus_results:
                    text = result.get("text", "")
                    # Split into sentences
                    sentences = re.split(r'[.!?]', text)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        word_count = len(sentence.split())
                        if min_words <= word_count <= max_words:
                            potential_hooks.append(sentence)

                # Select a hook that has interesting elements
                interesting_hooks = []
                for hook in potential_hooks:
                    # Check for interesting elements like danger, treasure, mystery
                    if re.search(r'\b(danger|treasure|secret|mystery|ancient|power|evil|threat|magic)\b',
                                 hook, re.IGNORECASE):
                        interesting_hooks.append(hook)

                if interesting_hooks:
                    return random.choice(interesting_hooks)
                elif potential_hooks:
                    return random.choice(potential_hooks)
                else:
                    # Fall back to generic hook
                    generic_hooks = [
                        "A mysterious stranger approaches with an urgent request.",
                        "An ancient evil stirs beneath the ruins of a forgotten civilization.",
                        "A valuable artifact has been stolen and must be recovered.",
                        "Strange disappearances in the nearby village require investigation.",
                        "A powerful noble seeks capable adventurers for a dangerous mission."
                    ]
                    return random.choice(generic_hooks)

            except Exception as e:
                self.logger.error(f"Error generating story hook: {e}")
                return "A mysterious quest awaits brave adventurers."

        def generate_world_detail(self, location_type, detail_type="rumors", faction=None):
            """
            Generate a world-building detail for a location.

            Args:
                location_type: Type of location (town, forest, dungeon, etc.)
                detail_type: Type of detail (rumors, history, factions, features)
                faction: Optional faction to include in the detail

            Returns:
                A string containing the world detail
            """
            try:
                # Build query based on location and detail type
                query_text = f"{location_type} {detail_type}"
                if faction:
                    query_text += f" {faction}"

                # Query corpus for related text
                corpus_results = self._query_corpus(query_text, limit=15)

                # Extract suitable descriptions
                details = []
                for result in corpus_results:
                    text = result.get("text", "")
                    # Filter based on length
                    if 15 <= len(text.split()) <= 40:
                        details.append(text)

                if details:
                    # Select a random detail
                    detail = random.choice(details)

                    # Customize with location name if needed
                    if location_type.lower() not in detail.lower():
                        detail = re.sub(r'\b(place|location|area|region)\b', location_type, detail,
                                        flags=re.IGNORECASE)

                    # Add faction if provided and not already mentioned
                    if faction and faction.lower() not in detail.lower():
                        faction_additions = [
                            f"The {faction} are rumored to be involved.",
                            f"Members of the {faction} have been seen in the area.",
                            f"This has attracted the attention of the {faction}."
                        ]
                        detail += f" {random.choice(faction_additions)}"

                    return detail

                # Fall back to template-based generation
                if detail_type == "rumors":
                    templates = [
                        f"Locals whisper about strange occurrences in the {location_type}.",
                        f"Rumors speak of hidden treasure within the {location_type}.",
                        f"People avoid the {location_type} after dark due to eerie sounds.",
                        f"An ancient power is said to slumber beneath the {location_type}.",
                        f"Travelers report unusual creatures lurking in the {location_type}."
                    ]
                elif detail_type == "history":
                    templates = [
                        f"The {location_type} was once a battleground in a forgotten war.",
                        f"Ancient civilizations built grand structures in this {location_type}.",
                        f"The {location_type} has changed hands many times throughout history.",
                        f"Legends tell of a great cataclysm that shaped this {location_type}.",
                        f"This {location_type} holds significance in local folklore."
                    ]
                elif detail_type == "factions":
                    templates = [
                        f"The {faction if faction else 'local guild'} maintains a strong presence here.",
                        f"Two rival groups compete for control of the {location_type}.",
                        f"Hidden agents watch over activities in the {location_type}.",
                        f"The {faction if faction else 'ruling faction'} carefully monitors all visitors.",
                        f"Various factions use the {location_type} as neutral meeting ground."
                    ]
                else:  # features
                    templates = [
                        f"A distinctive landmark dominates the {location_type}.",
                        f"Unusual flora can be found throughout the {location_type}.",
                        f"Natural formations create maze-like passages in the {location_type}.",
                        f"The {location_type} contains resources highly prized by crafters.",
                        f"Weather patterns in the {location_type} are unpredictable and extreme."
                    ]

                return random.choice(templates)

            except Exception as e:
                self.logger.error(f"Error generating world detail: {e}")
                return f"The {location_type} holds many secrets waiting to be discovered."

        def generate_narrative_transition(self, from_scene, to_scene, mood="neutral", time_passed="immediate"):
            """
            Generate a narrative transition between scenes.

            Args:
                from_scene: Description of the current scene
                to_scene: Description of the scene transitioning to
                mood: Emotional tone of the transition
                time_passed: Amount of time passed during transition

            Returns:
                Narrative text describing the transition between scenes
            """
            try:
                # Build query based on mood and time passed
                query_text = f"{mood} {time_passed} journey travel"

                # Query corpus for transition examples
                corpus_results = self._query_corpus(query_text, limit=10)

                # Extract suitable transition texts (paragraphs that describe movement/transition)
                transitions = []
                for result in corpus_results:
                    text = result.get("text", "")
                    # Look for texts with movement words
                    if re.search(r'\b(travel|journey|path|road|walk|moved|passage|continue|proceed)\b', text,
                                 re.IGNORECASE):
                        transitions.append(text)

                if transitions:
                    # Select a transition that's not too long
                    filtered_transitions = [t for t in transitions if 15 <= len(t.split()) <= 40]

                    if filtered_transitions:
                        # Choose a random transition
                        transition_text = random.choice(filtered_transitions)

                        # Customize the transition with scene names
                        if from_scene.lower() not in transition_text.lower():
                            transition_text = transition_text.replace("the area", from_scene)
                            transition_text = transition_text.replace("their location", from_scene)

                        if to_scene.lower() not in transition_text.lower():
                            transition_text = transition_text.replace("destination", to_scene)
                            transition_text = transition_text.replace("their goal", to_scene)

                        # Ensure transition mentions both locations
                        if from_scene.lower() not in transition_text.lower() and to_scene.lower() not in transition_text.lower():
                            transition_text += f" The party leaves {from_scene} behind as they approach {to_scene}."

                        # Add a sensory detail based on the mood
                        sensory_details = {
                            "neutral": [
                                "Birds call in the distance.",
                                "A light breeze stirs the air.",
                                "The familiar sounds of travel accompany them."
                            ],
                            "tense": [
                                "Twigs snap underfoot, each sound magnified in the silence.",
                                "The air feels thick with unspoken danger.",
                                "Shadows seem to move at the edge of vision."
                            ],
                            "triumphant": [
                                "The sun breaks through the clouds, as if celebrating their victory.",
                                "Their voices carry through the air, spirits unburdened.",
                                "Even the challenges ahead seem conquerable now."
                            ],
                            "somber": [
                                "Rain begins to fall, mirroring the mood.",
                                "The world itself seems muted, colors less vibrant.",
                                "Silence hangs between them, words unnecessary."
                            ],
                            "mysterious": [
                                "Strange lights flicker just beyond clear vision.",
                                "The air tingles with unknown energies.",
                                "Sounds carry oddly, echoing when they shouldn't."
                            ],
                            "hopeful": [
                                "The first stars appear overhead, like distant promises.",
                                "Wildflowers brighten the path, springing up in unlikely places.",
                                "The air feels fresh with possibility."
                            ]
                        }

                        if random.random() < 0.7:  # 70% chance to add sensory detail
                            sensory_options = sensory_details.get(mood, sensory_details["neutral"])
                            transition_text += " " + random.choice(sensory_options)

                        return transition_text

                # Fall back to template-based generation if corpus approach fails

                # Time transition phrases
                time_transitions = {
                    "immediate": [
                        "Without delay", "In the next moment", "Immediately",
                        "Straight away", "All at once", "At once"
                    ],
                    "short": [
                        "Shortly thereafter", "After a brief respite", "A short while later",
                        "Within the hour", "Before long", "After a brief journey"
                    ],
                    "medium": [
                        "Several hours later", "As time passes", "After resting",
                        "When next we find our heroes", "The journey takes several hours",
                        "Later that day"
                    ],
                    "long": [
                        "Days later", "After a long journey", "The following day",
                        "Having traveled for many leagues", "After an arduous trek",
                        "The next morning"
                    ],
                    "very_long": [
                        "Weeks pass", "After many days of travel", "A fortnight later",
                        "The seasons begin to change", "Following a long and difficult journey",
                        "Many moons later"
                    ]
                }

                # Mood-specific transition phrases
                mood_transitions = {
                    "neutral": [
                        "The party continues", "Moving forward", "The adventure continues",
                        "Pressing on", "Continuing their quest", "The journey leads"
                    ],
                    "tense": [
                        "With nerves on edge", "Alert to every sound", "Tension mounting",
                        "Every shadow conceals potential danger", "Hands never straying far from weapons",
                        "The oppressive feeling grows"
                    ],
                    "triumphant": [
                        "Buoyed by their success", "Spirits high from victory", "Confidence bolstered",
                        "Riding the wave of triumph", "Having conquered the challenge",
                        "Success fresh in their minds"
                    ],
                    "somber": [
                        "Weighted by recent events", "With heavy hearts", "Solemnly",
                        "The mood subdued", "Reflection weighs on each step",
                        "Grief and duty driving them forward"
                    ],
                    "mysterious": [
                        "Following cryptic signs", "Drawn by mysterious forces", "The strange path leads",
                        "Guided by unknown purpose", "Mysteries beckoning them forward",
                        "Strange omens marking their path"
                    ],
                    "hopeful": [
                        "With renewed purpose", "Hope kindling in their hearts", "Spirits lifting",
                        "The path ahead seeming brighter", "Determination growing",
                        "A sense of possibility driving them forward"
                    ]
                }

                # Get transition phrases based on time and mood
                time_phrases = time_transitions.get(time_passed, time_transitions["immediate"])
                mood_phrases = mood_transitions.get(mood, mood_transitions["neutral"])

                # Select random phrases
                time_phrase = random.choice(time_phrases)
                mood_phrase = random.choice(mood_phrases)

                # Generate the transition text
                transition = f"{time_phrase}, {mood_phrase} from {from_scene} to {to_scene}. "

                # Add a sensory detail based on the mood
                sensory_details = {
                    "neutral": [
                        "Birds call in the distance.",
                        "A light breeze stirs the air.",
                        "The familiar sounds of travel accompany them."
                    ],
                    "tense": [
                        "Twigs snap underfoot, each sound magnified in the silence.",
                        "The air feels thick with unspoken danger.",
                        "Shadows seem to move at the edge of vision."
                    ],
                    "triumphant": [
                        "The sun breaks through the clouds, as if celebrating their victory.",
                        "Their voices carry through the air, spirits unburdened.",
                        "Even the challenges ahead seem conquerable now."
                    ],
                    "somber": [
                        "Rain begins to fall, mirroring the mood.",
                        "The world itself seems muted, colors less vibrant.",
                        "Silence hangs between them, words unnecessary."
                    ],
                    "mysterious": [
                        "Strange lights flicker just beyond clear vision.",
                        "The air tingles with unknown energies.",
                        "Sounds carry oddly, echoing when they shouldn't."
                    ],
                    "hopeful": [
                        "The first stars appear overhead, like distant promises.",
                        "Wildflowers brighten the path, springing up in unlikely places.",
                        "The air feels fresh with possibility."
                    ]
                }

                sensory_options = sensory_details.get(mood, sensory_details["neutral"])
                transition += random.choice(sensory_options)

                return transition

            except Exception as e:
                self.logger.error(f"Error generating narrative transition: {e}")
                return f"The party travels from {from_scene} to {to_scene}."

        def _apply_race_vocabulary(self, text: str, race: str) -> str:
            """Apply race-specific vocabulary replacements to text."""
            # Get vocabulary for this race
            vocabulary = self.race_vocabulary.get(race, {})

            # If no vocabulary for this race, return unchanged
            if not vocabulary:
                return text

            # Apply replacements
            modified_text = text
            for original, replacement in vocabulary.items():
                # Only replace whole words
                modified_text = re.sub(r'\b' + re.escape(original) + r'\b', replacement, modified_text,
                                       flags=re.IGNORECASE)

            return modified_text

        def _apply_speech_pattern(self, text: str, race: str) -> str:
            """Apply race-specific speech patterns to text."""
            # Get speech patterns for this race
            patterns = self.race_speech_patterns.get(race, [])

            # If no patterns for this race, return unchanged
            if not patterns:
                return text

            # Apply up to two random patterns
            num_patterns = min(2, len(patterns))
            selected_patterns = random.sample(patterns, num_patterns)

            modified_text = text

            for pattern in selected_patterns:
                # Apply specific pattern transformations
                if pattern == "speaking_formally":
                    modified_text = modified_text.replace("you", "thee").replace("your", "thy")
                elif pattern == "poetic_phrasing" and len(modified_text.split()) > 5:
                    words = modified_text.split()
                    insert_pos = len(words) // 2
                    poetic_phrases = ["like leaves in autumn", "as stars would guide", "in harmony with nature"]
                    modified_text = " ".join(words[:insert_pos]) + " " + random.choice(poetic_phrases) + " " + " ".join(
                        words[insert_pos:])
                elif pattern == "simple_sentences" and "," in modified_text:
                    # Simplify sentences by removing clauses
                    modified_text = ". ".join([s.split(",")[0] for s in modified_text.split(".")])
                elif pattern == "third_person_references" and random.random() < 0.5:
                    # Sometimes refer to self in third person
                    modified_text = modified_text.replace("I ", f"{race.title()} ")
                elif pattern == "sentence_start_by_my_beard" and not modified_text.startswith("By my beard"):
                    modified_text = "By my beard, " + modified_text
                elif pattern == "sentence_end_or_I_am_no_dwarf" and not modified_text.endswith("or I am no dwarf"):
                    modified_text = modified_text.rstrip(".!?") + ", or I am no dwarf!"
                elif pattern == "sentence_start_well_now" and not modified_text.startswith("Well now"):
                    modified_text = "Well now, " + modified_text
                elif pattern == "sentence_end_if_you_catch_my_meaning" and not modified_text.endswith(
                        "if you catch my meaning"):
                    modified_text = modified_text.rstrip(".!?") + ", if you catch my meaning."

            return modified_text

        def _load_dialogue_templates(self):
            """Load dialogue templates from database."""
            # Default templates if file not found
            self.dialogue_templates = {
                "greeting": ["Hello, traveler.", "Greetings, adventurer."],
                "farewell": ["Farewell.", "Safe travels."],
                "tavern": ["What'll it be?", "Looking for a drink?"],
                "merchant": ["I've got wares if you've got coin.", "See anything you like?"],
                "guard": ["Move along.", "Keep out of trouble."],
                "quest_giver": ["I need your help.", "I have a task for capable adventurers."],
                "combat": ["Prepare to die!", "You'll regret this!"],
                "victory": ["We've done it!", "Victory is ours!"],
                "defeat": ["We must retreat!", "Fall back!"]
            }

            # Try to load templates from file
            template_path = os.path.join(self.database_path, "dialogue_templates.json")
            try:
                if os.path.exists(template_path):
                    with open(template_path, 'r') as f:
                        self.dialogue_templates = json.load(f)
                    self.logger.info(f"Loaded dialogue templates from {template_path}")
                else:
                    self.logger.warning(f"Dialogue templates file not found: {template_path}, using defaults")
            except Exception as e:
                self.logger.error(f"Error loading dialogue templates: {e}")

        def _load_dialogue_templates(self):
            """Load dialogue templates from database."""
            # Default templates if file not found
            self.dialogue_templates = {
                "greeting": ["Hello, traveler.", "Greetings, adventurer."],
                "farewell": ["Farewell.", "Safe travels."],
                "tavern": ["What'll it be?", "Looking for a drink?"],
                "merchant": ["I've got wares if you've got coin.", "See anything you like?"],
                "guard": ["Move along.", "Keep out of trouble."],
                "quest_giver": ["I need your help.", "I have a task for capable adventurers."],
                "combat": ["Prepare to die!", "You'll regret this!"],
                "victory": ["We've done it!", "Victory is ours!"],
                "defeat": ["We must retreat!", "Fall back!"]
            }

            # Try to load templates from file
            template_path = os.path.join(self.database_path, "dialogue_templates.json")
            try:
                if os.path.exists(template_path):
                    with open(template_path, 'r') as f:
                        self.dialogue_templates = json.load(f)
                    self.logger.info(f"Loaded dialogue templates from {template_path}")
                else:
                    self.logger.warning(f"Dialogue templates file not found: {template_path}, using defaults")
            except Exception as e:
                self.logger.error(f"Error loading dialogue templates: {e}")

        def _load_environment_templates(self) -> Dict[str, Dict[str, List[str]]]:
            """
            Load environment description templates for different location types.

            Returns:
                Dictionary of environment templates by location type and time of day
            """
            # Implementation of loading environment templates
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_combat_templates(self) -> Dict[str, Dict[str, List[str]]]:
            """
            Load combat description templates for different action types.

            Returns:
                Dictionary of combat templates by action type and success/failure
            """
            # Implementation of loading combat templates
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_race_vocabulary(self) -> Dict[str, Dict[str, str]]:
            """
            Load vocabulary replacements for different races, dialects, and backgrounds.

            Returns:
                Dictionary of vocabulary replacements by race/dialect
            """
            # Implementation of loading race vocabulary
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_race_speech_patterns(self) -> Dict[str, List[str]]:
            """
            Load speech patterns for different races and backgrounds.

            Returns:
                Dictionary of speech patterns by race/background
            """
            # Implementation of loading race speech patterns
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_name_patterns(self) -> Dict[str, Dict[str, List[str]]]:
            """
            Load name patterns for NPCs and locations by race/region.

            Returns:
                Dictionary of name patterns by race/region and gender
            """
            # Implementation of loading name patterns
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_fantasy_phrases(self) -> Dict[str, List[str]]:
            """
            Load fantasy phrases and idioms.

            Returns:
                Dictionary of fantasy phrases and idioms by type
            """
            # Implementation of loading fantasy phrases
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_modern_replacements(self) -> Dict[str, str]:
            """
            Load modern term replacements.

            Returns:
                Dictionary of modern terms and their fantasy replacements
            """
            # Implementation of loading modern replacements
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier

        def _load_story_hooks(self) -> Dict[str, List[str]]:
            """
            Load story hooks and plot elements.

            Returns:
                Dictionary of story hooks by theme
            """
            # Implementation of loading story hooks
            # In a full implementation, this would load from files
            # This method is already defined earlier in the code
            return {}  # Placeholder since this is defined earlier