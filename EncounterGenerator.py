# EncounterEngine/EncounterEngine.py
import random
import math
from typing import Dict, List, Any, Optional


class EncounterGenerator:
    """Generates balanced encounters based on party composition and environment."""

    def __init__(self, database_path=None):
        """
        Initialize the encounter generator.

        Args:
            database_path: Optional path to monster database
        """
        self.default_environment_monsters = {
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

        # Challenge rating ranges by character level
        self.cr_by_level = {
            1: {"easy": 0.125, "medium": 0.25, "hard": 0.5, "deadly": 1},
            2: {"easy": 0.25, "medium": 0.5, "hard": 1, "deadly": 2},
            3: {"easy": 0.5, "medium": 1, "hard": 2, "deadly": 3},
            4: {"easy": 0.5, "medium": 1, "hard": 2, "deadly": 4},
            5: {"easy": 1, "medium": 2, "hard": 3, "deadly": 6},
            6: {"easy": 1, "medium": 3, "hard": 4, "deadly": 7},
            7: {"easy": 2, "medium": 4, "hard": 5, "deadly": 8},
            8: {"easy": 2, "medium": 4, "hard": 6, "deadly": 9},
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

        # XP thresholds by character level
        self.xp_thresholds = {
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

    def create_encounter(self, party, location_type, difficulty="medium"):
        """
        Create a balanced combat encounter for the party.

        Args:
            party: List of player characters
            location_type: Environment type for the encounter
            difficulty: Encounter difficulty level

        Returns:
            Dictionary with encounter details
        """
        if not party:
            return {"status": "error", "message": "No party data provided"}

        # Calculate average party level and size
        party_size = len(party)
        avg_party_level = sum(char.get("level", 1) for char in party) / party_size
        avg_party_level = int(round(avg_party_level))  # Round to nearest level

        # Calculate target XP based on party composition and difficulty
        target_xp = self._calculate_target_xp(party, difficulty)

        # Get suitable monsters for this environment and level
        suitable_monsters = self._filter_suitable_monsters(location_type, avg_party_level, difficulty)

        if not suitable_monsters:
            # Fall back to default monsters with more intelligent selection
            default_monsters = self._get_default_monsters(location_type, avg_party_level)

            return {
                "status": "success",
                "monsters": default_monsters,
                "difficulty": difficulty,
                "note": "Using default monsters for this environment",
                "total_xp": sum(monster.get("xp", 0) for monster in default_monsters),
                "location_type": location_type
            }

        # Select monsters to create a balanced encounter
        selected_monsters = self._select_monsters(suitable_monsters, target_xp, difficulty, party_size)

        # Apply encounter multiplier based on number of monsters
        multiplier = self._get_encounter_multiplier(len(selected_monsters), party_size)
        adjusted_xp = sum(monster.get("xp", 0) for monster in selected_monsters) * multiplier

        return {
            "status": "success",
            "monsters": selected_monsters,
            "difficulty": difficulty,
            "target_xp": target_xp,
            "actual_xp": adjusted_xp,
            "encounter_multiplier": multiplier,
            "location_type": location_type
        }

    def _calculate_target_xp(self, party, difficulty):
        """
        Calculate target XP for an encounter based on party composition.

        Args:
            party: List of player characters
            difficulty: Encounter difficulty level

        Returns:
            Target XP value
        """
        total_xp = 0

        # Sum individual thresholds
        for character in party:
            level = character.get("level", 1)
            level = min(20, max(1, level))  # Ensure level is between 1 and 20

            # Get threshold for this character's level and difficulty
            threshold = self.xp_thresholds.get(level, {}).get(difficulty, 0)
            total_xp += threshold

        # Adjust for party size
        party_size = len(party)

        if party_size < 3:
            # Small party needs weaker encounters
            total_xp *= 0.8
        elif party_size > 5:
            # Large party can handle stronger encounters
            total_xp *= 1.2

        return int(total_xp)

    def _filter_suitable_monsters(self, location_type, party_level, difficulty):
        """
        Filter monsters suitable for the location and party level.

        Args:
            location_type: Environment type for the encounter
            party_level: Average party level
            difficulty: Encounter difficulty level

        Returns:
            List of suitable monster dictionaries
        """
        # In a real implementation, this would query the monster database
        # For now, use a simplified approach with default monsters

        # Get CR range for this level and difficulty
        cr_range = self.cr_by_level.get(party_level, {}).get(difficulty, 1)

        # Adjust CR range based on difficulty
        if difficulty == "easy":
            min_cr = cr_range / 2
            max_cr = cr_range * 1.5
        elif difficulty == "medium":
            min_cr = cr_range / 1.5
            max_cr = cr_range * 2
        elif difficulty == "hard":
            min_cr = cr_range / 1.2
            max_cr = cr_range * 3
        elif difficulty == "deadly":
            min_cr = cr_range
            max_cr = cr_range * 4
        else:
            min_cr = cr_range / 2
            max_cr = cr_range * 2

        # For now, return some simulated monsters
        suitable_monsters = []

        # Get default monsters for this environment
        default_monsters = self.default_environment_monsters.get(location_type, [])

        # Create monster entries with appropriate CR
        for monster_name in default_monsters:
            # Randomize CR within range
            cr = min_cr + random.random() * (max_cr - min_cr)

            # Ensure minimum CR of 0.125
            cr = max(0.125, cr)

            monster = {
                "name": monster_name,
                "cr": cr,
                "xp": self._calculate_xp_from_cr(cr),
                "hp": int(cr * 15 + random.randint(5, 15)),  # Approximate HP based on CR
                "environment": location_type
            }

            suitable_monsters.append(monster)

        return suitable_monsters

    def _select_monsters(self, monsters, target_xp, difficulty, party_size):
        """
        Select a combination of monsters for the encounter.

        Args:
            monsters: List of potential monsters
            target_xp: Target XP for the encounter
            difficulty: Encounter difficulty level
            party_size: Number of players in the party

        Returns:
            List of selected monsters
        """
        # Sort monsters by XP (ascending)
        sorted_monsters = sorted(monsters, key=lambda m: m.get("xp", 0))

        # Determine number of monsters based on difficulty and party size
        if difficulty == "easy":
            max_monsters = max(1, party_size - 1)
        elif difficulty == "medium":
            max_monsters = party_size
        elif difficulty == "hard":
            max_monsters = party_size + 1
        elif difficulty == "deadly":
            max_monsters = party_size + 2
        else:
            max_monsters = party_size

        # Adjust based on party size
        if party_size <= 2:
            max_monsters = max(1, max_monsters - 1)
        elif party_size >= 6:
            max_monsters = max_monsters + 1

        # Calculate encounter multiplier for different monster counts
        encounter_multipliers = {}
        for count in range(1, max_monsters + 1):
            encounter_multipliers[count] = self._get_encounter_multiplier(count, party_size)

        # Try different combinations of monsters
        best_selection = []
        best_xp_diff = float('inf')

        # Try different numbers of monsters
        for num_monsters in range(1, max_monsters + 1):
            # Adjust target XP based on encounter multiplier
            adjusted_target = target_xp / encounter_multipliers[num_monsters]

            # Try to find a combination close to the adjusted target
            current_selection = []
            current_xp = 0

            # For simplicity, use a greedy approach
            remaining_monsters = sorted_monsters.copy()

            # If we want multiple monsters, prioritize variety
            if num_monsters > 1:
                # Start with a stronger monster
                high_index = len(remaining_monsters) - 1
                while high_index >= 0 and current_xp + remaining_monsters[high_index]["xp"] <= adjusted_target:
                    current_selection.append(remaining_monsters[high_index])
                    current_xp += remaining_monsters[high_index]["xp"]
                    break  # Just add one stronger monster

            # Fill in with appropriate monsters
            for _ in range(len(current_selection), num_monsters):
                found = False

                # Find a monster that fits within remaining XP
                for i, monster in enumerate(remaining_monsters):
                    if monster in current_selection:
                        continue

                    if current_xp + monster["xp"] <= adjusted_target:
                        current_selection.append(monster)
                        current_xp += monster["xp"]
                        found = True
                        break

                if not found and remaining_monsters:
                    # If no monster fits, add the smallest one
                    smallest = remaining_monsters[0]
                    for monster in remaining_monsters:
                        if monster not in current_selection and monster["xp"] < smallest["xp"]:
                            smallest = monster

                    current_selection.append(smallest)
                    current_xp += smallest["xp"]

            # Apply actual encounter multiplier to compare with target
            actual_xp = current_xp * encounter_multipliers[num_monsters]
            xp_diff = abs(actual_xp - target_xp)

            if xp_diff < best_xp_diff:
                best_selection = current_selection
                best_xp_diff = xp_diff

        # If no monsters selected, choose the one closest to target XP
        if not best_selection and sorted_monsters:
            best_monster = min(sorted_monsters, key=lambda m: abs(m.get("xp", 0) - target_xp))
            best_selection = [best_monster]

        return best_selection

    def _get_default_monsters(self, location_type, party_level):
        """
        Get default monsters for a given location type with appropriate CR.

        Args:
            location_type: Environment type
            party_level: Average party level

        Returns:
            List of monster dictionaries
        """
        default_monsters = self.default_environment_monsters.get(location_type,
                                                                 self.default_environment_monsters["dungeon"])

        # Scale CR based on party level
        scaled_cr = max(0.25, party_level / 4)  # Minimum CR of 1/4

        # Convert monster names to monster dictionaries with scaled stats
        monster_dicts = []
        for name in default_monsters[:3]:  # Limit to 3 monsters
            monster_dicts.append({
                'name': name,
                'cr': scaled_cr,  # Scale CR with party level
                'xp': self._calculate_xp_from_cr(scaled_cr),
                'hp': int(scaled_cr * 15 + random.randint(5, 15)),  # Approximate HP based on CR
                'environment': location_type
            })

        return monster_dicts

    def _calculate_xp_from_cr(self, cr):
        """
        Calculate XP value from Challenge Rating.

        Args:
            cr: Challenge Rating value

        Returns:
            XP value
        """
        # XP by CR table from D&D 5e
        xp_table = {
            0: 10,
            0.125: 25,
            0.25: 50,
            0.5: 100,
            1: 200,
            2: 450,
            3: 700,
            4: 1100,
            5: 1800,
            6: 2300,
            7: 2900,
            8: 3900,
            9: 5000,
            10: 5900,
            11: 7200,
            12: 8400,
            13: 10000,
            14: 11500,
            15: 13000,
            16: 15000,
            17: 18000,
            18: 20000,
            19: 22000,
            20: 25000,
            21: 33000,
            22: 41000,
            23: 50000,
            24: 62000,
            25: 75000,
            26: 90000,
            27: 105000,
            28: 120000,
            29: 135000,
            30: 155000
        }

        # Find exact match or nearest CR
        if cr in xp_table:
            return xp_table[cr]

        # Handle intermediate CRs
        lower_cr = max([c for c in xp_table.keys() if c < cr], default=0)
        higher_cr = min([c for c in xp_table.keys() if c > cr], default=30)

        # Linear interpolation
        lower_xp = xp_table[lower_cr]
        higher_xp = xp_table[higher_cr]

        if higher_cr == lower_cr:
            return lower_xp

        ratio = (cr - lower_cr) / (higher_cr - lower_cr)
        return int(lower_xp + ratio * (higher_xp - lower_xp))

    def _get_encounter_multiplier(self, num_monsters, party_size):
        """
        Get the encounter multiplier based on number of monsters.

        Args:
            num_monsters: Number of monsters in the encounter
            party_size: Number of players in the party

        Returns:
            Encounter multiplier
        """
        # Standard 5e encounter multipliers
        if num_monsters == 1:
            return 1.0
        elif num_monsters == 2:
            return 1.5
        elif 3 <= num_monsters <= 6:
            return 2.0
        elif 7 <= num_monsters <= 10:
            return 2.5
        elif 11 <= num_monsters <= 14:
            return 3.0
        else:
            return 4.0