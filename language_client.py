# language_client.py
import requests
import json
import logging
from typing import Dict, List, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("language_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("language_client")


class LanguageServiceClient:
    """Client for interacting with the language service."""

    def __init__(self, base_url="http://localhost:8000"):
        """Initialize the client with the service URL."""
        self.base_url = base_url
        self.session = requests.Session()
        self.connected = False

        # Try to connect to the service
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.connected = True
                service_status = response.json()
                logger.info(f"Connected to language service: {service_status}")
            else:
                logger.warning(f"Language service returned status code {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to connect to language service: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected to the service."""
        return self.connected

    def generate_dialogue(self,
                          npc_id: str,
                          npc_type: str,
                          npc_race: str,
                          npc_attitude: str,
                          situation: str,
                          topic: Optional[str] = None,
                          npc_name: Optional[str] = None,
                          history: Optional[List[Dict[str, str]]] = None,
                          personality_traits: Optional[List[str]] = None,
                          knowledge: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate dialogue for an NPC."""
        if not self.connected:
            return self._create_fallback_response(
                f"NPC {npc_name or npc_type}: \"Greetings, adventurer.\""
            )

        try:
            request_data = {
                "npc_id": npc_id,
                "npc_type": npc_type,
                "npc_race": npc_race,
                "npc_attitude": npc_attitude,
                "situation": situation,
                "topic": topic,
                "npc_name": npc_name,
                "history": history or [],
                "personality_traits": personality_traits or [],
                "knowledge": knowledge or {}
            }

            response = self.session.post(
                f"{self.base_url}/generate/dialogue",
                json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating dialogue: {response.status_code} - {response.text}")
                return self._create_fallback_response(
                    f"NPC {npc_name or npc_type}: \"Greetings, adventurer.\""
                )
        except Exception as e:
            logger.error(f"Exception generating dialogue: {e}")
            return self._create_fallback_response(
                f"NPC {npc_name or npc_type}: \"Greetings, adventurer.\""
            )

    def generate_description(self,
                             location_type: str,
                             time_of_day: str = "day",
                             weather: str = "clear",
                             specific_features: Optional[List[str]] = None,
                             atmosphere: Optional[str] = "neutral",
                             visited_before: bool = False,
                             significant_events: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate an environment description."""
        if not self.connected:
            return self._create_fallback_response(
                f"You find yourself in a {location_type}. It is {time_of_day} and the weather is {weather}."
            )

        try:
            request_data = {
                "location_type": location_type,
                "time_of_day": time_of_day,
                "weather": weather,
                "specific_features": specific_features,
                "atmosphere": atmosphere,
                "visited_before": visited_before,
                "significant_events": significant_events
            }

            response = self.session.post(
                f"{self.base_url}/generate/description",
                json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating description: {response.status_code} - {response.text}")
                return self._create_fallback_response(
                    f"You find yourself in a {location_type}. It is {time_of_day} and the weather is {weather}."
                )
        except Exception as e:
            logger.error(f"Exception generating description: {e}")
            return self._create_fallback_response(
                f"You find yourself in a {location_type}. It is {time_of_day} and the weather is {weather}."
            )

    def generate_combat(self,
                        action_type: str,
                        outcome: str,
                        attacker: str,
                        defender: Optional[str] = None,
                        weapon: Optional[str] = None,
                        spell: Optional[str] = None,
                        damage_amount: Optional[int] = None,
                        critical: bool = False,
                        combat_state: Optional[Dict[str, Any]] = None,
                        previous_actions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate a combat description."""
        if not self.connected:
            fallback = f"{attacker} attacks {defender or 'the enemy'} and "
            fallback += "hits." if "hit" in outcome else "misses."
            return self._create_fallback_response(fallback)

        try:
            request_data = {
                "action_type": action_type,
                "outcome": outcome,
                "attacker": attacker,
                "defender": defender,
                "weapon": weapon,
                "spell": spell,
                "damage_amount": damage_amount,
                "critical": critical,
                "combat_state": combat_state or {},
                "previous_actions": previous_actions or []
            }

            response = self.session.post(
                f"{self.base_url}/generate/combat",
                json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating combat: {response.status_code} - {response.text}")
                fallback = f"{attacker} attacks {defender or 'the enemy'} and "
                fallback += "hits." if "hit" in outcome else "misses."
                return self._create_fallback_response(fallback)
        except Exception as e:
            logger.error(f"Exception generating combat: {e}")
            fallback = f"{attacker} attacks {defender or 'the enemy'} and "
            fallback += "hits." if "hit" in outcome else "misses."
            return self._create_fallback_response(fallback)

    def generate_quest(self,
                       quest_type: Optional[str] = None,
                       difficulty: str = "medium",
                       level: int = 1,
                       location: Optional[str] = None,
                       giver: Optional[str] = None,
                       party_info: Optional[Dict[str, Any]] = None,
                       world_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a quest."""
        if not self.connected:
            fallback_quest = {
                "title": "A Simple Task",
                "type": quest_type or "retrieval",
                "description": f"A simple task is requested of brave adventurers in {location or 'the area'}.",
                "objective": "Complete the task",
                "rewards": ["Gold", "Experience"],
                "difficulty": difficulty,
                "level": level,
                "location": location or "Nearby",
                "giver": giver or "Village Elder"
            }
            return self._create_fallback_response(json.dumps(fallback_quest))

        try:
            request_data = {
                "quest_type": quest_type,
                "difficulty": difficulty,
                "level": level,
                "location": location,
                "giver": giver,
                "party_info": party_info or {},
                "world_state": world_state or {}
            }

            response = self.session.post(
                f"{self.base_url}/generate/quest",
                json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating quest: {response.status_code} - {response.text}")
                fallback_quest = {
                    "title": "A Simple Task",
                    "type": quest_type or "retrieval",
                    "description": f"A simple task is requested of brave adventurers in {location or 'the area'}.",
                    "objective": "Complete the task",
                    "rewards": ["Gold", "Experience"],
                    "difficulty": difficulty,
                    "level": level,
                    "location": location or "Nearby",
                    "giver": giver or "Village Elder"
                }
                return self._create_fallback_response(json.dumps(fallback_quest))
        except Exception as e:
            logger.error(f"Exception generating quest: {e}")
            fallback_quest = {
                "title": "A Simple Task",
                "type": quest_type or "retrieval",
                "description": f"A simple task is requested of brave adventurers in {location or 'the area'}.",
                "objective": "Complete the task",
                "rewards": ["Gold", "Experience"],
                "difficulty": difficulty,
                "level": level,
                "location": location or "Nearby",
                "giver": giver or "Village Elder"
            }
            return self._create_fallback_response(json.dumps(fallback_quest))

    def generate_transition(self,
                            from_scene: str,
                            to_scene: str,
                            mood: str = "neutral",
                            time_passed: str = "immediate",
                            party_state: Optional[Dict[str, Any]] = None,
                            significant_events: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a narrative transition."""
        if not self.connected:
            return self._create_fallback_response(
                f"The party travels from {from_scene} to {to_scene}."
            )

        try:
            request_data = {
                "from_scene": from_scene,
                "to_scene": to_scene,
                "mood": mood,
                "time_passed": time_passed,
                "party_state": party_state or {},
                "significant_events": significant_events or []
            }

            response = self.session.post(
                f"{self.base_url}/generate/transition",
                json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating transition: {response.status_code} - {response.text}")
                return self._create_fallback_response(
                    f"The party travels from {from_scene} to {to_scene}."
                )
        except Exception as e:
            logger.error(f"Exception generating transition: {e}")
            return self._create_fallback_response(
                f"The party travels from {from_scene} to {to_scene}."
            )

    def _create_fallback_response(self, text: str) -> Dict[str, Any]:
        """Create a fallback response when the service is unavailable."""
        return {
            "text": text,
            "status": "fallback",
            "message": "Using fallback due to service unavailability"
        }