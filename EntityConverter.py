# DataManager/EntityConverter.py
import re
import random
from typing import Dict, Any, Optional


class EntityConverter:
    """Converts between different entity data formats."""

    def __init__(self):
        """Initialize the entity converter."""
        pass

    def convert_to_combat_entity(self, character):
        """
        Convert a character to a combat entity.

        Args:
            character: Character data

        Returns:
            Combat entity data
        """
        # Basic structure for a combat entity
        combat_entity = {
            "name": character.get("name", "Unknown"),
            "id": f"enemy_{random.randint(0, 1000)}" if not character.get("is_player",
                                                                          True) else f"player_{random.randint(0, 1000)}",
            "is_player": character.get("is_player", False),
            "stats": character.copy(),
            "current_hp": character.get("hit_points", 20),
            "max_hp": character.get("hit_points", 20),
            "initiative": 0,
            "conditions": [],
            "resources": {}
        }

        return combat_entity

    def convert_monster_to_combat_entity(self, monster):
        """
        Convert a monster to a combat entity.

        Args:
            monster: Monster data

        Returns:
            Combat entity data
        """
        # Parse HP from string like "45 (7d8+14)"
        hp = 20
        if "hp" in monster:
            hp_text = monster["hp"]
            if isinstance(hp_text, str):
                match = re.search(r'(\d+)', hp_text)
                if match:
                    hp = int(match.group(1))

        # Get creature name
        name = monster.get("name", "Unknown Monster")

        # Create combat entity
        combat_entity = {
            "name": name,
            "id": f"enemy_{random.randint(0, 1000)}",
            "is_player": False,
            "stats": monster.copy(),
            "current_hp": hp,
            "max_hp": hp,
            "initiative": 0,
            "conditions": [],
            "resources": {}
        }

        return combat_entity