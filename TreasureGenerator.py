# EncounterEngine/TreasureGenerator.py
import random
import math
from typing import Dict, List, Any, Optional


class TreasureGenerator:
    """Generates treasure rewards for encounters."""

    def __init__(self):
        """Initialize the treasure generator."""
        # Define treasure tables
        self.treasure_tables = {
            "individual": {
                "low": [  # CR 0-4
                    {"dice": "5d6", "multiplier": 1, "type": "cp"},
                    {"dice": "4d6", "multiplier": 1, "type": "sp"},
                    {"dice": "3d6", "multiplier": 1, "type": "gp"},
                    {"dice": "1d6", "multiplier": 1, "type": "pp"}
                ],
                "medium": [  # CR 5-10
                    {"dice": "4d6", "multiplier": 10, "type": "cp"},
                    {"dice": "3d6", "multiplier": 10, "type": "sp"},
                    {"dice": "2d6", "multiplier": 10, "type": "gp"},
                    {"dice": "1d6", "multiplier": 10, "type": "pp"}
                ],
                "high": [  # CR 11-16
                    {"dice": "2d6", "multiplier": 100, "type": "sp"},
                    {"dice": "2d6", "multiplier": 100, "type": "gp"},
                    {"dice": "2d6", "multiplier": 10, "type": "pp"}
                ],
                "very_high": [  # CR 17+
                    {"dice": "2d6", "multiplier": 1000, "type": "gp"},
                    {"dice": "3d6", "multiplier": 100, "type": "pp"}
                ]
            },
            "hoard": {
                "low": {
                    "coins": [
                        {"dice": "6d6", "multiplier": 100, "type": "cp"},
                        {"dice": "3d6", "multiplier": 100, "type": "sp"},
                        {"dice": "2d6", "multiplier": 10, "type": "gp"}
                    ],
                    "items": {
                        "gems": {"chance": 0.6, "dice": "2d6", "value": 10},
                        "art": {"chance": 0.3, "dice": "1d6", "value": 25},
                        "magic_items": {"chance": 0.2, "table": "A", "dice": "1d6"}
                    }
                },
                "medium": {
                    "coins": [
                        {"dice": "2d6", "multiplier": 100, "type": "sp"},
                        {"dice": "4d6", "multiplier": 100, "type": "gp"},
                        {"dice": "3d6", "multiplier": 10, "type": "pp"}
                    ],
                    "items": {
                        "gems": {"chance": 0.6, "dice": "4d6", "value": 50},
                        "art": {"chance": 0.5, "dice": "3d6", "value": 100},
                        "magic_items": {"chance": 0.4, "table": "B", "dice": "1d6"}
                    }
                },
                "high": {
                    "coins": [
                        {"dice": "6d6", "multiplier": 1000, "type": "gp"},
                        {"dice": "5d6", "multiplier": 100, "type": "pp"}
                    ],
                    "items": {
                        "gems": {"chance": 0.7, "dice": "6d6", "value": 100},
                        "art": {"chance": 0.6, "dice": "4d6", "value": 250},
                        "magic_items": {"chance": 0.6, "table": "C", "dice": "1d4"}
                    }
                },
                "very_high": {
                    "coins": [
                        {"dice": "12d6", "multiplier": 1000, "type": "gp"},
                        {"dice": "8d6", "multiplier": 1000, "type": "pp"}
                    ],
                    "items": {
                        "gems": {"chance": 0.8, "dice": "8d6", "value": 500},
                        "art": {"chance": 0.7, "dice": "6d6", "value": 750},
                        "magic_items": {"chance": 0.8, "table": "D", "dice": "1d4"}
                    }
                }
            }
        }

        # Magic item tables (simplified)
        self.magic_item_tables = {
            "A": [
                "Potion of Healing",
                "Spell Scroll (cantrip)",
                "Potion of Climbing",
                "Spell Scroll (1st level)",
                "Spell Scroll (2nd level)",
                "Potion of Greater Healing"
            ],
            "B": [
                "Potion of Greater Healing",
                "Potion of Fire Breath",
                "Potion of Resistance",
                "Ammunition +1",
                "Potion of Animal Friendship",
                "Potion of Hill Giant Strength",
                "Potion of Water Breathing",
                "Spell Scroll (2nd level)",
                "Spell Scroll (3rd level)",
                "Bag of Holding",
                "Keoghtom's Ointment"
            ],
            "C": [
                "Potion of Superior Healing",
                "Spell Scroll (4th level)",
                "Ammunition +2",
                "Potion of Clairvoyance",
                "Potion of Diminution",
                "Potion of Gaseous Form",
                "Potion of Frost Giant Strength",
                "Potion of Stone Giant Strength",
                "Potion of Heroism",
                "Potion of Mind Reading",
                "Spell Scroll (5th level)",
                "Elixir of Health",
                "Oil of Etherealness",
                "Potion of Fire Giant Strength"
            ],
            "D": [
                "Potion of Supreme Healing",
                "Potion of Invisibility",
                "Potion of Speed",
                "Spell Scroll (6th level)",
                "Spell Scroll (7th level)",
                "Ammunition +3",
                "Oil of Sharpness",
                "Potion of Flying",
                "Potion of Cloud Giant Strength",
                "Potion of Longevity",
                "Potion of Vitality",
                "Spell Scroll (8th level)",
                "Horseshoes of Speed",
                "Nolzur's Marvelous Pigments",
                "Bag of Devouring"
            ]
        }

        # Gem and art object tables
        self.gem_tables = {
            10: ["Azurite", "Banded agate", "Blue quartz", "Eye agate", "Hematite", "Lapis lazuli", "Malachite",
                 "Moss agate", "Obsidian", "Rhodochrosite", "Tiger eye", "Turquoise"],
            50: ["Bloodstone", "Carnelian", "Chalcedony", "Chrysoprase", "Citrine", "Jasper", "Moonstone", "Onyx",
                 "Quartz", "Sardonyx", "Star rose quartz", "Zircon"],
            100: ["Amber", "Amethyst", "Chrysoberyl", "Coral", "Garnet", "Jade", "Jet", "Pearl", "Spinel",
                  "Tourmaline"],
            500: ["Alexandrite", "Aquamarine", "Black pearl", "Blue spinel", "Peridot", "Topaz"],
            1000: ["Black opal", "Blue sapphire", "Emerald", "Fire opal", "Opal", "Star ruby", "Star sapphire",
                   "Yellow sapphire"],
            5000: ["Black sapphire", "Diamond", "Jacinth", "Ruby"]
        }

        self.art_tables = {
            25: ["Silver ewer", "Carved bone statuette", "Small gold bracelet", "Cloth-of-gold vestments",
                 "Black velvet mask with silver thread", "Copper chalice with silver filigree",
                 "Pair of engraved bone dice", "Small mirror in painted wooden frame"],
            100: ["Silver plate with moonstones", "Silk robe with gold embroidery", "Gold locket with painted portrait",
                  "Gold ring with bloodstones", "Carved ivory statuette", "Large gold bracelet", "Bronze crown",
                  "Silver comb with moonstones"],
            250: ["Circlet of gold with four aquamarines", "String of pearls", "Gold music box",
                  "Gold and silver brooch", "Obsidian statuette with gold fittings", "Painted gold war mask"],
            750: ["Fine gold chain with fire opal pendant", "Old masterpiece painting",
                  "Embroidered silk and velvet mantle with gold clasps", "Sapphire pendant",
                  "Embroidered glove with jewel chips", "Jeweled anklet"],
            2500: ["Fine gold crown with deep purple amethysts", "Jeweled gold ring",
                   "Small gold statuette with rubies", "Gold cup set with emeralds",
                   "Gold jewelry box with platinum filigree", "Painted gold child's sarcophagus"],
            7500: ["Jeweled gold crown", "Jeweled platinum ring", "Small platinum statuette with rubies",
                   "Platinum cup set with emeralds", "Gold and platinum jewelry box with diamonds",
                   "Painted platinum mask"]
        }

    def generate_treasure(self, encounter_level, is_hoard=False, custom_modifiers=None):
        """
        Generate treasure for an encounter.

        Args:
            encounter_level: Challenge rating of the encounter
            is_hoard: Whether this is a hoard (True) or individual (False) treasure
            custom_modifiers: Optional dictionary of custom modifiers

        Returns:
            Dictionary containing treasure details
        """
        # Determine treasure tier
        if encounter_level <= 4:
            tier = "low"
        elif encounter_level <= 10:
            tier = "medium"
        elif encounter_level <= 16:
            tier = "high"
        else:
            tier = "very_high"

        # Apply custom modifiers
        if custom_modifiers:
            # Wealth modifier increases/decreases overall treasure
            wealth_mod = custom_modifiers.get("wealth", 1.0)
        else:
            wealth_mod = 1.0

        # Generate treasure based on type
        if is_hoard:
            treasure = self._generate_hoard(tier, wealth_mod)
        else:
            treasure = self._generate_individual(tier, wealth_mod)

        return treasure

    def _generate_individual(self, tier, wealth_mod=1.0):
        """
        Generate individual treasure.

        Args:
            tier: Treasure tier
            wealth_mod: Wealth modifier

        Returns:
            Dictionary with coin counts
        """
        result = {
            "coins": {},
            "total_value": 0
        }

        # Roll for each coin type
        for coin_entry in self.treasure_tables["individual"][tier]:
            dice = coin_entry["dice"]
            multiplier = coin_entry["multiplier"]
            coin_type = coin_entry["type"]

            # Roll dice and apply multiplier and wealth mod
            value = self._roll_dice(dice) * multiplier * wealth_mod
            value = int(value)

            if value > 0:
                result["coins"][coin_type] = value

                # Add to total value in gold pieces
                if coin_type == "cp":
                    result["total_value"] += value / 100
                elif coin_type == "sp":
                    result["total_value"] += value / 10
                elif coin_type == "gp":
                    result["total_value"] += value
                elif coin_type == "pp":
                    result["total_value"] += value * 10

        return result

    def _generate_hoard(self, tier, wealth_mod=1.0):
        """
        Generate treasure hoard.

        Args:
            tier: Treasure tier
            wealth_mod: Wealth modifier

        Returns:
            Dictionary with hoard contents
        """
        result = {
            "coins": {},
            "gems": [],
            "art_objects": [],
            "magic_items": [],
            "total_value": 0
        }

        # Get hoard table
        hoard_table = self.treasure_tables["hoard"][tier]

        # Roll for coins
        for coin_entry in hoard_table["coins"]:
            dice = coin_entry["dice"]
            multiplier = coin_entry["multiplier"]
            coin_type = coin_entry["type"]

            # Roll dice and apply multiplier and wealth mod
            value = self._roll_dice(dice) * multiplier * wealth_mod
            value = int(value)

            if value > 0:
                result["coins"][coin_type] = value

                # Add to total value in gold pieces
                if coin_type == "cp":
                    result["total_value"] += value / 100
                elif coin_type == "sp":
                    result["total_value"] += value / 10
                elif coin_type == "gp":
                    result["total_value"] += value
                elif coin_type == "pp":
                    result["total_value"] += value * 10

        # Roll for gems
        if "gems" in hoard_table["items"]:
            gem_info = hoard_table["items"]["gems"]
            chance = gem_info["chance"]

            if random.random() < chance:
                count = self._roll_dice(gem_info["dice"])
                value = gem_info["value"]

                for _ in range(count):
                    gem_type = self._random_gem(value)
                    result["gems"].append({"type": gem_type, "value": value})
                    result["total_value"] += value

        # Roll for art objects
        if "art" in hoard_table["items"]:
            art_info = hoard_table["items"]["art"]
            chance = art_info["chance"]

            if random.random() < chance:
                count = self._roll_dice(art_info["dice"])
                value = art_info["value"]

                for _ in range(count):
                    art_type = self._random_art(value)
                    result["art_objects"].append({"type": art_type, "value": value})
                    result["total_value"] += value

        # Roll for magic items
        if "magic_items" in hoard_table["items"]:
            item_info = hoard_table["items"]["magic_items"]
            chance = item_info["chance"]

            if random.random() < chance:
                count = self._roll_dice(item_info["dice"])
                table = item_info["table"]

                for _ in range(count):
                    item = self._random_magic_item(table)
                    result["magic_items"].append(item)
                    # Magic items don't contribute to total_value as they're not typically sold

        return result

    def _random_gem(self, value):
        """
        Select a random gem of the given value.

        Args:
            value: Value of the gem

        Returns:
            String with gem type
        """
        if value in self.gem_tables:
            return random.choice(self.gem_tables[value])
        else:
            # Find closest value
            keys = sorted(self.gem_tables.keys())
            closest = min(keys, key=lambda x: abs(x - value))
            return random.choice(self.gem_tables[closest])

    def _random_art(self, value):
        """
        Select a random art object of the given value.

        Args:
            value: Value of the art object

        Returns:
            String with art object description
        """
        if value in self.art_tables:
            return random.choice(self.art_tables[value])
        else:
            # Find closest value
            keys = sorted(self.art_tables.keys())
            closest = min(keys, key=lambda x: abs(x - value))
            return random.choice(self.art_tables[closest])

    def _random_magic_item(self, table):
        """
        Select a random magic item from the given table.

        Args:
            table: Magic item table identifier

        Returns:
            String with magic item name
        """
        if table in self.magic_item_tables:
            return random.choice(self.magic_item_tables[table])
        else:
            # Default to table A
            return random.choice(self.magic_item_tables["A"])

    def _roll_dice(self, dice_str):
        """
        Roll dice based on string format like '3d6' or '1d10'.

        Args:
            dice_str: Dice notation string

        Returns:
            Roll result
        """
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

    def get_treasure_description(self, treasure):
        """
        Generate a text description of the treasure.

        Args:
            treasure: Treasure data dictionary

        Returns:
            Text description
        """
        description = []

        # Describe coins
        if treasure.get("coins"):
            coin_parts = []
            for coin_type, amount in treasure["coins"].items():
                if amount > 0:
                    # Format large numbers with commas
                    formatted_amount = "{:,}".format(amount)

                    # Full coin type names
                    coin_names = {
                        "cp": "copper pieces",
                        "sp": "silver pieces",
                        "gp": "gold pieces",
                        "pp": "platinum pieces"
                    }

                    coin_parts.append(f"{formatted_amount} {coin_names.get(coin_type, coin_type)}")

            if coin_parts:
                description.append("Coins: " + ", ".join(coin_parts))

        # Describe gems
        if treasure.get("gems") and len(treasure["gems"]) > 0:
            if len(treasure["gems"]) <= 5:
                # List individual gems
                gem_parts = []
                for gem in treasure["gems"]:
                    gem_parts.append(f"{gem['type']} ({gem['value']} gp)")

                description.append("Gems: " + ", ".join(gem_parts))
            else:
                # Summarize gems
                gem_counts = {}
                for gem in treasure["gems"]:
                    value = gem["value"]
                    if value not in gem_counts:
                        gem_counts[value] = 0
                    gem_counts[value] += 1

                gem_summary = []
                for value, count in sorted(gem_counts.items()):
                    gem_summary.append(f"{count} gems worth {value} gp each")

                description.append("Gems: " + ", ".join(gem_summary))

        # Describe art objects
        if treasure.get("art_objects") and len(treasure["art_objects"]) > 0:
            if len(treasure["art_objects"]) <= 5:
                # List individual art objects
                art_parts = []
                for art in treasure["art_objects"]:
                    art_parts.append(f"{art['type']} ({art['value']} gp)")

                description.append("Art Objects: " + ", ".join(art_parts))
            else:
                # Summarize art objects
                art_counts = {}
                for art in treasure["art_objects"]:
                    value = art["value"]
                    if value not in art_counts:
                        art_counts[value] = 0
                    art_counts[value] += 1

                art_summary = []
                for value, count in sorted(art_counts.items()):
                    art_summary.append(f"{count} art objects worth {value} gp each")

                description.append("Art Objects: " + ", ".join(art_summary))

        # Describe magic items
        if treasure.get("magic_items") and len(treasure["magic_items"]) > 0:
            if len(treasure["magic_items"]) <= 5:
                description.append("Magic Items: " + ", ".join(treasure["magic_items"]))
            else:
                description.append(f"Magic Items: {len(treasure['magic_items'])} various magical items")

        # Add total value
        if "total_value" in treasure:
            formatted_value = "{:,.2f}".format(treasure["total_value"])
            description.append(f"Total Value: {formatted_value} gp")

        return "\n".join(description)