# context_manager.py
import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Union, Any, Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("context_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("context_manager")


class ContextManager:
    """Manages context objects for language generation."""

    def __init__(self, max_context_size=5000, max_history_items=100):
        """
        Initialize the context manager.

        Args:
            max_context_size: Maximum size of context in tokens
            max_history_items: Maximum number of history items to store
        """
        self.max_context_size = max_context_size
        self.max_history_items = max_history_items

        # Entity storage
        self.npcs = {}  # NPC data keyed by ID
        self.locations = {}  # Location data keyed by ID
        self.player_party = {}  # Player character data
        self.quests = {}  # Quest data keyed by ID

        # History storage
        self.dialogue_history = {}  # Dialogue history keyed by NPC ID
        self.combat_history = []  # Recent combat actions
        self.scene_history = []  # Scene transitions
        self.interaction_history = []  # General interactions

        # World state
        self.time_of_day = "day"
        self.weather = "clear"
        self.current_location_id = None
        self.active_quest_ids = set()

        # In-memory counter for token estimation
        self.estimated_token_count = 0

        logger.info("ContextManager initialized")

    def register_npc(self, npc_id: str, npc_data: Dict[str, Any]) -> None:
        """
        Register or update an NPC in the context.

        Args:
            npc_id: Unique identifier for the NPC
            npc_data: Dictionary of NPC data
        """
        # Merge with existing data if present
        if npc_id in self.npcs:
            self.npcs[npc_id].update(npc_data)
        else:
            self.npcs[npc_id] = npc_data

        logger.info(f"Registered NPC: {npc_id}")

    def register_location(self, location_id: str, location_data: Dict[str, Any]) -> None:
        """
        Register or update a location in the context.

        Args:
            location_id: Unique identifier for the location
            location_data: Dictionary of location data
        """
        # Merge with existing data if present
        if location_id in self.locations:
            self.locations[location_id].update(location_data)
        else:
            self.locations[location_id] = location_data

        logger.info(f"Registered location: {location_id}")

    def update_player_party(self, party_data: Dict[str, Any]) -> None:
        """
        Update player party information.

        Args:
            party_data: Dictionary of party data
        """
        self.player_party.update(party_data)
        logger.info("Updated player party data")

    def register_quest(self, quest_id: str, quest_data: Dict[str, Any]) -> None:
        """
        Register or update a quest in the context.

        Args:
            quest_id: Unique identifier for the quest
            quest_data: Dictionary of quest data
        """
        # Merge with existing data if present
        if quest_id in self.quests:
            self.quests[quest_id].update(quest_data)
        else:
            self.quests[quest_id] = quest_data

        # Add to active quests if not completed
        if quest_data.get("status") == "active":
            self.active_quest_ids.add(quest_id)
        elif quest_id in self.active_quest_ids:
            self.active_quest_ids.remove(quest_id)

        logger.info(f"Registered quest: {quest_id} (Status: {quest_data.get('status', 'unknown')})")

    def add_dialogue_history(self, npc_id: str, player_text: str, npc_text: str,
                             topic: Optional[str] = None) -> None:
        """
        Add dialogue history for an NPC.

        Args:
            npc_id: NPC identifier
            player_text: What the player said
            npc_text: What the NPC said in response
            topic: Optional topic of conversation
        """
        if npc_id not in self.dialogue_history:
            self.dialogue_history[npc_id] = []

        # Add entry with timestamp
        entry = {
            "timestamp": time.time(),
            "player": player_text,
            "npc": npc_text,
            "topic": topic
        }

        self.dialogue_history[npc_id].append(entry)

        # Limit size
        if len(self.dialogue_history[npc_id]) > self.max_history_items:
            self.dialogue_history[npc_id] = self.dialogue_history[npc_id][-self.max_history_items:]

        logger.debug(f"Added dialogue history for NPC {npc_id}")

    def add_combat_action(self, action_data: Dict[str, Any]) -> None:
        """
        Add a combat action to history.

        Args:
            action_data: Dictionary of combat action data
        """
        # Add entry with timestamp
        entry = {
            "timestamp": time.time(),
            **action_data
        }

        self.combat_history.append(entry)

        # Limit size
        if len(self.combat_history) > self.max_history_items:
            self.combat_history = self.combat_history[-self.max_history_items:]

        logger.debug("Added combat action to history")

    def add_scene_transition(self, from_scene: str, to_scene: str,
                             description: str, mood: str = "neutral") -> None:
        """
        Add a scene transition to history.

        Args:
            from_scene: Starting scene
            to_scene: Destination scene
            description: Transition description
            mood: Emotional mood of the transition
        """
        # Add entry with timestamp
        entry = {
            "timestamp": time.time(),
            "from_scene": from_scene,
            "to_scene": to_scene,
            "description": description,
            "mood": mood
        }

        self.scene_history.append(entry)

        # Update current location
        self.current_location_id = to_scene

        # Limit size
        if len(self.scene_history) > self.max_history_items:
            self.scene_history = self.scene_history[-self.max_history_items:]

        logger.debug(f"Added scene transition: {from_scene} -> {to_scene}")

    def update_world_state(self, time_of_day: Optional[str] = None,
                           weather: Optional[str] = None) -> None:
        """
        Update world state information.

        Args:
            time_of_day: Current time of day
            weather: Current weather
        """
        if time_of_day:
            self.time_of_day = time_of_day

        if weather:
            self.weather = weather

        logger.info(f"Updated world state: {self.time_of_day}, {self.weather}")

    def add_interaction(self, interaction_type: str, description: str,
                        entities_involved: List[str] = None) -> None:
        """
        Add a general interaction to history.

        Args:
            interaction_type: Type of interaction
            description: Description of what happened
            entities_involved: List of entity IDs involved
        """
        # Add entry with timestamp
        entry = {
            "timestamp": time.time(),
            "type": interaction_type,
            "description": description,
            "entities": entities_involved or []
        }

        self.interaction_history.append(entry)

        # Limit size
        if len(self.interaction_history) > self.max_history_items:
            self.interaction_history = self.interaction_history[-self.max_history_items:]

        logger.debug(f"Added interaction: {interaction_type}")

    def get_npc_context(self, npc_id: str, include_history: bool = True,
                        max_history_items: int = 5) -> Dict[str, Any]:
        """
        Get context for NPC interaction.

        Args:
            npc_id: NPC identifier
            include_history: Whether to include dialogue history
            max_history_items: Maximum dialogue history items to include

        Returns:
            Dictionary of NPC context
        """
        context = {}

        # Basic NPC data
        if npc_id in self.npcs:
            context["npc"] = self.npcs[npc_id]
        else:
            logger.warning(f"NPC {npc_id} not found in context")
            return {"error": f"NPC {npc_id} not found"}

        # Dialogue history
        if include_history and npc_id in self.dialogue_history:
            history = self.dialogue_history[npc_id]
            context["dialogue_history"] = history[-max_history_items:]

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "current_location": self.current_location_id
        }

        # Location info if available
        if self.current_location_id and self.current_location_id in self.locations:
            context["location"] = self.locations[self.current_location_id]

        # Active quests involving this NPC
        context["related_quests"] = []
        for quest_id, quest in self.quests.items():
            if npc_id in quest.get("related_npcs", []) and quest_id in self.active_quest_ids:
                context["related_quests"].append(quest)

        # Recent interactions involving this NPC
        context["recent_interactions"] = []
        for interaction in reversed(self.interaction_history):
            if npc_id in interaction.get("entities", []):
                context["recent_interactions"].append(interaction)
                if len(context["recent_interactions"]) >= 3:
                    break

        return context

    def get_location_context(self, location_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get context for a location.

        Args:
            location_id: Location identifier (uses current location if None)

        Returns:
            Dictionary of location context
        """
        location_id = location_id or self.current_location_id
        if not location_id:
            logger.warning("No location specified and no current location set")
            return {"error": "No location specified"}

        context = {}

        # Basic location data
        if location_id in self.locations:
            context["location"] = self.locations[location_id]
        else:
            logger.warning(f"Location {location_id} not found in context")
            return {"error": f"Location {location_id} not found"}

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather
        }

        # NPCs in this location
        context["present_npcs"] = []
        for npc_id, npc in self.npcs.items():
            if npc.get("current_location") == location_id:
                context["present_npcs"].append(npc)

        # Previous scene transitions involving this location
        context["scene_history"] = []
        for transition in reversed(self.scene_history):
            if transition["from_scene"] == location_id or transition["to_scene"] == location_id:
                context["scene_history"].append(transition)
                if len(context["scene_history"]) >= 3:
                    break

        # Active quests related to this location
        context["related_quests"] = []
        for quest_id, quest in self.quests.items():
            if location_id in quest.get("locations", []) and quest_id in self.active_quest_ids:
                context["related_quests"].append(quest)

        return context

    def get_combat_context(self, include_party: bool = True,
                           max_history_items: int = 5) -> Dict[str, Any]:
        """
        Get context for combat.

        Args:
            include_party: Whether to include player party data
            max_history_items: Maximum combat history items to include

        Returns:
            Dictionary of combat context
        """
        context = {}

        # Combat history
        context["combat_history"] = self.combat_history[-max_history_items:]

        # Player party if requested
        if include_party:
            context["player_party"] = self.player_party

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "current_location": self.current_location_id
        }

        # Location info if available
        if self.current_location_id and self.current_location_id in self.locations:
            context["location"] = self.locations[self.current_location_id]

        return context

    def get_quest_context(self, quest_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get context for a quest.

        Args:
            quest_id: Quest identifier (returns all active quests if None)

        Returns:
            Dictionary of quest context
        """
        context = {}

        if quest_id:
            # Specific quest
            if quest_id in self.quests:
                context["quest"] = self.quests[quest_id]

                # Related NPCs
                context["related_npcs"] = []
                for npc_id in self.quests[quest_id].get("related_npcs", []):
                    if npc_id in self.npcs:
                        context["related_npcs"].append(self.npcs[npc_id])

                # Related locations
                context["related_locations"] = []
                for loc_id in self.quests[quest_id].get("locations", []):
                    if loc_id in self.locations:
                        context["related_locations"].append(self.locations[loc_id])
            else:
                logger.warning(f"Quest {quest_id} not found in context")
                return {"error": f"Quest {quest_id} not found"}
        else:
            # All active quests
            context["active_quests"] = []
            for quest_id in self.active_quest_ids:
                if quest_id in self.quests:
                    context["active_quests"].append(self.quests[quest_id])

        # Player party
        context["player_party"] = self.player_party

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "current_location": self.current_location_id
        }

        return context

    def get_world_context(self) -> Dict[str, Any]:
        """
        Get comprehensive world context.

        Returns:
            Dictionary of world context
        """
        context = {}

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "current_location": self.current_location_id
        }

        # Player party
        context["player_party"] = self.player_party

        # Current location detail
        if self.current_location_id and self.current_location_id in self.locations:
            context["current_location"] = self.locations[self.current_location_id]

        # Active quests
        context["active_quests"] = []
        for quest_id in self.active_quest_ids:
            if quest_id in self.quests:
                context["active_quests"].append(self.quests[quest_id])

        # Active NPCs (NPCs in current location)
        context["present_npcs"] = []
        for npc_id, npc in self.npcs.items():
            if npc.get("current_location") == self.current_location_id:
                context["present_npcs"].append(npc)

        # Recent scene transitions
        context["recent_transitions"] = self.scene_history[-3:] if self.scene_history else []

        # Recent interactions
        context["recent_interactions"] = self.interaction_history[-5:] if self.interaction_history else []

        # Recent combat
        context["recent_combat"] = self.combat_history[-3:] if self.combat_history else []

        return context

    def get_transition_context(self, from_scene: str, to_scene: str) -> Dict[str, Any]:
        """
        Get context for a scene transition.

        Args:
            from_scene: Starting scene ID
            to_scene: Destination scene ID

        Returns:
            Dictionary of transition context
        """
        context = {}

        # Source and destination info
        if from_scene in self.locations:
            context["from_location"] = self.locations[from_scene]

        if to_scene in self.locations:
            context["to_location"] = self.locations[to_scene]

        # World state
        context["world_state"] = {
            "time_of_day": self.time_of_day,
            "weather": self.weather
        }

        # Player party
        context["player_party"] = self.player_party

        # Previous transitions to these locations
        context["previous_transitions"] = []
        for transition in reversed(self.scene_history):
            if (from_scene in [transition["from_scene"], transition["to_scene"]] or
                    to_scene in [transition["from_scene"], transition["to_scene"]]):
                context["previous_transitions"].append(transition)
                if len(context["previous_transitions"]) >= 3:
                    break

        # Active quests related to destination
        context["related_quests"] = []
        for quest_id, quest in self.quests.items():
            if to_scene in quest.get("locations", []) and quest_id in self.active_quest_ids:
                context["related_quests"].append(quest)

        # Recent interactions
        context["recent_interactions"] = self.interaction_history[-3:] if self.interaction_history else []

        return context

    def prune_old_data(self, older_than_days: int = 7) -> None:
        """
        Remove data older than specified days.

        Args:
            older_than_days: Age threshold in days
        """
        threshold = time.time() - (older_than_days * 24 * 60 * 60)

        # Prune dialogue history
        for npc_id in self.dialogue_history:
            self.dialogue_history[npc_id] = [
                entry for entry in self.dialogue_history[npc_id]
                if entry.get("timestamp", 0) > threshold
            ]

        # Prune combat history
        self.combat_history = [
            entry for entry in self.combat_history
            if entry.get("timestamp", 0) > threshold
        ]

        # Prune scene history
        self.scene_history = [
            entry for entry in self.scene_history
            if entry.get("timestamp", 0) > threshold
        ]

        # Prune interaction history
        self.interaction_history = [
            entry for entry in self.interaction_history
            if entry.get("timestamp", 0) > threshold
        ]

        logger.info(f"Pruned data older than {older_than_days} days")

    def save_to_file(self, filepath: str) -> bool:
        """
        Save context data to file.

        Args:
            filepath: Path to save the data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                "npcs": self.npcs,
                "locations": self.locations,
                "player_party": self.player_party,
                "quests": self.quests,
                "dialogue_history": self.dialogue_history,
                "combat_history": self.combat_history,
                "scene_history": self.scene_history,
                "interaction_history": self.interaction_history,
                "time_of_day": self.time_of_day,
                "weather": self.weather,
                "current_location_id": self.current_location_id,
                "active_quest_ids": list(self.active_quest_ids),
                "saved_timestamp": time.time()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Context data saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving context data: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """
        Load context data from file.

        Args:
            filepath: Path to load the data from

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.npcs = data.get("npcs", {})
            self.locations = data.get("locations", {})
            self.player_party = data.get("player_party", {})
            self.quests = data.get("quests", {})
            self.dialogue_history = data.get("dialogue_history", {})
            self.combat_history = data.get("combat_history", [])
            self.scene_history = data.get("scene_history", [])
            self.interaction_history = data.get("interaction_history", [])
            self.time_of_day = data.get("time_of_day", "day")
            self.weather = data.get("weather", "clear")
            self.current_location_id = data.get("current_location_id")
            self.active_quest_ids = set(data.get("active_quest_ids", []))

            logger.info(f"Context data loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading context data: {e}")
            return False

    def clear(self) -> None:
        """Clear all context data."""
        self.npcs = {}
        self.locations = {}
        self.player_party = {}
        self.quests = {}
        self.dialogue_history = {}
        self.combat_history = []
        self.scene_history = []
        self.interaction_history = []
        self.time_of_day = "day"
        self.weather = "clear"
        self.current_location_id = None
        self.active_quest_ids = set()

        logger.info("Context data cleared")

    def estimate_token_count(self, context: Dict[str, Any]) -> int:
        """
        Estimate number of tokens in a context object.

        Args:
            context: Context dictionary

        Returns:
            int: Estimated token count
        """
        # Simple estimation: 1 token ~ 4 characters on average
        json_str = json.dumps(context)
        return len(json_str) // 4

    def prioritize_context(self, context: Dict[str, Any], max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Prioritize context to fit within token limit.

        Args:
            context: Full context dictionary
            max_tokens: Maximum tokens to include

        Returns:
            Dict[str, Any]: Prioritized context
        """
        # Estimate total tokens
        estimated_tokens = self.estimate_token_count(context)

        if estimated_tokens <= max_tokens:
            return context  # Already within limit

        # Need to prioritize and reduce
        prioritized = {}

        # Priority order for different context elements
        priority_keys = [
            "npc",  # Current NPC is highest priority
            "location",  # Current location
            "world_state",  # World state
            "dialogue_history",  # Recent dialogues
            "quest",  # Specific quest details
            "active_quests",  # Active quests
            "player_party",  # Player characters
            "present_npcs",  # NPCs in location
            "related_npcs",  # NPCs related to quests
            "recent_interactions",  # Recent interactions
            "combat_history",  # Combat history
            "recent_transitions",  # Scene transitions
            "scene_history",  # Scene history
            "previous_transitions",  # Previous transitions
            "related_quests",  # Related quests
            "related_locations"  # Related locations
        ]

        # Add keys in priority order until we hit the limit
        remaining_tokens = max_tokens
        for key in priority_keys:
            if key in context:
                value = context[key]

                # For list elements, prioritize most recent
                if isinstance(value, list) and len(value) > 0:
                    # Limit history items
                    if key == "dialogue_history" and len(value) > 3:
                        value = value[-3:]  # Keep only 3 most recent
                    elif len(value) > 5:
                        value = value[-5:]  # Keep only 5 most recent

                # Estimate tokens for this element
                element_tokens = self.estimate_token_count({key: value})

                # Include if it fits
                if element_tokens <= remaining_tokens:
                    prioritized[key] = value
                    remaining_tokens -= element_tokens
                elif key in ["dialogue_history", "combat_history", "scene_history",
                             "recent_interactions"] and len(value) > 1:
                    # Try to include at least one item from important history
                    smallest_value = [value[-1]]  # Most recent item
                    element_tokens = self.estimate_token_count({key: smallest_value})
                    if element_tokens <= remaining_tokens:
                        prioritized[key] = smallest_value
                        remaining_tokens -= element_tokens

        return prioritized