# MapEventSystem.py
# Part of the MapAI subsystem for D&D5e CoreAI integration
# Handles world events that affect the map and tracks changes over time

import os
import json
import logging
import time
import random
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mapai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MapEventSystem")


class MapEventSystem:
    """
    Handles world events that affect the map and geographic/political elements.
    Tracks event history, manages event generation, and applies event effects to the world state.
    """

    def __init__(self,
                 map_file_path: str = "C:\\DnD5e\\Mapping\\Test.map",
                 event_data_path: str = "C:\\MapAI\\EventData",
                 world_state=None):
        """
        Initialize the Map Event System.

        Args:
            map_file_path: Path to the Azgaar map file (.map format)
            event_data_path: Path to store event data and history
            world_state: Reference to a MapWorldState object
        """
        # Configure logging
        logger.info("Initializing Map Event System...")

        # Set core paths and configurations
        self.map_file_path = map_file_path
        self.event_data_path = event_data_path
        self.world_state = world_state

        # Initialize state
        self.map_data = None
        self.event_history = []
        self.active_events = []
        self.event_templates = {}
        self.last_event_time = 0
        self.world_time = {
            "year": 1500,
            "month": 1,
            "day": 1,
            "season": "spring",
            "climate_modifier": 0
        }

        # Create event data directory if it doesn't exist
        os.makedirs(event_data_path, exist_ok=True)

        # Load map data
        self._load_map_data()

        # Load event templates
        self._load_event_templates()

        # Load event history if exists
        self._load_event_history()

        logger.info("Map Event System initialized successfully")

    def _load_map_data(self) -> None:
        """
        Load map data from Azgaar's map file.
        """
        try:
            # Check file extension
            file_extension = os.path.splitext(self.map_file_path)[1].lower()

            if file_extension == '.map':
                logger.info(f"Loading map data from .map file: {self.map_file_path}")
                with open(self.map_file_path, 'r', encoding='utf-8') as f:
                    self.map_data = json.load(f)
            elif file_extension == '.json':
                logger.info(f"Loading map data from JSON export: {self.map_file_path}")
                with open(self.map_file_path, 'r', encoding='utf-8') as f:
                    self.map_data = json.load(f)
            else:
                logger.error(f"Unsupported map file format: {file_extension}")
                raise ValueError(f"Unsupported map file format: {file_extension}")

            # Log success
            if self.map_data:
                logger.info(f"Map data loaded successfully with {len(self.map_data.get('cells', []))} cells")
            else:
                logger.warning("Map data loaded but appears to be empty")

        except Exception as e:
            logger.error(f"Error loading map data: {e}")
            # Create empty map data structure as fallback
            self.map_data = {
                "info": {
                    "name": "Empty Map",
                    "description": "Fallback empty map",
                    "version": "0.1",
                    "created": time.time()
                },
                "cells": [],
                "burgs": [],
                "states": [],
                "provinces": [],
                "cultures": [],
                "religions": []
            }

    def _load_event_templates(self) -> None:
        """
        Load event templates from the event data path.
        """
        template_path = os.path.join(self.event_data_path, "event_templates.json")

        try:
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.event_templates = json.load(f)
                logger.info(f"Loaded {len(self.event_templates)} event templates")
            else:
                # Create default templates
                self._create_default_event_templates()
                # Save them
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(self.event_templates, f, indent=2)
                logger.info(f"Created and saved default event templates")
        except Exception as e:
            logger.error(f"Error loading event templates: {e}")
            # Create default templates without saving
            self._create_default_event_templates()

    def _create_default_event_templates(self) -> None:
        """
        Create default event templates.
        """
        self.event_templates = {
            "natural_disaster": {
                "types": [
                    {
                        "id": "earthquake",
                        "name": "Earthquake",
                        "description": "A powerful tremor shakes the ground, causing destruction",
                        "duration": [7, 14],  # days
                        "radius": [50, 200],  # miles
                        "severity_levels": [
                            {"name": "minor", "damage_factor": 0.1, "recovery_time": 30},  # days
                            {"name": "moderate", "damage_factor": 0.3, "recovery_time": 90},
                            {"name": "major", "damage_factor": 0.7, "recovery_time": 180},
                            {"name": "catastrophic", "damage_factor": 0.9, "recovery_time": 365}
                        ],
                        "biome_modifiers": {
                            "mountain": 2.0,
                            "hills": 1.5,
                            "desert": 1.2
                        },
                        "effects": {
                            "population": -0.2,
                            "economy": -0.3,
                            "buildings": -0.4,
                            "terrain": "may create new features"
                        }
                    },
                    {
                        "id": "flood",
                        "name": "Flood",
                        "description": "Rising waters inundate the land",
                        "duration": [14, 30],
                        "radius": [20, 100],
                        "severity_levels": [
                            {"name": "minor", "damage_factor": 0.1, "recovery_time": 20},
                            {"name": "moderate", "damage_factor": 0.2, "recovery_time": 60},
                            {"name": "major", "damage_factor": 0.5, "recovery_time": 120},
                            {"name": "catastrophic", "damage_factor": 0.8, "recovery_time": 240}
                        ],
                        "biome_modifiers": {
                            "river": 2.0,
                            "lake": 1.8,
                            "floodplain": 3.0,
                            "desert": 0.2
                        },
                        "effects": {
                            "population": -0.1,
                            "economy": -0.3,
                            "buildings": -0.3,
                            "terrain": "may change to wetland temporarily",
                            "agriculture": -0.5
                        }
                    },
                    {
                        "id": "drought",
                        "name": "Drought",
                        "description": "A prolonged period without rain causes water shortages",
                        "duration": [60, 180],
                        "radius": [100, 500],
                        "severity_levels": [
                            {"name": "minor", "damage_factor": 0.1, "recovery_time": 30},
                            {"name": "moderate", "damage_factor": 0.3, "recovery_time": 90},
                            {"name": "major", "damage_factor": 0.6, "recovery_time": 180},
                            {"name": "catastrophic", "damage_factor": 0.8, "recovery_time": 365}
                        ],
                        "biome_modifiers": {
                            "desert": 2.0,
                            "savanna": 1.5,
                            "grassland": 1.3,
                            "wetland": 0.3
                        },
                        "effects": {
                            "population": -0.05,
                            "economy": -0.2,
                            "agriculture": -0.7,
                            "water_sources": -0.5
                        }
                    }
                ]
            },
            "political_event": {
                "types": [
                    {
                        "id": "war",
                        "name": "War",
                        "description": "Armed conflict between states",
                        "duration": [90, 1095],  # 3 months to 3 years
                        "radius": [0, 0],  # entire states
                        "severity_levels": [
                            {"name": "border_conflict", "damage_factor": 0.1, "stability_impact": -0.2},
                            {"name": "limited_war", "damage_factor": 0.3, "stability_impact": -0.4},
                            {"name": "full_scale_war", "damage_factor": 0.6, "stability_impact": -0.7},
                            {"name": "total_war", "damage_factor": 0.9, "stability_impact": -0.9}
                        ],
                        "possible_outcomes": [
                            "white_peace",
                            "minor_territorial_change",
                            "major_territorial_change",
                            "vassal_state",
                            "complete_annexation"
                        ],
                        "effects": {
                            "population": -0.2,
                            "economy": -0.4,
                            "military": -0.5,
                            "diplomatic_relations": "hostile",
                            "borders": "may change"
                        }
                    },
                    {
                        "id": "rebellion",
                        "name": "Rebellion",
                        "description": "Uprising against the ruling authority",
                        "duration": [30, 365],
                        "radius": [50, 200],
                        "severity_levels": [
                            {"name": "unrest", "damage_factor": 0.05, "stability_impact": -0.1},
                            {"name": "riots", "damage_factor": 0.2, "stability_impact": -0.3},
                            {"name": "armed_rebellion", "damage_factor": 0.4, "stability_impact": -0.6},
                            {"name": "civil_war", "damage_factor": 0.7, "stability_impact": -0.9}
                        ],
                        "possible_outcomes": [
                            "suppressed",
                            "concessions_made",
                            "autonomy_granted",
                            "new_leadership",
                            "new_state_formed"
                        ],
                        "effects": {
                            "population": -0.1,
                            "economy": -0.3,
                            "stability": -0.5,
                            "governance": "may change",
                            "borders": "may change"
                        }
                    }
                ]
            },
            "cultural_event": {
                "types": [
                    {
                        "id": "festival",
                        "name": "Festival",
                        "description": "A large celebration or cultural event",
                        "duration": [1, 14],
                        "radius": [10, 50],
                        "significance_levels": [
                            {"name": "local", "participation_factor": 0.1, "economic_boost": 0.05},
                            {"name": "regional", "participation_factor": 0.3, "economic_boost": 0.1},
                            {"name": "national", "participation_factor": 0.6, "economic_boost": 0.2},
                            {"name": "international", "participation_factor": 0.8, "economic_boost": 0.3}
                        ],
                        "effects": {
                            "economy": 0.2,
                            "cultural_unity": 0.3,
                            "happiness": 0.4,
                            "tourism": 0.5
                        }
                    },
                    {
                        "id": "migration",
                        "name": "Migration",
                        "description": "Movement of people from one area to another",
                        "duration": [30, 365],
                        "radius": [100, 1000],
                        "scale_levels": [
                            {"name": "small_group", "population_factor": 0.01, "cultural_impact": 0.02},
                            {"name": "large_group", "population_factor": 0.05, "cultural_impact": 0.1},
                            {"name": "mass_migration", "population_factor": 0.2, "cultural_impact": 0.3},
                            {"name": "exodus", "population_factor": 0.5, "cultural_impact": 0.6}
                        ],
                        "causes": [
                            "war",
                            "natural_disaster",
                            "economic_opportunity",
                            "religious_persecution",
                            "climate_change"
                        ],
                        "effects": {
                            "source_population": -0.1,
                            "destination_population": 0.1,
                            "cultural_diversity": 0.2,
                            "economy": 0.1
                        }
                    }
                ]
            }
        }

    def _load_event_history(self) -> None:
        """
        Load event history from the event data path.
        """
        history_path = os.path.join(self.event_data_path, "event_history.json")
        active_path = os.path.join(self.event_data_path, "active_events.json")

        try:
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.event_history = json.load(f)
                logger.info(f"Loaded {len(self.event_history)} historical events")

            if os.path.exists(active_path):
                with open(active_path, 'r', encoding='utf-8') as f:
                    self.active_events = json.load(f)
                logger.info(f"Loaded {len(self.active_events)} active events")
        except Exception as e:
            logger.error(f"Error loading event history: {e}")
            self.event_history = []
            self.active_events = []

    def save_state(self) -> bool:
        """
        Save the current event state.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save event history
            history_path = os.path.join(self.event_data_path, "event_history.json")
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.event_history, f, indent=2)

            # Save active events
            active_path = os.path.join(self.event_data_path, "active_events.json")
            with open(active_path, 'w', encoding='utf-8') as f:
                json.dump(self.active_events, f, indent=2)

            logger.info("Event state saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving event state: {e}")
            return False

    def advance_time(self, days: int = 1) -> Dict[str, Any]:
        """
        Advance the world time and process any events that should occur.

        Args:
            days: Number of days to advance

        Returns:
            Dictionary with time advancement results
        """
        initial_year = self.world_time["year"]
        initial_month = self.world_time["month"]
        initial_day = self.world_time["day"]

        # Convert current time to datetime
        current_date = datetime(
            year=self.world_time["year"],
            month=self.world_time["month"],
            day=self.world_time["day"]
        )

        # Advance time
        new_date = current_date + timedelta(days=days)

        # Update world time
        self.world_time["year"] = new_date.year
        self.world_time["month"] = new_date.month
        self.world_time["day"] = new_date.day

        # Update season
        self._update_season()

        # Process active events
        expired_events = []
        updated_events = []

        for event in self.active_events:
            # Calculate event end date
            start_date = datetime.fromtimestamp(event["start_time"])
            end_date = start_date + timedelta(days=event["duration"])

            # Check if event has expired
            if new_date >= end_date:
                # Process event end effects
                self._process_event_end(event)
                expired_events.append(event)
            else:
                # Process ongoing event effects
                updated_event = self._process_ongoing_event(event, days)
                updated_events.append(updated_event)

        # Remove expired events from active events
        for event in expired_events:
            self.active_events.remove(event)
            # Add to history
            event["status"] = "completed"
            event["end_time"] = time.time()
            self.event_history.append(event)

        # Update active events with any changes
        for i, updated_event in enumerate(updated_events):
            for j, active_event in enumerate(self.active_events):
                if active_event["id"] == updated_event["id"]:
                    self.active_events[j] = updated_event
                    break

        # Generate new events
        new_events = self._generate_events(days)

        # Add new events to active events
        self.active_events.extend(new_events)

        # Save state
        self.save_state()

        # Create time advancement results
        results = {
            "previous_date": {
                "year": initial_year,
                "month": initial_month,
                "day": initial_day
            },
            "new_date": {
                "year": self.world_time["year"],
                "month": self.world_time["month"],
                "day": self.world_time["day"],
                "season": self.world_time["season"]
            },
            "days_advanced": days,
            "expired_events": expired_events,
            "new_events": new_events,
            "active_events": self.active_events
        }

        return results

    def _update_season(self) -> None:
        """
        Update the current season based on the month.
        """
        month = self.world_time["month"]

        if 3 <= month <= 5:
            self.world_time["season"] = "spring"
        elif 6 <= month <= 8:
            self.world_time["season"] = "summer"
        elif 9 <= month <= 11:
            self.world_time["season"] = "autumn"
        else:  # 12, 1, 2
            self.world_time["season"] = "winter"

    def _process_event_end(self, event: Dict[str, Any]) -> None:
        """
        Process the end of an event and apply any final effects.

        Args:
            event: The event that is ending
        """
        event_type = event["type"]

        if event_type == "natural_disaster":
            # Natural disaster recovery
            if self.world_state:
                # Notify world state about event end
                recovery_data = {
                    "event_id": event["id"],
                    "event_type": event_type,
                    "disaster_type": event["disaster_type"],
                    "affected_area": event["affected_area"],
                    "severity": event["severity"],
                    "recovery_factor": 1.0  # fully recovered
                }
                self.world_state.update_from_event_end(recovery_data)

            # Log event end
            logger.info(f"Natural disaster {event['disaster_type']} has ended. ID: {event['id']}")

        elif event_type == "political_event":
            # Process political event resolution
            if event["political_type"] == "war":
                # Determine war outcome
                outcome = self._resolve_war(event)

                # Apply outcome effects
                if self.world_state:
                    outcome_data = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "political_type": event["political_type"],
                        "involved_states": event["involved_states"],
                        "outcome": outcome
                    }
                    self.world_state.update_from_event_end(outcome_data)

                # Log war end
                logger.info(
                    f"War between {event['involved_states']} has ended with outcome: {outcome}. ID: {event['id']}")

            elif event["political_type"] == "rebellion":
                # Determine rebellion outcome
                outcome = self._resolve_rebellion(event)

                # Apply outcome effects
                if self.world_state:
                    outcome_data = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "political_type": event["political_type"],
                        "involved_state": event["involved_state"],
                        "rebellion_location": event["location"],
                        "outcome": outcome
                    }
                    self.world_state.update_from_event_end(outcome_data)

                # Log rebellion end
                logger.info(
                    f"Rebellion in {event['involved_state']} has ended with outcome: {outcome}. ID: {event['id']}")

        elif event_type == "cultural_event":
            # Process cultural event end
            if event["cultural_type"] == "festival":
                # Apply festival end effects
                if self.world_state:
                    festival_data = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "cultural_type": event["cultural_type"],
                        "location": event["location"],
                        "significance": event["significance"],
                        "economic_boost": event.get("economic_boost", 0.1)
                    }
                    self.world_state.update_from_event_end(festival_data)

                # Log festival end
                logger.info(f"Festival in {event['location']} has ended. ID: {event['id']}")

            elif event["cultural_type"] == "migration":
                # Apply migration end effects
                if self.world_state:
                    migration_data = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "cultural_type": event["cultural_type"],
                        "source": event["source"],
                        "destination": event["destination"],
                        "population_moved": event.get("population_moved", 0)
                    }
                    self.world_state.update_from_event_end(migration_data)

                # Log migration end
                logger.info(f"Migration from {event['source']} to {event['destination']} has ended. ID: {event['id']}")

    def _process_ongoing_event(self, event: Dict[str, Any], days_passed: int) -> Dict[str, Any]:
        """
        Process an ongoing event and apply any periodic effects.

        Args:
            event: The ongoing event
            days_passed: Number of days that have passed

        Returns:
            Updated event data
        """
        event_type = event["type"]
        updated_event = event.copy()

        if event_type == "natural_disaster":
            # Continue natural disaster effects
            if self.world_state and days_passed > 0:
                # Calculate ongoing damage based on days passed
                ongoing_effect = {
                    "event_id": event["id"],
                    "event_type": event_type,
                    "disaster_type": event["disaster_type"],
                    "affected_area": event["affected_area"],
                    "severity": event["severity"],
                    "days_passed": days_passed,
                    "ongoing_damage": event["severity"]["damage_factor"] * (days_passed / event["duration"])
                }
                self.world_state.update_from_ongoing_event(ongoing_effect)

        elif event_type == "political_event":
            if event["political_type"] == "war":
                # Continue war effects
                # Update war progress
                if "war_progress" not in updated_event:
                    updated_event["war_progress"] = 0

                # Determine how the war is progressing
                progress_change = self._calculate_war_progress(event, days_passed)
                updated_event["war_progress"] += progress_change

                # Clamp war progress to -100 to 100 range
                updated_event["war_progress"] = max(-100, min(100, updated_event["war_progress"]))

                # Apply ongoing war effects
                if self.world_state:
                    war_effect = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "political_type": event["political_type"],
                        "involved_states": event["involved_states"],
                        "war_progress": updated_event["war_progress"],
                        "days_passed": days_passed
                    }
                    self.world_state.update_from_ongoing_event(war_effect)

            elif event["political_type"] == "rebellion":
                # Continue rebellion effects
                # Update rebellion strength
                if "rebellion_strength" not in updated_event:
                    updated_event["rebellion_strength"] = 0.5  # Start at 50%

                # Determine how the rebellion is progressing
                strength_change = self._calculate_rebellion_strength(event, days_passed)
                updated_event["rebellion_strength"] += strength_change

                # Clamp rebellion strength to 0.0 to 1.0 range
                updated_event["rebellion_strength"] = max(0.0, min(1.0, updated_event["rebellion_strength"]))

                # Apply ongoing rebellion effects
                if self.world_state:
                    rebellion_effect = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "political_type": event["political_type"],
                        "involved_state": event["involved_state"],
                        "rebellion_location": event["location"],
                        "rebellion_strength": updated_event["rebellion_strength"],
                        "days_passed": days_passed
                    }
                    self.world_state.update_from_ongoing_event(rebellion_effect)

        elif event_type == "cultural_event":
            # Continue cultural event effects
            if event["cultural_type"] == "festival":
                # Festivals have minimal ongoing effects, just track progress
                if "progress" not in updated_event:
                    updated_event["progress"] = 0

                # Update progress percentage
                progress_percent = min(100, (updated_event["progress"] + days_passed) / event["duration"] * 100)
                updated_event["progress"] = progress_percent

                # Apply ongoing festival effects
                if self.world_state:
                    festival_effect = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "cultural_type": event["cultural_type"],
                        "location": event["location"],
                        "significance": event["significance"],
                        "progress": progress_percent,
                        "days_passed": days_passed
                    }
                    self.world_state.update_from_ongoing_event(festival_effect)

            elif event["cultural_type"] == "migration":
                # Continue migration effects
                if "progress" not in updated_event:
                    updated_event["progress"] = 0
                    updated_event["population_moved"] = 0

                # Calculate how much population has moved
                total_population = event.get("total_population", 1000)
                population_per_day = total_population / event["duration"]
                new_population_moved = population_per_day * days_passed

                updated_event["population_moved"] += new_population_moved
                updated_event["progress"] = min(100, updated_event["population_moved"] / total_population * 100)

                # Apply ongoing migration effects
                if self.world_state:
                    migration_effect = {
                        "event_id": event["id"],
                        "event_type": event_type,
                        "cultural_type": event["cultural_type"],
                        "source": event["source"],
                        "destination": event["destination"],
                        "population_moved": updated_event["population_moved"],
                        "progress": updated_event["progress"],
                        "days_passed": days_passed
                    }
                    self.world_state.update_from_ongoing_event(migration_effect)

        return updated_event

    def _resolve_war(self, event: Dict[str, Any]) -> str:
        """
        Resolve the outcome of a war.

        Args:
            event: The war event

        Returns:
            The outcome of the war
        """
        # Get war progress
        war_progress = event.get("war_progress", 0)

        # Determine outcome based on war progress
        if war_progress > 80:
            return "complete_victory_attacker"
        elif war_progress > 40:
            return "partial_victory_attacker"
        elif war_progress > -40:
            return "white_peace"
        elif war_progress > -80:
            return "partial_victory_defender"
        else:
            return "complete_victory_defender"

    def _resolve_rebellion(self, event: Dict[str, Any]) -> str:
        """
        Resolve the outcome of a rebellion.

        Args:
            event: The rebellion event

        Returns:
            The outcome of the rebellion
        """
        # Get rebellion strength
        rebellion_strength = event.get("rebellion_strength", 0.5)

        # Determine outcome based on rebellion strength
        if rebellion_strength > 0.9:
            return "new_state_formed"
        elif rebellion_strength > 0.7:
            return "autonomy_granted"
        elif rebellion_strength > 0.5:
            return "concessions_made"
        elif rebellion_strength > 0.3:
            return "partially_suppressed"
        else:
            return "fully_suppressed"

    def _calculate_war_progress(self, event: Dict[str, Any], days_passed: int) -> float:
        """
        Calculate how a war progresses over time.

        Args:
            event: The war event
            days_passed: Number of days that have passed

        Returns:
            Change in war progress
        """
        # In a real implementation, this would consider military strength,
        # terrain, alliances, etc. For now, use a simple random model

        # War has natural fluctuations
        base_change = random.uniform(-5, 5)

        # Get advantage factor from event data
        advantage_factor = event.get("advantage_factor", 0)

        # Calculate progress change
        progress_change = base_change + (advantage_factor * days_passed / 10)

        return progress_change

    def _calculate_rebellion_strength(self, event: Dict[str, Any], days_passed: int) -> float:
        """
        Calculate how a rebellion's strength changes over time.

        Args:
            event: The rebellion event
            days_passed: Number of days that have passed

        Returns:
            Change in rebellion strength
        """
        # In a real implementation, this would consider state stability,
        # popular support, terrain, etc. For now, use a simple model

        # Base fluctuation
        base_change = random.uniform(-0.05, 0.05)

        # Get support factor from event data
        support_factor = event.get("support_factor", 0)

        # Calculate strength change
        strength_change = base_change + (support_factor * days_passed / 100)

        return strength_change

    def _generate_events(self, days_passed: int) -> List[Dict[str, Any]]:
        """
        Generate new events based on the current state of the world.

        Args:
            days_passed: Number of days that have passed

        Returns:
            List of new events
        """
        new_events = []

        # Calculate base event probabilities
        base_natural_disaster_chance = 0.001 * days_passed  # 0.1% per day
        base_political_event_chance = 0.002 * days_passed  # 0.2% per day
        base_cultural_event_chance = 0.005 * days_passed  # 0.5% per day

        # Adjust based on season
        season_modifiers = {
            "spring": {"natural_disaster": 1.5, "political_event": 1.0, "cultural_event": 1.2},
            "summer": {"natural_disaster": 1.2, "political_event": 0.8, "cultural_event": 1.5},
            "autumn": {"natural_disaster": 1.0, "political_event": 1.2, "cultural_event": 1.3},
            "winter": {"natural_disaster": 0.8, "political_event": 1.5, "cultural_event": 0.7}
        }

        current_season = self.world_time["season"]
        season_mod = season_modifiers.get(current_season,
                                          {"natural_disaster": 1.0, "political_event": 1.0, "cultural_event": 1.0})

        # Roll for natural disasters
        natural_disaster_chance = base_natural_disaster_chance * season_mod["natural_disaster"]
        if random.random() < natural_disaster_chance:
            new_disaster = self._generate_natural_disaster()
            if new_disaster:
                new_events.append(new_disaster)

        # Roll for political events
        political_event_chance = base_political_event_chance * season_mod["political_event"]
        if random.random() < political_event_chance:
            new_political_event = self._generate_political_event()
            if new_political_event:
                new_events.append(new_political_event)

        # Roll for cultural events
        cultural_event_chance = base_cultural_event_chance * season_mod["cultural_event"]
        if random.random() < cultural_event_chance:
            new_cultural_event = self._generate_cultural_event()
            if new_cultural_event:
                new_events.append(new_cultural_event)

        return new_events

    def _generate_natural_disaster(self) -> Optional[Dict[str, Any]]:
        """
        Generate a natural disaster event.

        Returns:
            Natural disaster event data or None if generation fails
        """
        try:
            # Get disaster templates
            if "natural_disaster" not in self.event_templates or not self.event_templates["natural_disaster"]["types"]:
                logger.warning("No natural disaster templates available")
                return None

            disaster_types = self.event_templates["natural_disaster"]["types"]

            # Select a random disaster type
            disaster_type = random.choice(disaster_types)

            # Select severity
            severity_levels = disaster_type["severity_levels"]
            severity = random.choice(severity_levels)

            # Select duration
            min_duration, max_duration = disaster_type.get("duration", [7, 30])
            duration = random.randint(min_duration, max_duration)

            # Select radius
            min_radius, max_radius = disaster_type.get("radius", [20, 100])
            radius = random.randint(min_radius, max_radius)

            # Select location (random for now, could be more sophisticated)
            location = self._select_random_location()

            # Create affected area
            affected_area = {
                "center": location,
                "radius": radius,
                "type": "circle"
            }

            # Create event
            event = {
                "id": f"disaster_{int(time.time())}_{random.randint(1000, 9999)}",
                "type": "natural_disaster",
                "disaster_type": disaster_type["id"],
                "name": disaster_type["name"],
                "description": disaster_type["description"],
                "severity": severity,
                "affected_area": affected_area,
                "start_time": time.time(),
                "duration": duration,
                "status": "active",
                "effects": disaster_type["effects"]
            }

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Log event creation
            logger.info(f"Generated natural disaster: {event['name']} (Severity: {severity['name']})")

            return event

        except Exception as e:
            logger.error(f"Error generating natural disaster: {e}")
            return None

    def _generate_political_event(self) -> Optional[Dict[str, Any]]:
        """
        Generate a political event.

        Returns:
            Political event data or None if generation fails
        """
        try:
            # Get political event templates
            if "political_event" not in self.event_templates or not self.event_templates["political_event"]["types"]:
                logger.warning("No political event templates available")
                return None

            event_types = self.event_templates["political_event"]["types"]

            # Select a random event type
            event_type = random.choice(event_types)

            # Process based on event type
            if event_type["id"] == "war":
                # Generate war event

                # Select two different states
                states = self._get_valid_states()
                if len(states) < 2:
                    logger.warning("Not enough states to generate war")
                    return None

                # Select two random states
                state1, state2 = random.sample(states, 2)

                # Select severity
                severity_levels = event_type["severity_levels"]
                severity = random.choice(severity_levels)

                # Select duration
                min_duration, max_duration = event_type.get("duration", [90, 365])
                duration = random.randint(min_duration, max_duration)

                # Determine advantage factor (-1.0 to 1.0)
                # Positive means attacker advantage, negative means defender advantage
                advantage_factor = random.uniform(-1.0, 1.0)

                # Create event
                event = {
                    "id": f"war_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "political_event",
                    "political_type": "war",
                    "name": f"War between {state1['name']} and {state2['name']}",
                    "description": f"Armed conflict between {state1['name']} and {state2['name']}",
                    "involved_states": [
                        {"id": state1["i"], "name": state1["name"], "role": "attacker"},
                        {"id": state2["i"], "name": state2["name"], "role": "defender"}
                    ],
                    "severity": severity,
                    "start_time": time.time(),
                    "duration": duration,
                    "advantage_factor": advantage_factor,
                    "war_progress": 0,  # 0 is neutral, positive means attacker winning
                    "status": "active",
                    "possible_outcomes": event_type["possible_outcomes"],
                    "effects": event_type["effects"]
                }

            elif event_type["id"] == "rebellion":
                # Generate rebellion event

                # Select a state
                states = self._get_valid_states()
                if not states:
                    logger.warning("No valid states to generate rebellion")
                    return None

                state = random.choice(states)

                # Select a location within the state
                location = self._select_location_in_state(state)
                if not location:
                    logger.warning(f"Could not find location in state {state['name']}")
                    return None

                # Select severity
                severity_levels = event_type["severity_levels"]
                severity = random.choice(severity_levels)

                # Select duration
                min_duration, max_duration = event_type.get("duration", [30, 365])
                duration = random.randint(min_duration, max_duration)

                # Determine support factor (0.0 to 1.0)
                # Higher means more rebel support
                support_factor = random.uniform(0.0, 1.0)

                # Create event
                event = {
                    "id": f"rebellion_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "political_event",
                    "political_type": "rebellion",
                    "name": f"Rebellion in {state['name']}",
                    "description": f"Uprising against the ruling authority in {state['name']}",
                    "involved_state": {"id": state["i"], "name": state["name"]},
                    "location": location,
                    "severity": severity,
                    "start_time": time.time(),
                    "duration": duration,
                    "support_factor": support_factor,
                    "rebellion_strength": 0.5,  # Start at 50%
                    "status": "active",
                    "possible_outcomes": event_type["possible_outcomes"],
                    "effects": event_type["effects"]
                }

            else:
                logger.warning(f"Unknown political event type: {event_type['id']}")
                return None

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Log event creation
            logger.info(f"Generated political event: {event['name']} (Type: {event_type['id']})")

            return event

        except Exception as e:
            logger.error(f"Error generating political event: {e}")
            return None

    def _generate_cultural_event(self) -> Optional[Dict[str, Any]]:
        """
        Generate a cultural event.

        Returns:
            Cultural event data or None if generation fails
        """
        try:
            # Get cultural event templates
            if "cultural_event" not in self.event_templates or not self.event_templates["cultural_event"]["types"]:
                logger.warning("No cultural event templates available")
                return None

            event_types = self.event_templates["cultural_event"]["types"]

            # Select a random event type
            event_type = random.choice(event_types)

            # Process based on event type
            if event_type["id"] == "festival":
                # Generate festival event

                # Select a location (preferably a burg)
                location = self._select_random_burg()
                if not location:
                    logger.warning("Could not find a valid location for festival")
                    return None

                # Select significance
                significance_levels = event_type["significance_levels"]
                significance = random.choice(significance_levels)

                # Select duration
                min_duration, max_duration = event_type.get("duration", [1, 14])
                duration = random.randint(min_duration, max_duration)

                # Create event
                event = {
                    "id": f"festival_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "cultural_event",
                    "cultural_type": "festival",
                    "name": f"Festival in {location['name']}",
                    "description": f"A {significance['name']} festival in {location['name']}",
                    "location": location,
                    "significance": significance,
                    "start_time": time.time(),
                    "duration": duration,
                    "economic_boost": significance["economic_boost"],
                    "status": "active",
                    "effects": event_type["effects"]
                }

            elif event_type["id"] == "migration":
                # Generate migration event

                # Select source and destination
                states = self._get_valid_states()
                if len(states) < 2:
                    logger.warning("Not enough states to generate migration")
                    return None

                # Select two random states
                source_state, destination_state = random.sample(states, 2)

                # Select scale
                scale_levels = event_type["scale_levels"]
                scale = random.choice(scale_levels)

                # Select duration
                min_duration, max_duration = event_type.get("duration", [30, 365])
                duration = random.randint(min_duration, max_duration)

                # Select cause
                cause = random.choice(event_type["causes"])

                # Estimate total population to migrate
                # In a real implementation, would get actual population data
                source_population = 100000  # Placeholder
                total_population = int(source_population * scale["population_factor"])

                # Create event
                event = {
                    "id": f"migration_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "cultural_event",
                    "cultural_type": "migration",
                    "name": f"Migration from {source_state['name']} to {destination_state['name']}",
                    "description": f"Movement of people from {source_state['name']} to {destination_state['name']} due to {cause}",
                    "source": source_state,
                    "destination": destination_state,
                    "scale": scale,
                    "cause": cause,
                    "start_time": time.time(),
                    "duration": duration,
                    "total_population": total_population,
                    "population_moved": 0,
                    "status": "active",
                    "effects": event_type["effects"]
                }

            else:
                logger.warning(f"Unknown cultural event type: {event_type['id']}")
                return None

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Log event creation
            logger.info(f"Generated cultural event: {event['name']} (Type: {event_type['id']})")

            return event

        except Exception as e:
            logger.error(f"Error generating cultural event: {e}")
            return None

    def _select_random_location(self) -> Dict[str, Any]:
        """
        Select a random location from the map.

        Returns:
            Location data
        """
        # Get all cells
        cells = self.map_data.get("cells", [])
        if not cells:
            # Create dummy location if no cells
            return {
                "x": 0,
                "y": 0,
                "biome": "grassland",
                "name": "Unknown Location"
            }

        # Select random cell
        cell = random.choice(cells)

        # Create location data
        if "p" in cell:
            x, y = cell["p"]
        else:
            x, y = 0, 0

        location = {
            "id": cell.get("i", 0),
            "x": x,
            "y": y,
            "biome": cell.get("biome", "grassland")
        }

        # Add feature name if available
        if "featureName" in cell:
            location["name"] = cell["featureName"]
        else:
            location["name"] = f"Location {cell.get('i', 0)}"

        return location

    def _select_random_burg(self) -> Optional[Dict[str, Any]]:
        """
        Select a random settlement from the map.

        Returns:
            Settlement data or None if no settlements exist
        """
        # Get all burgs
        burgs = self.map_data.get("burgs", [])
        valid_burgs = [b for b in burgs if not b.get("removed", False)]

        if not valid_burgs:
            return None

        # Select random burg
        burg = random.choice(valid_burgs)

        # Create location data
        location = {
            "id": burg.get("i", 0),
            "x": burg.get("x", 0),
            "y": burg.get("y", 0),
            "name": burg.get("name", f"Burg {burg.get('i', 0)}"),
            "population": burg.get("population", 1000),
            "state": burg.get("state", 0),
            "cell": burg.get("cell", 0)
        }

        return location

    def _get_valid_states(self) -> List[Dict[str, Any]]:
        """
        Get a list of valid states from the map.

        Returns:
            List of state data
        """
        # Get all states
        states = self.map_data.get("states", [])

        # Filter valid states (ignore neutral state with i=0)
        valid_states = [s for s in states if s.get("i", 0) > 0]

        return valid_states

    def _select_location_in_state(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Select a location within a specific state.

        Args:
            state: State data

        Returns:
            Location data or None if no suitable location found
        """
        # First try to find a burg in the state
        burgs = self.map_data.get("burgs", [])
        state_burgs = [b for b in burgs if not b.get("removed", False) and b.get("state") == state.get("i")]

        if state_burgs:
            # Select random burg in state
            burg = random.choice(state_burgs)

            return {
                "id": burg.get("i", 0),
                "x": burg.get("x", 0),
                "y": burg.get("y", 0),
                "name": burg.get("name", f"Burg {burg.get('i', 0)}"),
                "population": burg.get("population", 1000),
                "type": "burg"
            }

        # If no burgs found, try to find a cell in the state
        cells = self.map_data.get("cells", [])
        provinces = self.map_data.get("provinces", [])

        # Find provinces in the state
        state_provinces = [p.get("i") for p in provinces if p.get("state") == state.get("i")]

        # Find cells in these provinces
        state_cells = []
        for cell in cells:
            if cell.get("province") in state_provinces:
                state_cells.append(cell)

        if state_cells:
            # Select random cell in state
            cell = random.choice(state_cells)

            # Create location data
            if "p" in cell:
                x, y = cell["p"]
            else:
                x, y = 0, 0

            location = {
                "id": cell.get("i", 0),
                "x": x,
                "y": y,
                "biome": cell.get("biome", "grassland"),
                "type": "cell"
            }

            # Add feature name if available
            if "featureName" in cell:
                location["name"] = cell["featureName"]
            else:
                location["name"] = f"Location {cell.get('i', 0)}"

            return location

        # If no suitable location found
        return None

        # Methods for CoreAI integration

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom event based on provided data.

        Args:
            event_data: Custom event data

        Returns:
            Created event information
        """
        try:
            # Ensure required fields
            required_fields = ["type", "name", "description", "duration"]
            for field in required_fields:
                if field not in event_data:
                    return {
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }

            # Process based on event type
            event_type = event_data["type"]

            if event_type == "natural_disaster":
                # Additional required fields for natural disasters
                additional_fields = ["disaster_type", "severity", "affected_area"]
                for field in additional_fields:
                    if field not in event_data:
                        return {
                            "status": "error",
                            "message": f"Missing required field for natural disaster: {field}"
                        }

                # Create natural disaster event
                event = {
                    "id": f"disaster_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "natural_disaster",
                    "disaster_type": event_data["disaster_type"],
                    "name": event_data["name"],
                    "description": event_data["description"],
                    "severity": event_data["severity"],
                    "affected_area": event_data["affected_area"],
                    "start_time": time.time(),
                    "duration": event_data["duration"],
                    "status": "active",
                    "effects": event_data.get("effects", {})
                }

            elif event_type == "political_event":
                # Create political event
                event = {
                    "id": f"political_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "political_event",
                    "political_type": event_data.get("political_type", "custom"),
                    "name": event_data["name"],
                    "description": event_data["description"],
                    "start_time": time.time(),
                    "duration": event_data["duration"],
                    "status": "active",
                    "effects": event_data.get("effects", {})
                }

                # Add type-specific fields
                if "political_type" in event_data:
                    if event_data["political_type"] == "war":
                        if "involved_states" in event_data:
                            event["involved_states"] = event_data["involved_states"]
                        else:
                            return {
                                "status": "error",
                                "message": "Missing involved_states for war event"
                            }
                    elif event_data["political_type"] == "rebellion":
                        if "involved_state" in event_data and "location" in event_data:
                            event["involved_state"] = event_data["involved_state"]
                            event["location"] = event_data["location"]
                        else:
                            return {
                                "status": "error",
                                "message": "Missing involved_state or location for rebellion event"
                            }

            elif event_type == "cultural_event":
                # Create cultural event
                event = {
                    "id": f"cultural_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "cultural_event",
                    "cultural_type": event_data.get("cultural_type", "custom"),
                    "name": event_data["name"],
                    "description": event_data["description"],
                    "start_time": time.time(),
                    "duration": event_data["duration"],
                    "status": "active",
                    "effects": event_data.get("effects", {})
                }

                # Add type-specific fields
                if "cultural_type" in event_data:
                    if event_data["cultural_type"] == "festival":
                        if "location" in event_data:
                            event["location"] = event_data["location"]
                        else:
                            return {
                                "status": "error",
                                "message": "Missing location for festival event"
                            }
                    elif event_data["cultural_type"] == "migration":
                        if "source" in event_data and "destination" in event_data:
                            event["source"] = event_data["source"]
                            event["destination"] = event_data["destination"]
                        else:
                            return {
                                "status": "error",
                                "message": "Missing source or destination for migration event"
                            }

            else:
                # Custom event type
                event = {
                    "id": f"custom_{int(time.time())}_{random.randint(1000, 9999)}",
                    "type": "custom",
                    "custom_type": event_type,
                    "name": event_data["name"],
                    "description": event_data["description"],
                    "start_time": time.time(),
                    "duration": event_data["duration"],
                    "status": "active",
                    "custom_data": event_data.get("custom_data", {})
                }

            # Add event to active events
            self.active_events.append(event)

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Save state
            self.save_state()

            # Log event creation
            logger.info(f"Created custom event: {event['name']} (Type: {event_type})")

            return {
                "status": "success",
                "message": f"Event '{event['name']}' created successfully",
                "event": event
            }

        except Exception as e:
            logger.error(f"Error creating custom event: {e}")
            return {
                "status": "error",
                "message": f"Error creating event: {str(e)}"
            }

    def end_event(self, event_id: str, outcome: Optional[str] = None) -> Dict[str, Any]:
        """
        End an active event early.

        Args:
            event_id: ID of the event to end
            outcome: Optional custom outcome

        Returns:
            Result of ending the event
        """
        try:
            # Find event
            event = None
            for e in self.active_events:
                if e.get("id") == event_id:
                    event = e
                    break

            if not event:
                return {
                    "status": "error",
                    "message": f"Event with ID {event_id} not found"
                }

            # Process event end effects
            event_copy = event.copy()
            self._process_event_end(event)

            # Add custom outcome if provided
            if outcome:
                event_copy["outcome"] = outcome

            # Update event status and end time
            event_copy["status"] = "completed"
            event_copy["end_time"] = time.time()

            # Remove from active events
            self.active_events.remove(event)

            # Add to history
            self.event_history.append(event_copy)

            # Save state
            self.save_state()

            # Log event end
            logger.info(f"Ended event: {event_copy['name']} (ID: {event_id})")

            return {
                "status": "success",
                "message": f"Event '{event_copy['name']}' ended successfully",
                "event": event_copy
            }

        except Exception as e:
            logger.error(f"Error ending event: {e}")
            return {
                "status": "error",
                "message": f"Error ending event: {str(e)}"
            }

    def get_active_events(self, event_type: Optional[str] = None, location_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all active events, optionally filtered by type or location.

        Args:
            event_type: Optional event type to filter by
            location_id: Optional location ID to filter by

        Returns:
            Dictionary with active events
        """
        # Filter events
        filtered_events = self.active_events

        if event_type:
            filtered_events = [e for e in filtered_events if e.get("type") == event_type]

        if location_id:
            # This is a simplified location check
            location_events = []
            for event in filtered_events:
                # Check if event has location data
                if "location" in event and event["location"].get("id") == location_id:
                    location_events.append(event)
                # Check if event has affected area that includes this location
                elif "affected_area" in event:
                    # Very simplified check - would need to be more sophisticated in practice
                    area = event["affected_area"]
                    if area.get("center", {}).get("id") == location_id:
                        location_events.append(event)

            filtered_events = location_events

        return {
            "status": "success",
            "count": len(filtered_events),
            "events": filtered_events
        }

    def get_event_history(self, limit: int = 10, offset: int = 0,
                          event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical events, with pagination and filtering.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            event_type: Optional event type to filter by

        Returns:
            Dictionary with historical events
        """
        # Filter events
        filtered_events = self.event_history

        if event_type:
            filtered_events = [e for e in filtered_events if e.get("type") == event_type]

        # Sort by end time (most recent first)
        sorted_events = sorted(filtered_events, key=lambda e: e.get("end_time", 0), reverse=True)

        # Apply pagination
        paginated_events = sorted_events[offset:offset + limit]

        return {
            "status": "success",
            "total": len(filtered_events),
            "limit": limit,
            "offset": offset,
            "events": paginated_events
        }

    def get_world_time(self) -> Dict[str, Any]:
        """
        Get the current world time.

        Returns:
            Dictionary with world time information
        """
        return {
            "status": "success",
            "time": self.world_time
        }

        def set_world_time(self, year: Optional[int] = None, month: Optional[int] = None,
                           day: Optional[int] = None) -> Dict[str, Any]:
            """
            Set the current world time.

            Args:
                year: Optional year to set
                month: Optional month to set (1-12)
                day: Optional day to set (1-31)

            Returns:
                Dictionary with updated world time information
            """
            try:
                # Get current values
                current_year = self.world_time["year"]
                current_month = self.world_time["month"]
                current_day = self.world_time["day"]

                # Update values if provided
                if year is not None:
                    current_year = year

                if month is not None:
                    if 1 <= month <= 12:
                        current_month = month
                    else:
                        return {
                            "status": "error",
                            "message": "Month must be between 1 and 12"
                        }

                if day is not None:
                    # Basic validation - doesn't account for different month lengths
                    if 1 <= day <= 31:
                        current_day = day
                    else:
                        return {
                            "status": "error",
                            "message": "Day must be between 1 and 31"
                        }

                # Create a valid date
                try:
                    # This will raise ValueError for invalid dates (e.g., February 30)
                    new_date = datetime(year=current_year, month=current_month, day=current_day)

                    # Update world time
                    self.world_time["year"] = new_date.year
                    self.world_time["month"] = new_date.month
                    self.world_time["day"] = new_date.day

                    # Update season
                    self._update_season()

                    return {
                        "status": "success",
                        "message": "World time updated successfully",
                        "time": self.world_time
                    }

                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Invalid date: {str(e)}"
                    }

            except Exception as e:
                logger.error(f"Error setting world time: {e}")
                return {
                    "status": "error",
                    "message": f"Error setting world time: {str(e)}"
                }

        def get_events_by_location(self, location_id: int, include_history: bool = False) -> Dict[str, Any]:
            """
            Get events affecting a specific location.

            Args:
                location_id: ID of the location
                include_history: Whether to include historical events

            Returns:
                Dictionary with events affecting the location
            """
            location_events = []

            # Check active events
            for event in self.active_events:
                # Check if event directly references this location
                if "location" in event and event["location"].get("id") == location_id:
                    location_events.append(event)
                    continue

                # Check if location is within an affected area
                if "affected_area" in event:
                    area = event["affected_area"]
                    center = area.get("center", {})
                    if center.get("id") == location_id:
                        location_events.append(event)
                        continue

                    # Simple radius check (would need to be more sophisticated in practice)
                    if "radius" in area and "x" in center and "y" in center:
                        # Get location coordinates
                        loc_x, loc_y = self._get_location_coordinates(location_id)
                        if loc_x is not None and loc_y is not None:
                            # Calculate distance
                            dx = center.get("x", 0) - loc_x
                            dy = center.get("y", 0) - loc_y
                            distance = (dx * dx + dy * dy) ** 0.5

                            # Check if within radius
                            if distance <= area["radius"]:
                                location_events.append(event)

                # Check for state-wide political events
                if event.get("type") == "political_event":
                    if "involved_states" in event:
                        # Get location's state
                        state_id = self._get_location_state(location_id)
                        if state_id is not None:
                            # Check if state is involved
                            for state in event["involved_states"]:
                                if state.get("id") == state_id:
                                    location_events.append(event)
                                    break

                    elif "involved_state" in event and isinstance(event["involved_state"], dict):
                        # Get location's state
                        state_id = self._get_location_state(location_id)
                        if state_id is not None and event["involved_state"].get("id") == state_id:
                            location_events.append(event)

            # Check historical events if requested
            if include_history:
                for event in self.event_history:
                    # Perform the same checks as for active events

                    # Check if event directly references this location
                    if "location" in event and event["location"].get("id") == location_id:
                        location_events.append(event)
                        continue

                    # Add the same checks as above for affected areas and political events
                    # (Code omitted for brevity - would be identical to the active events checks)

            return {
                "status": "success",
                "location_id": location_id,
                "count": len(location_events),
                "events": location_events
            }

        def _get_location_coordinates(self, location_id: int) -> Tuple[Optional[float], Optional[float]]:
            """
            Get the coordinates of a location.

            Args:
                location_id: ID of the location

            Returns:
                Tuple of (x, y) coordinates or (None, None) if not found
            """
            # Check burgs
            for burg in self.map_data.get("burgs", []):
                if burg.get("i") == location_id:
                    return burg.get("x", 0), burg.get("y", 0)

            # Check cells
            for cell in self.map_data.get("cells", []):
                if cell.get("i") == location_id:
                    if "p" in cell and len(cell["p"]) >= 2:
                        return cell["p"][0], cell["p"][1]

            return None, None

        def _get_location_state(self, location_id: int) -> Optional[int]:
            """
            Get the state ID of a location.

            Args:
                location_id: ID of the location

            Returns:
                State ID or None if not found
            """
            # Check burgs
            for burg in self.map_data.get("burgs", []):
                if burg.get("i") == location_id:
                    return burg.get("state")

            # Check cells
            for cell in self.map_data.get("cells", []):
                if cell.get("i") == location_id:
                    province_id = cell.get("province")
                    if province_id is not None:
                        # Find the province
                        for province in self.map_data.get("provinces", []):
                            if province.get("i") == province_id:
                                return province.get("state")

            return None

        def simulate_natural_disaster(self, location_id: int, disaster_type: str, severity: str) -> Dict[str, Any]:
            """
            Simulate a natural disaster at a specific location.

            Args:
                location_id: ID of the location for the disaster
                disaster_type: Type of disaster (earthquake, flood, drought, etc.)
                severity: Severity level (minor, moderate, major, catastrophic)

            Returns:
                Dictionary with disaster simulation results
            """
            # Get disaster templates
            if "natural_disaster" not in self.event_templates or not self.event_templates["natural_disaster"]["types"]:
                return {
                    "status": "error",
                    "message": "No natural disaster templates available"
                }

            # Find the requested disaster type
            disaster_template = None
            for dt in self.event_templates["natural_disaster"]["types"]:
                if dt["id"] == disaster_type:
                    disaster_template = dt
                    break

            if not disaster_template:
                return {
                    "status": "error",
                    "message": f"Unknown disaster type: {disaster_type}"
                }

            # Find the requested severity level
            severity_level = None
            for sl in disaster_template["severity_levels"]:
                if sl["name"] == severity:
                    severity_level = sl
                    break

            if not severity_level:
                return {
                    "status": "error",
                    "message": f"Unknown severity level: {severity}"
                }

            # Get location data
            location = None
            for burg in self.map_data.get("burgs", []):
                if burg.get("i") == location_id:
                    location = {
                        "id": burg.get("i"),
                        "name": burg.get("name", f"Burg {burg.get('i')}"),
                        "x": burg.get("x", 0),
                        "y": burg.get("y", 0),
                        "type": "burg"
                    }
                    break

            if not location:
                for cell in self.map_data.get("cells", []):
                    if cell.get("i") == location_id:
                        # Create location from cell
                        if "p" in cell:
                            x, y = cell["p"]
                        else:
                            x, y = 0, 0

                        location = {
                            "id": cell.get("i"),
                            "x": x,
                            "y": y,
                            "type": "cell"
                        }

                        # Add name if available
                        if "featureName" in cell:
                            location["name"] = cell["featureName"]
                        else:
                            location["name"] = f"Location {cell.get('i')}"

                        break

            if not location:
                return {
                    "status": "error",
                    "message": f"Location with ID {location_id} not found"
                }

            # Calculate radius based on severity
            base_radius = disaster_template.get("radius", [20, 100])
            radius = base_radius[0] + (base_radius[1] - base_radius[0]) * severity_level["damage_factor"]

            # Create affected area
            affected_area = {
                "center": location,
                "radius": radius,
                "type": "circle"
            }

            # Create disaster event
            event = {
                "id": f"disaster_{int(time.time())}_{random.randint(1000, 9999)}",
                "type": "natural_disaster",
                "disaster_type": disaster_type,
                "name": f"{disaster_template['name']} at {location.get('name', 'Unknown Location')}",
                "description": f"{severity.capitalize()} {disaster_template['description']} centered on {location.get('name', 'Unknown Location')}",
                "severity": severity_level,
                "affected_area": affected_area,
                "start_time": time.time(),
                "duration": severity_level.get("recovery_time", 30),  # Duration based on recovery time
                "status": "active",
                "effects": disaster_template["effects"]
            }

            # Add event to active events
            self.active_events.append(event)

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Save state
            self.save_state()

            # Log event creation
            logger.info(f"Simulated natural disaster: {event['name']} (Severity: {severity})")

            return {
                "status": "success",
                "message": f"{severity.capitalize()} {disaster_type} simulated successfully",
                "event": event
            }

        def simulate_war(self, state1_id: int, state2_id: int, severity: str = "limited_war") -> Dict[str, Any]:
            """
            Simulate a war between two states.

            Args:
                state1_id: ID of the first state (attacker)
                state2_id: ID of the second state (defender)
                severity: War severity level

            Returns:
                Dictionary with war simulation results
            """
            # Get valid states
            states = self._get_valid_states()

            # Find the states
            state1 = None
            state2 = None

            for state in states:
                if state.get("i") == state1_id:
                    state1 = state
                elif state.get("i") == state2_id:
                    state2 = state

            if not state1:
                return {
                    "status": "error",
                    "message": f"State with ID {state1_id} not found"
                }

            if not state2:
                return {
                    "status": "error",
                    "message": f"State with ID {state2_id} not found"
                }

            # Get war template
            if "political_event" not in self.event_templates or not self.event_templates["political_event"]["types"]:
                return {
                    "status": "error",
                    "message": "No political event templates available"
                }

            war_template = None
            for et in self.event_templates["political_event"]["types"]:
                if et["id"] == "war":
                    war_template = et
                    break

            if not war_template:
                return {
                    "status": "error",
                    "message": "War template not found"
                }

            # Find the requested severity level
            severity_level = None
            for sl in war_template["severity_levels"]:
                if sl["name"] == severity:
                    severity_level = sl
                    break

            if not severity_level:
                return {
                    "status": "error",
                    "message": f"Unknown severity level: {severity}"
                }

            # Calculate duration based on severity
            min_duration, max_duration = war_template.get("duration", [90, 365])
            base_duration = min_duration + (max_duration - min_duration) * severity_level["damage_factor"]
            duration = int(base_duration * random.uniform(0.8, 1.2))  # Add some randomness

            # Determine initial advantage
            advantage_factor = random.uniform(-0.3, 0.3)  # Small initial advantage

            # Create war event
            event = {
                "id": f"war_{int(time.time())}_{random.randint(1000, 9999)}",
                "type": "political_event",
                "political_type": "war",
                "name": f"War between {state1['name']} and {state2['name']}",
                "description": f"{severity.replace('_', ' ').capitalize()} between {state1['name']} and {state2['name']}",
                "involved_states": [
                    {"id": state1["i"], "name": state1["name"], "role": "attacker"},
                    {"id": state2["i"], "name": state2["name"], "role": "defender"}
                ],
                "severity": severity_level,
                "start_time": time.time(),
                "duration": duration,
                "advantage_factor": advantage_factor,
                "war_progress": 0,  # 0 is neutral, positive means attacker winning
                "status": "active",
                "possible_outcomes": war_template["possible_outcomes"],
                "effects": war_template["effects"]
            }

            # Add event to active events
            self.active_events.append(event)

            # Apply event to world state if available
            if self.world_state:
                self.world_state.apply_event(event)

            # Save state
            self.save_state()

            # Log event creation
            logger.info(f"Simulated war: {event['name']} (Severity: {severity})")

            return {
                "status": "success",
                "message": f"War between {state1['name']} and {state2['name']} simulated successfully",
                "event": event
            }

    # Debugging function (optional)
    def test_map_event_system():
        """
        Test function for the MapEventSystem.
        """
        # Initialize engine with default paths
        engine = MapEventSystem()

        # Print basic info
        print(f"Current world time: {engine.world_time}")
        print(f"Active events: {len(engine.active_events)}")
        print(f"Historical events: {len(engine.event_history)}")

        # Test advancing time
        print("\nAdvancing time by 30 days...")
        result = engine.advance_time(30)
        print(f"New date: {result['new_date']}")
        print(f"New events: {len(result['new_events'])}")

        # Test generating a natural disaster
        print("\nGenerating a natural disaster...")
        disaster = engine._generate_natural_disaster()
        if disaster:
            print(f"Generated disaster: {disaster['name']}")

        # Test getting active events
        print("\nActive events:")
        events = engine.get_active_events()
        for event in events['events']:
            print(f"- {event['name']} (Type: {event['type']})")

    if __name__ == "__main__":
        test_map_event_system()