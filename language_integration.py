# language_integration.py
import os
import json
import logging
from typing import Dict, List, Optional, Union, Any

# Use relative import for language_client
from .language_client import LanguageServiceClient
from .context_manager import ContextManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("language_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("language_integration")


class LanguageIntegration:
    """
    Integrates language service with context management for the D&D AI system.
    Acts as the main interface for the DungeonMasterAI to use language generation.
    """

    def __init__(self, service_url="http://localhost:8000", context_file=None):
        """
        Initialize the language integration.

        Args:
            service_url: URL of the language service
            context_file: Path to load/save context
        """
        # Initialize language client
        self.client = LanguageServiceClient(service_url)

        # Initialize context manager
        self.context = ContextManager()

        # Load context if file provided
        if context_file and os.path.exists(context_file):
            self.context.load_from_file(context_file)
            self.context_file = context_file
        else:
            self.context_file = context_file

        # Service status
        self.service_available = self.client.is_connected()

        logger.info(f"Language integration initialized. Service available: {self.service_available}")

    def generate_dialogue(self, npc_id: str, player_text: str,
                          topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate dialogue for an NPC in response to player text.

        Args:
            npc_id: NPC identifier
            player_text: What the player said
            topic: Optional topic of conversation

        Returns:
            Dictionary with generated dialogue and metadata
        """
        # Verify NPC exists in context
        if npc_id not in self.context.npcs:
            logger.warning(f"NPC {npc_id} not found in context")
            return {
                "text": f"Error: NPC {npc_id} not found in context",
                "status": "error"
            }

        # Get NPC data
        npc_data = self.context.npcs[npc_id]
        npc_name = npc_data.get("name", f"NPC-{npc_id}")
        npc_type = npc_data.get("type", "commoner")
        npc_race = npc_data.get("race", "human")
        npc_attitude = npc_data.get("attitude", "neutral")

        # Get dialogue history
        history = []
        if npc_id in self.context.dialogue_history:
            history = self.context.dialogue_history[npc_id][-5:]  # Last 5 exchanges

        # Prepare context
        npc_context = self.context.get_npc_context(npc_id)

        # Determine situation
        situation = f"at {self.context.current_location_id}" if self.context.current_location_id else "in the area"

        # Generate dialogue
        response = self.client.generate_dialogue(
            npc_id=npc_id,
            npc_name=npc_name,
            npc_type=npc_type,
            npc_race=npc_race,
            npc_attitude=npc_attitude,
            situation=situation,
            topic=topic,
            history=history,
            personality_traits=npc_data.get("personality_traits", []),
            knowledge=npc_context
        )

        # Extract generated text
        generated_text = response.get("text", f"{npc_name}: \"I'm not sure what to say.\"")

        # Update dialogue history
        self.context.add_dialogue_history(npc_id, player_text, generated_text, topic)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

        return response

    def generate_description(self, location_id: Optional[str] = None,
                             time_of_day: Optional[str] = None,
                             weather: Optional[str] = None,
                             specific_features: Optional[List[str]] = None,
                             atmosphere: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a description for a location.

        Args:
            location_id: Location identifier (uses current location if None)
            time_of_day: Time of day (uses current world state if None)
            weather: Weather condition (uses current world state if None)
            specific_features: Optional specific features to include
            atmosphere: Optional mood/atmosphere for the description

        Returns:
            Dictionary with generated description and metadata
        """
        # Use current location if none specified
        location_id = location_id or self.context.current_location_id
        if not location_id:
            logger.warning("No location specified and no current location set")
            return {
                "text": "Error: No location specified",
                "status": "error"
            }

        # Verify location exists in context
        if location_id not in self.context.locations:
            logger.warning(f"Location {location_id} not found in context")

            # Try to create a basic location entry
            location_type = location_id.split('_')[0] if '_' in location_id else location_id
            self.context.register_location(location_id, {
                "name": location_id.replace('_', ' ').title(),
                "type": location_type
            })

        # Get location data
        location_data = self.context.locations[location_id]
        location_type = location_data.get("type", "area")

        # Use world state if time/weather not specified
        time_of_day = time_of_day or self.context.time_of_day
        weather = weather or self.context.weather

        # Check if visited before
        visited_before = location_id in [scene.get("to_scene") for scene in self.context.scene_history]

        # Get significant events at this location
        significant_events = []
        for interaction in self.context.interaction_history:
            if interaction.get("location") == location_id:
                significant_events.append(interaction.get("description", ""))
                if len(significant_events) >= 3:
                    break

        # Generate description
        response = self.client.generate_description(
            location_type=location_type,
            time_of_day=time_of_day,
            weather=weather,
            specific_features=specific_features or location_data.get("features", []),
            atmosphere=atmosphere or location_data.get("atmosphere", "neutral"),
            visited_before=visited_before,
            significant_events=significant_events
        )

        # Extract generated text
        generated_text = response.get("text", f"You find yourself in a {location_type}.")

        # Update world state if changed
        if time_of_day != self.context.time_of_day or weather != self.context.weather:
            self.context.update_world_state(time_of_day, weather)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

        return response

    def generate_combat(self, action_type: str, outcome: str, attacker: str,
                        defender: Optional[str] = None, weapon: Optional[str] = None,
                        spell: Optional[str] = None, damage_amount: Optional[int] = None,
                        critical: bool = False) -> Dict[str, Any]:
        """
        Generate a combat description.

        Args:
            action_type: Type of combat action
            outcome: Outcome of the action
            attacker: Name of the attacker
            defender: Name of the defender
            weapon: Optional weapon being used
            spell: Optional spell being cast
            damage_amount: Optional amount of damage
            critical: Whether this is a critical hit/fail

        Returns:
            Dictionary with generated combat description and metadata
        """
        # Get previous combat actions
        previous_actions = self.context.combat_history[-3:] if self.context.combat_history else []

        # Generate combat description
        response = self.client.generate_combat(
            action_type=action_type,
            outcome=outcome,
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            spell=spell,
            damage_amount=damage_amount,
            critical=critical,
            previous_actions=previous_actions
        )

        # Extract generated text
        generated_text = response.get("text", f"{attacker} attacks {defender or 'the enemy'}.")

        # Add to combat history
        self.context.add_combat_action({
            "action_type": action_type,
            "outcome": outcome,
            "attacker": attacker,
            "defender": defender,
            "description": generated_text
        })

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

        return response

    def generate_quest(self, quest_type: Optional[str] = None, difficulty: str = "medium",
                       level: int = 1, location: Optional[str] = None,
                       giver: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a quest.

        Args:
            quest_type: Type of quest
            difficulty: Difficulty level
            level: Character level
            location: Optional location for the quest
            giver: Optional NPC who gives the quest

        Returns:
            Dictionary with generated quest and metadata
        """
        # Get party info
        party_info = self.context.player_party

        # Get relevant world state
        world_state = {
            "time_of_day": self.context.time_of_day,
            "weather": self.context.weather,
            "current_location": self.context.current_location_id,
            "active_quests": len(self.context.active_quest_ids)
        }

        # Generate quest
        response = self.client.generate_quest(
            quest_type=quest_type,
            difficulty=difficulty,
            level=level,
            location=location or self.context.current_location_id,
            giver=giver,
            party_info=party_info,
            world_state=world_state
        )

        # Extract generated text and parse as JSON
        try:
            quest_data = json.loads(response.get("text", "{}"))

            # Generate quest ID
            quest_id = f"quest_{len(self.context.quests) + 1}"

            # Register the quest in context
            quest_data["id"] = quest_id
            quest_data["status"] = "active"
            self.context.register_quest(quest_id, quest_data)

            # Format response
            response["quest_id"] = quest_id

            # Save context if file provided
            if self.context_file:
                self.context.save_to_file(self.context_file)

            return response
        except json.JSONDecodeError:
            logger.error("Failed to parse quest JSON")
            return {
                "text": "Error: Failed to generate valid quest data",
                "status": "error"
            }

    def generate_transition(self, from_scene: str, to_scene: str,
                            mood: str = "neutral", time_passed: str = "immediate") -> Dict[str, Any]:
        """
        Generate a narrative transition between scenes.

        Args:
            from_scene: Starting scene
            to_scene: Destination scene
            mood: Emotional mood of the transition
            time_passed: Amount of time passed

        Returns:
            Dictionary with generated transition and metadata
        """
        # Get party state
        party_state = self.context.player_party

        # Get significant events
        significant_events = []
        for event in self.context.interaction_history[-5:]:
            if event.get("type") == "significant":
                significant_events.append(event.get("description", ""))

        # Generate transition
        response = self.client.generate_transition(
            from_scene=from_scene,
            to_scene=to_scene,
            mood=mood,
            time_passed=time_passed,
            party_state=party_state,
            significant_events=significant_events
        )

        # Extract generated text
        generated_text = response.get("text", f"The party travels from {from_scene} to {to_scene}.")

        # Add to scene history
        self.context.add_scene_transition(from_scene, to_scene, generated_text, mood)

        # Update current location
        self.context.current_location_id = to_scene

        # Register location if it doesn't exist
        if to_scene not in self.context.locations:
            location_type = to_scene.split('_')[0] if '_' in to_scene else to_scene
            self.context.register_location(to_scene, {
                "name": to_scene.replace('_', ' ').title(),
                "type": location_type
            })

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

        return response

    def register_location(self, location_id: str, location_data: Dict[str, Any]) -> None:
        """
        Register a location in the context.

        Args:
            location_id: Location identifier
            location_data: Location data
        """
        self.context.register_location(location_id, location_data)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

    def register_npc(self, npc_id: str, npc_data: Dict[str, Any]) -> None:
        """
        Register an NPC in the context.

        Args:
            npc_id: NPC identifier
            npc_data: NPC data
        """
        self.context.register_npc(npc_id, npc_data)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

    def update_party(self, party_data: Dict[str, Any]) -> None:
        """
        Update player party information.

        Args:
            party_data: Party data
        """
        self.context.update_player_party(party_data)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

    def update_world_state(self, time_of_day: Optional[str] = None,
                           weather: Optional[str] = None) -> None:
        """
        Update world state.

        Args:
            time_of_day: Time of day
            weather: Weather condition
        """
        self.context.update_world_state(time_of_day, weather)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

    def add_interaction(self, interaction_type: str, description: str,
                        entities_involved: List[str] = None,
                        location: Optional[str] = None) -> None:
        """
        Add an interaction to the history.

        Args:
            interaction_type: Type of interaction
            description: Description of what happened
            entities_involved: List of entity IDs involved
            location: Optional location of the interaction
        """
        self.context.add_interaction(interaction_type, description, entities_involved)

        # Save context if file provided
        if self.context_file:
            self.context.save_to_file(self.context_file)

    def save_context(self, filepath: Optional[str] = None) -> bool:
        """
        Save context to file.

        Args:
            filepath: Optional filepath to save to

        Returns:
            bool: True if successful, False otherwise
        """
        filepath = filepath or self.context_file
        if not filepath:
            logger.warning("No context file specified")
            return False

        return self.context.save_to_file(filepath)

    def load_context(self, filepath: Optional[str] = None) -> bool:
        """
        Load context from file.

        Args:
            filepath: Optional filepath to load from

        Returns:
            bool: True if successful, False otherwise
        """
        filepath = filepath or self.context_file
        if not filepath or not os.path.exists(filepath):
            logger.warning(f"Context file not found: {filepath}")
            return False

        result = self.context.load_from_file(filepath)
        if result:
            self.context_file = filepath

        return result

    def check_service(self) -> bool:
        """
        Check if language service is available.

        Returns:
            bool: True if service is available, False otherwise
        """
        self.service_available = self.client.is_connected()
        return self.service_available