"""
MapPoliticalManager.py
Part of the D&D5e MapAI system
Manages political entities, borders, and relations within the game world.

Based on the structure from Azgaar's Fantasy Map Generator
"""

import json
import os
import random
from enum import Enum
from typing import Dict, List, Tuple, Set, Optional, Union, Any

# Import from other MapAI components
from MapWorldState import MapWorldState
from MapRegionManager import MapRegionManager


class PoliticalFormType(Enum):
    """Political form types based on Azgaar's Fantasy Map Generator"""
    MONARCHY = "Monarchy"
    REPUBLIC = "Republic"
    THEOCRACY = "Theocracy"
    UNION = "Union"
    ANARCHY = "Anarchy"
    OLIGARCHY = "Oligarchy"
    CONFEDERATION = "Confederation"
    PRINCIPALITY = "Principality"
    DUCHY = "Duchy"
    TRIBAL = "Tribal"


class RelationType(Enum):
    """Types of relations between political entities"""
    ALLIANCE = "Alliance"
    PEACE = "Peace"
    NEUTRAL = "Neutral"
    TENSION = "Tension"
    CONFLICT = "Conflict"
    WAR = "War"
    VASSAL = "Vassal"
    SUZERAIN = "Suzerain"
    TRUCE = "Truce"


class BorderType(Enum):
    """Types of borders between political entities"""
    NATURAL = "Natural"  # River, mountain, etc.
    ARTIFICIAL = "Artificial"  # Man-made
    CONTESTED = "Contested"  # Disputed
    OPEN = "Open"  # No physical barrier


class PoliticalEntity:
    """Represents a political entity (state, nation, etc.) in the game world"""
    
    def __init__(self, 
                 entity_id: int, 
                 name: str, 
                 form_type: PoliticalFormType = PoliticalFormType.MONARCHY,
                 color: str = "#000000",
                 center_cell_id: int = 0,
                 capital_id: int = 0,
                 culture_id: int = 0,
                 expansionism: float = 1.0):
        """
        Initialize a political entity
        
        Args:
            entity_id: Unique identifier
            name: Name of the political entity
            form_type: Type of government
            color: Hex color code for maps
            center_cell_id: Cell ID of the entity's center
            capital_id: ID of the capital city/location
            culture_id: ID of the dominant culture
            expansionism: Growth rate multiplier
        """
        self.id = entity_id
        self.name = name
        self.form_type = form_type
        self.color = color
        self.center_cell_id = center_cell_id
        self.capital_id = capital_id
        self.culture_id = culture_id
        self.expansionism = expansionism
        
        # Additional properties
        self.form_name = self._get_form_name()
        self.full_name = f"{self.name} {self.form_name}"
        
        # Territories and regions
        self.territory_cells: Set[int] = set()  # Set of cell IDs that belong to this entity
        self.core_provinces: List[int] = []  # Core/heartland provinces
        self.frontier_provinces: List[int] = []  # Border/frontier provinces
        self.disconnected_territories: List[Set[int]] = []  # Exclaves/colonies
        
        # Relations with other entities
        self.relations: Dict[int, RelationType] = {}  # Entity ID to relation type
        
        # Historical data
        self.foundation_date: int = 0  # When this entity was founded (game time)
        self.historical_events: List[Dict[str, Any]] = []  # Major events in history
        self.previous_territories: Dict[int, Set[int]] = {}  # Territory at different time periods
        
        # Additional game-specific properties
        self.military_strength: float = 1.0
        self.economic_power: float = 1.0
        self.stability: float = 1.0
        self.is_active: bool = True  # Whether this entity still exists
    
    def _get_form_name(self) -> str:
        """Return the formal name based on the form type"""
        form_names = {
            PoliticalFormType.MONARCHY: "Kingdom",
            PoliticalFormType.REPUBLIC: "Republic",
            PoliticalFormType.THEOCRACY: "Holy State",
            PoliticalFormType.UNION: "Union",
            PoliticalFormType.ANARCHY: "Anarchic Lands",
            PoliticalFormType.OLIGARCHY: "Oligarchy",
            PoliticalFormType.CONFEDERATION: "Confederation",
            PoliticalFormType.PRINCIPALITY: "Principality",
            PoliticalFormType.DUCHY: "Duchy",
            PoliticalFormType.TRIBAL: "Tribal Federation"
        }
        return form_names.get(self.form_type, "State")
    
    def set_relation(self, other_entity_id: int, relation: RelationType) -> None:
        """Set relation with another political entity"""
        self.relations[other_entity_id] = relation
    
    def add_territory(self, cell_ids: Union[int, List[int], Set[int]]) -> None:
        """Add territory cells to this entity"""
        if isinstance(cell_ids, int):
            self.territory_cells.add(cell_ids)
        else:
            self.territory_cells.update(cell_ids)
    
    def remove_territory(self, cell_ids: Union[int, List[int], Set[int]]) -> None:
        """Remove territory cells from this entity"""
        if isinstance(cell_ids, int):
            self.territory_cells.discard(cell_ids)
        else:
            self.territory_cells.difference_update(cell_ids)
    
    def calculate_borders(self, region_manager) -> Dict[int, Set[int]]:
        """
        Calculate border cells with other political entities
        
        Returns:
            Dict mapping entity IDs to set of shared border cell IDs
        """
        # Implementation would use region_manager to find bordering cells
        # between this entity's territory and others
        # This is a placeholder for the actual implementation
        return {}
    
    def calculate_disconnected_territories(self, region_manager) -> List[Set[int]]:
        """
        Identify disconnected territories (exclaves)
        
        Returns:
            List of sets containing cell IDs for each disconnected territory
        """
        # Implementation would use region_manager to find disconnected regions
        # This is a placeholder for the actual implementation
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to a dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "form_type": self.form_type.value,
            "form_name": self.form_name,
            "full_name": self.full_name,
            "color": self.color,
            "center_cell_id": self.center_cell_id,
            "capital_id": self.capital_id,
            "culture_id": self.culture_id,
            "expansionism": self.expansionism,
            "territory_cells": list(self.territory_cells),
            "core_provinces": self.core_provinces,
            "frontier_provinces": self.frontier_provinces,
            "relations": {str(k): v.value for k, v in self.relations.items()},
            "military_strength": self.military_strength,
            "economic_power": self.economic_power,
            "stability": self.stability,
            "is_active": self.is_active,
            "foundation_date": self.foundation_date,
            "historical_events": self.historical_events,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoliticalEntity':
        """Create a PoliticalEntity from a dictionary"""
        entity = cls(
            entity_id=data["id"],
            name=data["name"],
            form_type=PoliticalFormType(data["form_type"]),
            color=data["color"],
            center_cell_id=data["center_cell_id"],
            capital_id=data["capital_id"],
            culture_id=data["culture_id"],
            expansionism=data["expansionism"]
        )
        
        # Restore additional properties
        entity.territory_cells = set(data["territory_cells"])
        entity.core_provinces = data["core_provinces"]
        entity.frontier_provinces = data["frontier_provinces"]
        entity.relations = {int(k): RelationType(v) for k, v in data["relations"].items()}
        entity.military_strength = data.get("military_strength", 1.0)
        entity.economic_power = data.get("economic_power", 1.0)
        entity.stability = data.get("stability", 1.0)
        entity.is_active = data.get("is_active", True)
        entity.foundation_date = data.get("foundation_date", 0)
        entity.historical_events = data.get("historical_events", [])
        
        return entity


class Border:
    """Represents a border between two political entities"""
    
    def __init__(self, 
                 entity1_id: int, 
                 entity2_id: int, 
                 cells: Set[int], 
                 border_type: BorderType = BorderType.ARTIFICIAL):
        """
        Initialize a border between two entities
        
        Args:
            entity1_id: ID of first entity
            entity2_id: ID of second entity
            cells: Set of cell IDs that form the border
            border_type: Type of border
        """
        self.entity1_id = entity1_id
        self.entity2_id = entity2_id
        self.cells = cells
        self.border_type = border_type
        self.length = len(cells)
        self.is_contested = border_type == BorderType.CONTESTED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert border to dictionary for serialization"""
        return {
            "entity1_id": self.entity1_id,
            "entity2_id": self.entity2_id,
            "cells": list(self.cells),
            "border_type": self.border_type.value,
            "length": self.length,
            "is_contested": self.is_contested
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Border':
        """Create a Border from a dictionary"""
        return cls(
            entity1_id=data["entity1_id"],
            entity2_id=data["entity2_id"],
            cells=set(data["cells"]),
            border_type=BorderType(data["border_type"])
        )


class TerritorialDispute:
    """Represents a territorial dispute between political entities"""
    
    def __init__(self, 
                 disputed_cells: Set[int], 
                 claimant_ids: List[int], 
                 current_controller_id: int,
                 start_date: int,
                 intensity: float = 0.5):
        """
        Initialize a territorial dispute
        
        Args:
            disputed_cells: Set of disputed cell IDs
            claimant_ids: IDs of entities claiming the territory
            current_controller_id: ID of entity currently controlling the territory
            start_date: When the dispute started (game time)
            intensity: How intense the dispute is (0.0-1.0)
        """
        self.disputed_cells = disputed_cells
        self.claimant_ids = claimant_ids
        self.current_controller_id = current_controller_id
        self.start_date = start_date
        self.intensity = intensity
        self.resolved = False
        self.resolution_date = 0
        self.resolution_winner_id = 0
    
    def resolve(self, winner_id: int, resolution_date: int) -> None:
        """Resolve the dispute in favor of a particular entity"""
        self.resolved = True
        self.resolution_date = resolution_date
        self.resolution_winner_id = winner_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dispute to dictionary for serialization"""
        return {
            "disputed_cells": list(self.disputed_cells),
            "claimant_ids": self.claimant_ids,
            "current_controller_id": self.current_controller_id,
            "start_date": self.start_date,
            "intensity": self.intensity,
            "resolved": self.resolved,
            "resolution_date": self.resolution_date,
            "resolution_winner_id": self.resolution_winner_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerritorialDispute':
        """Create a TerritorialDispute from a dictionary"""
        dispute = cls(
            disputed_cells=set(data["disputed_cells"]),
            claimant_ids=data["claimant_ids"],
            current_controller_id=data["current_controller_id"],
            start_date=data["start_date"],
            intensity=data["intensity"]
        )
        dispute.resolved = data["resolved"]
        dispute.resolution_date = data["resolution_date"]
        dispute.resolution_winner_id = data["resolution_winner_id"]
        return dispute


class MapPoliticalManager:
    """Manages political entities, borders, and relations within the game world"""
    
    def __init__(self, world_state: MapWorldState, region_manager: MapRegionManager):
        """
        Initialize the political manager
        
        Args:
            world_state: Reference to the world state
            region_manager: Reference to the region manager
        """
        self.world_state = world_state
        self.region_manager = region_manager
        
        # Political entities storage
        self.entities: Dict[int, PoliticalEntity] = {}
        self.next_entity_id = 1
        
        # Borders between entities
        self.borders: List[Border] = []
        
        # Territorial disputes
        self.disputes: List[TerritorialDispute] = []
        
        # Neutral territories (not claimed by any entity)
        self.neutral_territories: Set[int] = set()
        
        # Historical data
        self.historical_entities: Dict[int, PoliticalEntity] = {}  # Defunct entities
        self.political_events: List[Dict[str, Any]] = []  # Major political events
    
    def create_entity(self, 
                      name: str, 
                      form_type: PoliticalFormType = PoliticalFormType.MONARCHY,
                      color: str = None,
                      center_cell_id: int = 0,
                      capital_id: int = 0,
                      culture_id: int = 0,
                      expansionism: float = 1.0) -> PoliticalEntity:
        """
        Create a new political entity
        
        Args:
            name: Name of the political entity
            form_type: Type of government
            color: Hex color code for maps (random if None)
            center_cell_id: Cell ID of the entity's center
            capital_id: ID of the capital city/location
            culture_id: ID of the dominant culture
            expansionism: Growth rate multiplier
            
        Returns:
            The created PoliticalEntity
        """
        # Generate a random color if none provided
        if color is None:
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        
        entity = PoliticalEntity(
            entity_id=self.next_entity_id,
            name=name,
            form_type=form_type,
            color=color,
            center_cell_id=center_cell_id,
            capital_id=capital_id,
            culture_id=culture_id,
            expansionism=expansionism
        )
        
        self.entities[entity.id] = entity
        self.next_entity_id += 1
        
        # Mark entity foundation date and add to world history
        entity.foundation_date = self.world_state.current_date
        self.add_political_event(
            event_type="entity_founded",
            entity_id=entity.id,
            description=f"{entity.full_name} was founded"
        )
        
        return entity
    
    def remove_entity(self, entity_id: int, reason: str = "dissolved") -> bool:
        """
        Remove a political entity
        
        Args:
            entity_id: ID of the entity to remove
            reason: Reason for removal (dissolved, conquered, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # Move territories to neutral
        self.neutral_territories.update(entity.territory_cells)
        
        # Record historical event
        self.add_political_event(
            event_type="entity_removed",
            entity_id=entity_id,
            description=f"{entity.full_name} was {reason}"
        )
        
        # Move to historical entities
        entity.is_active = False
        self.historical_entities[entity_id] = entity
        del self.entities[entity_id]
        
        # Update borders
        self._update_borders_after_entity_change(entity_id)
        
        return True
    
    def merge_entities(self, entity1_id: int, entity2_id: int, 
                      new_name: str = None, new_form_type: PoliticalFormType = None) -> Optional[PoliticalEntity]:
        """
        Merge two political entities into one
        
        Args:
            entity1_id: ID of first entity (primary)
            entity2_id: ID of second entity (to be absorbed)
            new_name: Name for the merged entity (if None, keep first entity's name)
            new_form_type: Form type for merged entity (if None, keep first entity's form)
            
        Returns:
            The merged PoliticalEntity or None if failed
        """
        if entity1_id not in self.entities or entity2_id not in self.entities:
            return None
        
        entity1 = self.entities[entity1_id]
        entity2 = self.entities[entity2_id]
        
        # Keep the first entity and absorb the second
        entity1.add_territory(entity2.territory_cells)
        
        # Update name and form if specified
        if new_name:
            entity1.name = new_name
            entity1.full_name = f"{new_name} {entity1.form_name}"
        
        if new_form_type:
            entity1.form_type = new_form_type
            entity1.form_name = entity1._get_form_name()
            entity1.full_name = f"{entity1.name} {entity1.form_name}"
        
        # Record historical event
        self.add_political_event(
            event_type="entities_merged",
            entity_ids=[entity1_id, entity2_id],
            description=f"{entity2.full_name} was absorbed by {entity1.full_name}"
        )
        
        # Remove the second entity
        self.remove_entity(entity2_id, reason="merged")
        
        # Update borders
        self._update_borders_after_entity_change(entity2_id)
        
        return entity1
    
    def set_relation(self, entity1_id: int, entity2_id: int, 
                    relation: RelationType, bidirectional: bool = True) -> bool:
        """
        Set relation between two political entities
        
        Args:
            entity1_id: ID of first entity
            entity2_id: ID of second entity
            relation: Type of relation to set
            bidirectional: Whether to set the same relation for both entities
            
        Returns:
            True if successful, False otherwise
        """
        if entity1_id not in self.entities or entity2_id not in self.entities:
            return False
        
        entity1 = self.entities[entity1_id]
        entity2 = self.entities[entity2_id]
        
        # Set relation for first entity
        old_relation = entity1.relations.get(entity2_id, RelationType.NEUTRAL)
        entity1.set_relation(entity2_id, relation)
        
        # Record if relation changed
        if old_relation != relation:
            self.add_political_event(
                event_type="relation_changed",
                entity_ids=[entity1_id, entity2_id],
                description=f"Relation between {entity1.name} and {entity2.name} changed from {old_relation.value} to {relation.value}"
            )
        
        # Set bidirectional relation if requested
        if bidirectional:
            entity2.set_relation(entity1_id, relation)
        
        return True
    
    def expand_entity(self, entity_id: int, new_cells: Set[int]) -> bool:
        """
        Expand a political entity's territory
        
        Args:
            entity_id: ID of the entity to expand
            new_cells: Set of cell IDs to add to territory
            
        Returns:
            True if successful, False otherwise
        """
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # Check which cells are already claimed by other entities
        other_entities_cells = set()
        for other_id, other_entity in self.entities.items():
            if other_id != entity_id:
                other_entities_cells.update(other_entity.territory_cells)
        
        # Determine which cells are neutral vs. contested
        neutral_cells = new_cells.difference(other_entities_cells)
        contested_cells = new_cells.intersection(other_entities_cells)
        
        # Add neutral cells to entity territory
        entity.add_territory(neutral_cells)
        self.neutral_territories.difference_update(neutral_cells)
        
        # Create disputes for contested cells
        for cell in contested_cells:
            # Find which entities claim this cell
            claimants = [eid for eid, e in self.entities.items() 
                         if cell in e.territory_cells]
            
            # Create a dispute
            if claimants:
                dispute = TerritorialDispute(
                    disputed_cells={cell},
                    claimant_ids=claimants + [entity_id],
                    current_controller_id=claimants[0],  # Current controller
                    start_date=self.world_state.current_date
                )
                self.disputes.append(dispute)
        
        # Update borders
        self._calculate_all_borders()
        
        return True
    
    def create_dispute(self, disputed_cells: Set[int], claimant_ids: List[int],
                      current_controller_id: int, intensity: float = 0.5) -> TerritorialDispute:
        """
        Create a new territorial dispute
        
        Args:
            disputed_cells: Set of disputed cell IDs
            claimant_ids: IDs of entities claiming the territory
            current_controller_id: ID of entity currently controlling the territory
            intensity: How intense the dispute is (0.0-1.0)
            
        Returns:
            The created TerritorialDispute
        """
        dispute = TerritorialDispute(
            disputed_cells=disputed_cells,
            claimant_ids=claimant_ids,
            current_controller_id=current_controller_id,
            start_date=self.world_state.current_date,
            intensity=intensity
        )
        
        self.disputes.append(dispute)
        
        # Add a border for this disputed territory
        for i, entity1_id in enumerate(claimant_ids):
            for entity2_id in claimant_ids[i+1:]:
                border = Border(
                    entity1_id=entity1_id,
                    entity2_id=entity2_id,
                    cells=disputed_cells,
                    border_type=BorderType.CONTESTED
                )
                self.borders.append(border)
        
        # Record event
        entity_names = [self.entities[eid].name for eid in claimant_ids if eid in self.entities]
        self.add_political_event(
            event_type="dispute_started",
            entity_ids=claimant_ids,
            description=f"Territorial dispute started between {', '.join(entity_names)}"
        )
        
        return dispute
    
    def resolve_dispute(self, dispute_index: int, winner_id: int) -> bool:
        """
        Resolve a territorial dispute
        
        Args:
            dispute_index: Index of the dispute in the disputes list
            winner_id: ID of the entity that wins the dispute
            
        Returns:
            True if successful, False otherwise
        """
        if dispute_index >= len(self.disputes):
            return False
        
        dispute = self.disputes[dispute_index]
        
        if dispute.resolved:
            return False
        
        if winner_id not in dispute.claimant_ids:
            return False
        
        # Resolve the dispute
        dispute.resolve(winner_id, self.world_state.current_date)
        
        # Transfer territory to winner
        winner = self.entities.get(winner_id)
        if winner:
            # Remove these cells from all other entities
            for entity_id, entity in self.entities.items():
                if entity_id != winner_id:
                    entity.remove_territory(dispute.disputed_cells)
            
            # Add to winner's territory
            winner.add_territory(dispute.disputed_cells)
        
        # Update borders
        self._calculate_all_borders()
        
        # Record event
        winner_name = self.entities[winner_id].name if winner_id in self.entities else "Unknown"
        self.add_political_event(
            event_type="dispute_resolved",
            entity_ids=dispute.claimant_ids,
            winner_id=winner_id,
            description=f"Territorial dispute resolved in favor of {winner_name}"
        )
        
        return True
    
    def update_entity_form(self, entity_id: int, new_form: PoliticalFormType) -> bool:
        """
        Update the form of government for an entity
        
        Args:
            entity_id: ID of the entity
            new_form: New form of government
            
        Returns:
            True if successful, False otherwise
        """
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        old_form = entity.form_type
        
        # Update the form
        entity.form_type = new_form
        entity.form_name = entity._get_form_name()
        entity.full_name = f"{entity.name} {entity.form_name}"
        
        # Record event
        self.add_political_event(
            event_type="form_changed",
            entity_id=entity_id,
            description=f"{entity.name} changed from {old_form.value} to {new_form.value}"
        )
        
        return True
    
    def get_entities_by_culture(self, culture_id: int) -> List[PoliticalEntity]:
        """
        Get all political entities associated with a specific culture
        
        Args:
            culture_id: ID of the culture
            
        Returns:
            List of PoliticalEntity objects with the specified culture
        """
        return [entity for entity in self.entities.values() if entity.culture_id == culture_id]
    
    def get_political_entities_in_region(self, region_id: int) -> Dict[int, float]:
        """
        Get all political entities in a specific region and their influence
        
        Args:
            region_id: ID of the region
            
        Returns:
            Dictionary mapping entity IDs to their influence in the region (0.0-1.0)
        """
                    # Get cells in this region
            region_cells = self.region_manager.GetRegionCells(region_id)
            if not region_cells:
                return {}
            
            # Calculate influence for each entity in the region
            entity_influences = {}
            total_cells = len(region_cells)
            
            for entity_id, entity in self.entities.items():
                # Count how many cells in this region belong to this entity
                entity_cells = entity.territory_cells.intersection(region_cells)
                if entity_cells:
                    influence = len(entity_cells) / total_cells
                    entity_influences[entity_id] = influence
            
            return entity_influences
    
    def get_entity_at_position(self, x: float, y: float) -> Optional[PoliticalEntity]:
        """
        Get the political entity at a specific position
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The political entity at this position, or None if not found
        """
        # Convert position to cell ID using MapRegionManager
        cell_id = self.region_manager.GetCellIdFromPosition(x, y)
        if cell_id < 0:
            return None
        
        # Find entity that owns this cell
        for entity in self.entities.values():
            if cell_id in entity.territory_cells:
                return entity
        
        return None
    
    def get_political_map_color(self, x: float, y: float) -> str:
        """
        Get the color to use when drawing the political map at a specific position
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Hex color code (e.g., "#FF0000") or "neutral" if no entity controls this area
        """
        entity = self.get_entity_at_position(x, y)
        if entity:
            return entity.color
        return "#CCCCCC"  # Default gray for neutral territories
    
    def _calculate_all_borders(self) -> None:
        """
        Calculate all borders between political entities
        """
        self.borders.clear()
        
        # Keep track of which entity pairs we've already processed
        processed_pairs = set()
        
        # For each entity, check for borders with other entities
        for entity1_id, entity1 in self.entities.items():
            for entity2_id, entity2 in self.entities.items():
                # Skip if same entity or already processed this pair
                if entity1_id == entity2_id or (entity1_id, entity2_id) in processed_pairs or (entity2_id, entity1_id) in processed_pairs:
                    continue
                
                # Calculate border cells between these entities
                border_cells = self._calculate_border_between_entities(entity1, entity2)
                
                if border_cells:
                    # Determine border type
                    border_type = self._determine_border_type(border_cells)
                    
                    # Create border object
                    border = Border(
                        entity1_id=entity1_id,
                        entity2_id=entity2_id,
                        cells=border_cells,
                        border_type=border_type
                    )
                    
                    self.borders.append(border)
                
                # Mark this pair as processed
                processed_pairs.add((entity1_id, entity2_id))
    
    def _calculate_border_between_entities(self, entity1: PoliticalEntity, entity2: PoliticalEntity) -> Set[int]:
        """
        Calculate the border cells between two entities
        
        Args:
            entity1: First political entity
            entity2: Second political entity
            
        Returns:
            Set of cell IDs that form the border
        """
        border_cells = set()
        
        # For each cell in entity1, check if it's adjacent to any cell in entity2
        for cell1 in entity1.territory_cells:
            # Get neighboring cells
            neighbor_cells = self.region_manager.GetNeighboringCells(cell1)
            
            # Check if any neighbors belong to entity2
            for neighbor in neighbor_cells:
                if neighbor in entity2.territory_cells:
                    border_cells.add(cell1)
                    break
        
        return border_cells
    
    def _determine_border_type(self, border_cells: Set[int]) -> BorderType:
        """
        Determine the type of border based on terrain
        
        Args:
            border_cells: Set of cell IDs that form the border
            
        Returns:
            BorderType enum value
        """
        # Count terrain types along border
        terrain_counts = {}
        
        for cell_id in border_cells:
            terrain = self.region_manager.GetTerrainTypeForCell(cell_id)
            terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
        
        # If mostly water (river), it's a natural border
        water_terrains = ["river", "water", "sea"]
        water_count = sum(terrain_counts.get(t, 0) for t in water_terrains)
        
        if water_count > len(border_cells) * 0.5:
            return BorderType.NATURAL
        
        # If mostly mountains, it's a natural border
        mountain_terrains = ["mountain", "highland", "hill"]
        mountain_count = sum(terrain_counts.get(t, 0) for t in mountain_terrains)
        
        if mountain_count > len(border_cells) * 0.5:
            return BorderType.NATURAL
        
        # Default to artificial border
        return BorderType.ARTIFICIAL
    
    def _update_borders_after_entity_change(self, changed_entity_id: int) -> None:
        """
        Update borders after an entity is changed, merged, or removed
        
        Args:
            changed_entity_id: ID of the entity that changed
        """
        # Remove borders involving this entity
        self.borders = [b for b in self.borders if b.entity1_id != changed_entity_id and b.entity2_id != changed_entity_id]
        
        # Recalculate all borders
        self._calculate_all_borders()
    
    def add_political_event(self, event_type: str, description: str, entity_id: int = None, 
                           entity_ids: List[int] = None, winner_id: int = None, 
                           disputed_cells: Set[int] = None) -> None:
        """
        Add a political event to the world history
        
        Args:
            event_type: Type of event (e.g., "relation_changed", "entity_formed")
            description: Text description of the event
            entity_id: ID of the related entity (if applicable)
            entity_ids: List of related entity IDs (if applicable)
            winner_id: ID of the winning entity (if applicable)
            disputed_cells: Set of disputed cells (if applicable)
        """
        event = {
            "type": event_type,
            "description": description,
            "date": self.world_state.current_date,
            "entity_id": entity_id,
            "entity_ids": entity_ids,
            "winner_id": winner_id,
            "disputed_cells": list(disputed_cells) if disputed_cells else None
        }
        
        self.political_events.append(event)
        
        # Also add to world state events if available
        if hasattr(self.world_state, 'add_event'):
            self.world_state.add_event(event_type, description)
    
    def generate_random_political_entities(self, num_entities: int = 5) -> None:
        """
        Generate random political entities for testing or initialization
        
        Args:
            num_entities: Number of entities to generate
        """
        # Clear existing entities
        self.entities.clear()
        self.next_entity_id = 1
        
        # Get suitable locations for capitals
        suitable_locations = self.region_manager.FindSettlementLocations(num_entities)
        
        # Generate random name prefixes and suffixes
        name_prefixes = ["North", "South", "East", "West", "Great", "United", "Royal", "Imperial", "Free"]
        name_roots = ["land", "istan", "ia", "ium", "or", "aria", "onia", "istan", "heim"]
        name_suffixes = ["Kingdom", "Republic", "Empire", "Confederation", "State", "Nation", "Realm"]
        
        form_types = list(PoliticalFormType)
        
        # Generate entities
        for i in range(num_entities):
            # Generate a random name
            prefix = random.choice(name_prefixes)
            root = random.choice(name_roots)
            name = f"{prefix}{root.capitalize()}"
            
            # Generate a random color (ensuring it's visibly different from others)
            color = self._generate_distinct_color()
            
            # Get location for capital
            capital_pos = suitable_locations[i] if i < len(suitable_locations) else None
            capital_cell_id = -1
            
            if capital_pos is not None:
                capital_cell_id = self.region_manager.GetCellIdFromPosition(capital_pos.x, capital_pos.y)
            
            # Use region manager to determine culture ID based on location
            culture_id = 0  # Default
            if capital_cell_id >= 0:
                biome = self.region_manager.GetBiomeForCell(capital_cell_id)
                if biome is not None:
                    culture_id = hash(biome.Type) % 10  # Simple hash to get a culture ID
            
            # Create the entity
            form_type = random.choice(form_types)
            entity = self.create_entity(
                name=name,
                form_type=form_type,
                color=color,
                center_cell_id=capital_cell_id,
                culture_id=culture_id,
                expansionism=random.uniform(0.8, 1.2)
            )
            
            # Generate initial territory
            if capital_cell_id >= 0:
                # Start with capital cell
                entity.add_territory({capital_cell_id})
                
                # Expand outward based on expansionism
                self._expand_entity_territory(entity, int(30 * entity.expansionism))
        
        # Establish initial relations between entities
        self._initialize_relations_between_entities()
        
        # Calculate borders
        self._calculate_all_borders()
    
    def _generate_distinct_color(self) -> str:
        """
        Generate a color that is visibly distinct from existing entity colors
        
        Returns:
            Hex color code
        """
        def color_distance(color1, color2):
            # Convert hex to RGB
            r1 = int(color1[1:3], 16)
            g1 = int(color1[3:5], 16)
            b1 = int(color1[5:7], 16)
            
            r2 = int(color2[1:3], 16)
            g2 = int(color2[3:5], 16)
            b2 = int(color2[5:7], 16)
            
            # Calculate Euclidean distance
            return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
        
        existing_colors = [e.color for e in self.entities.values()]
        
        # Generate colors until we find one that's distinct enough
        min_distance = 100  # Minimum distance threshold
        
        for _ in range(100):  # Try up to 100 times
            # Generate a random color
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            
            # Check distance from existing colors
            if not existing_colors or all(color_distance(color, ec) > min_distance for ec in existing_colors):
                return color
        
        # If we couldn't find a distinct color, just return a random one
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    
    def _expand_entity_territory(self, entity: PoliticalEntity, num_cells: int) -> None:
        """
        Expand an entity's territory by adding neighboring cells
        
        Args:
            entity: The political entity to expand
            num_cells: Number of cells to add
        """
        added_cells = 0
        frontier = list(entity.territory_cells)
        
        while added_cells < num_cells and frontier:
            # Get a random cell from the frontier
            current_cell = random.choice(frontier)
            frontier.remove(current_cell)
            
            # Get neighboring cells
            neighbors = self.region_manager.GetNeighboringCells(current_cell)
            
            for neighbor in neighbors:
                # Skip if already in territory or in another entity's territory
                if neighbor in entity.territory_cells or self._cell_belongs_to_any_entity(neighbor, entity.id):
                    continue
                
                # Add cell to territory
                entity.add_territory({neighbor})
                added_cells += 1
                
                # Add to frontier for further expansion
                frontier.append(neighbor)
                
                if added_cells >= num_cells:
                    break
    
    def _cell_belongs_to_any_entity(self, cell_id: int, exclude_entity_id: int = None) -> bool:
        """
        Check if a cell belongs to any political entity
        
        Args:
            cell_id: The cell ID to check
            exclude_entity_id: Optional entity ID to exclude from check
            
        Returns:
            True if the cell belongs to any entity (except the excluded one), False otherwise
        """
        for entity_id, entity in self.entities.items():
            if exclude_entity_id is not None and entity_id == exclude_entity_id:
                continue
                
            if cell_id in entity.territory_cells:
                return True
                
        return False
    
    def _initialize_relations_between_entities(self) -> None:
        """
        Initialize relations between all political entities
        """
        # Get all entity IDs
        entity_ids = list(self.entities.keys())
        
        # For each pair of entities
        for i, entity1_id in enumerate(entity_ids):
            for entity2_id in entity_ids[i+1:]:
                # Determine relation type based on distance, borders, etc.
                relation = self._determine_initial_relation(entity1_id, entity2_id)
                
                # Set relation in both directions
                self.set_relation(entity1_id, entity2_id, relation)
    
    def _determine_initial_relation(self, entity1_id: int, entity2_id: int) -> RelationType:
        """
        Determine the initial relation between two entities
        
        Args:
            entity1_id: ID of the first entity
            entity2_id: ID of the second entity
            
        Returns:
            RelationType enum value
        """
        entity1 = self.entities[entity1_id]
        entity2 = self.entities[entity2_id]
        
        # Check if they share a border
        has_border = False
        for border in self.borders:
            if (border.entity1_id == entity1_id and border.entity2_id == entity2_id) or \
               (border.entity1_id == entity2_id and border.entity2_id == entity1_id):
                has_border = True
                break
        
        # Entities that share a border are more likely to have tensions
        if has_border:
            # 50% chance of neutral, 30% chance of tension, 10% chance of conflict, 10% chance of peace
            rand = random.random()
            if rand < 0.5:
                return RelationType.NEUTRAL
            elif rand < 0.8:
                return RelationType.TENSION
            elif rand < 0.9:
                return RelationType.CONFLICT
            else:
                return RelationType.PEACE
        else:
            # Distant entities are more likely to be neutral or at peace
            # 70% chance of neutral, 20% chance of peace, 10% chance of tension
            rand = random.random()
            if rand < 0.7:
                return RelationType.NEUTRAL
            elif rand < 0.9:
                return RelationType.PEACE
            else:
                return RelationType.TENSION
    
    def generate_border_conflicts(self, num_conflicts: int = 2) -> None:
        """
        Generate random border conflicts/disputes between entities
        
        Args:
            num_conflicts: Number of conflicts to generate
        """
        # Need at least 2 entities
        if len(self.entities) < 2:
            return
        
        # Get borders that aren't already contested
        available_borders = [b for b in self.borders if b.border_type != BorderType.CONTESTED]
        
        if not available_borders:
            return
        
        # Generate conflicts
        for _ in range(min(num_conflicts, len(available_borders))):
            # Pick a random border
            border = random.choice(available_borders)
            available_borders.remove(border)
            
            # Make it contested
            border.border_type = BorderType.CONTESTED
            border.is_contested = True
            
            # Create a territorial dispute
            dispute = TerritorialDispute(
                disputed_cells=border.cells,
                claimant_ids=[border.entity1_id, border.entity2_id],
                current_controller_id=border.entity1_id,  # Arbitrary choice
                start_date=self.world_state.current_date,
                intensity=random.uniform(0.3, 0.9)
            )
            
            self.disputes.append(dispute)
            
            # Update relations to TENSION or CONFLICT
            relation = RelationType.TENSION if random.random() < 0.7 else RelationType.CONFLICT
            self.set_relation(border.entity1_id, border.entity2_id, relation)
            
            # Record event
            entity1_name = self.entities[border.entity1_id].name
            entity2_name = self.entities[border.entity2_id].name
            self.add_political_event(
                event_type="border_dispute",
                description=f"Border dispute erupted between {entity1_name} and {entity2_name}",
                entity_ids=[border.entity1_id, border.entity2_id],
                disputed_cells=border.cells
            )
    
    def update(self) -> None:
        """
        Update the political state based on world state changes
        """
        # Process active disputes
        self._process_disputes()
        
        # Update entity relationships based on current state
        self._update_relationships()
        
        # Small chance for random political events
        if random.random() < 0.1:  # 10% chance
            self._generate_random_political_event()
    
    def _process_disputes(self) -> None:
        """
        Process active territorial disputes
        """
        for i, dispute in enumerate(self.disputes[:]):
            if dispute.resolved:
                continue
                
            # Small chance to resolve the dispute
            if random.random() < 0.05:  # 5% chance
                # Determine winner based on various factors
                entity1_id = dispute.claimant_ids[0]
                entity2_id = dispute.claimant_ids[1]
                
                entity1 = self.entities.get(entity1_id)
                entity2 = self.entities.get(entity2_id)
                
                if entity1 and entity2:
                    # Simple calculation based on military strength and stability
                    entity1_score = entity1.military_strength * entity1.stability
                    entity2_score = entity2.military_strength * entity2.stability
                    
                    # Add some randomness
                    entity1_score *= random.uniform(0.8, 1.2)
                    entity2_score *= random.uniform(0.8, 1.2)
                    
                    winner_id = entity1_id if entity1_score > entity2_score else entity2_id
                    
                    # Resolve the dispute
                    self.resolve_dispute(i, winner_id)
                else:
                    # If one entity no longer exists, the other wins by default
                    winner_id = entity2_id if not entity1 else entity1_id
                    self.resolve_dispute(i, winner_id)
    
    def _update_relationships(self) -> None:
        """
        Update relationships between entities based on current state
        """
        # For each pair of entities
        entity_ids = list(self.entities.keys())
        
        for i, entity1_id in enumerate(entity_ids):
            for entity2_id in entity_ids[i+1:]:
                # Small chance to change relationship
                if random.random() < 0.02:  # 2% chance
                    entity1 = self.entities[entity1_id]
                    entity2 = self.entities[entity2_id]
                    
                    current_relation = entity1.relations.get(entity2_id, RelationType.NEUTRAL)
                    
                    # Calculate new relation
                    new_relation = self._calculate_new_relation(entity1_id, entity2_id, current_relation)
                    
                    if new_relation != current_relation:
                        # Update relation
                        self.set_relation(entity1_id, entity2_id, new_relation)
    
    def _calculate_new_relation(self, entity1_id: int, entity2_id: int, 
                               current_relation: RelationType) -> RelationType:
        """
        Calculate a new relation between two entities
        
        Args:
            entity1_id: ID of the first entity
            entity2_id: ID of the second entity
            current_relation: Current relation between them
            
        Returns:
            New RelationType enum value
        """
        # Check for active disputes
        has_dispute = False
        for dispute in self.disputes:
            if not dispute.resolved and entity1_id in dispute.claimant_ids and entity2_id in dispute.claimant_ids:
                has_dispute = True
                break
        
        # If they have an active dispute, relations tend to worsen
        if has_dispute:
            if current_relation == RelationType.PEACE:
                return RelationType.NEUTRAL
            elif current_relation == RelationType.NEUTRAL:
                return RelationType.TENSION
            elif current_relation == RelationType.TENSION:
                return RelationType.CONFLICT
            elif current_relation == RelationType.CONFLICT:
                return RelationType.WAR if random.random() < 0.3 else RelationType.CONFLICT
            else:
                return current_relation
        
        # Without disputes, relations can improve
        if random.random() < 0.7:  # 70% chance to improve
            if current_relation == RelationType.WAR:
                return RelationType.CONFLICT
            elif current_relation == RelationType.CONFLICT:
                return RelationType.TENSION
            elif current_relation == RelationType.TENSION:
                return RelationType.NEUTRAL
            elif current_relation == RelationType.NEUTRAL:
                return RelationType.PEACE
            else:
                return current_relation
        
        return current_relation
    
    def _generate_random_political_event(self) -> None:
        """
        Generate a random political event
        """
        # Choose a random entity
        if not self.entities:
            return
            
        entity_id = random.choice(list(self.entities.keys()))
        entity = self.entities[entity_id]
        
        # Possible event types
        event_types = [
            "government_change", 
            "civil_unrest", 
            "stability_increase", 
            "expansion",
            "new_capital"
        ]
        
        event_type = random.choice(event_types)
        
        if event_type == "government_change":
            old_form = entity.form_type
            new_form = random.choice([f for f in PoliticalFormType if f != old_form])
            
            # Update entity form
            self.update_entity_form(entity_id, new_form)
            
            # Event description
            description = f"{entity.name} has changed from a {old_form.value} to a {new_form.value}"
            
        elif event_type == "civil_unrest":
            # Decrease stability
            entity.stability = max(0.1, entity.stability - random.uniform(0.1, 0.3))
            
            description = f"Civil unrest has decreased stability in {entity.name}"
            
        elif event_type == "stability_increase":
            # Increase stability
            entity.stability = min(1.0, entity.stability + random.uniform(0.1, 0.2))
            
            description = f"Stability has increased in {entity.name}"
            
        elif event_type == "expansion":
            # Add some territory
            if entity.territory_cells:
                frontier = list(entity.territory_cells)
                new_cells = set()
                
                for _ in range(5):  # Add up to 5 cells
                    if not frontier:
                        break
                        
                    cell = random.choice(frontier)
                    neighbors = self.region_manager.GetNeighboringCells(cell)
                    
                    for neighbor in neighbors:
                        if neighbor not in entity.territory_cells and not self._cell_belongs_to_any_entity(neighbor):
                            new_cells.add(neighbor)
                            break
                
                if new_cells:
                    entity.add_territory(new_cells)
                    self._update_borders_after_entity_change(entity_id)
                    
                    description = f"{entity.name} has expanded its territory"
                else:
                    description = f"{entity.name} attempted to expand but was blocked"
            else:
                description = f"{entity.name} could not expand its territory"
                
        elif event_type == "new_capital":
            # Find a new cell to be the capital
            if entity.territory_cells:
                new_capital = random.choice(list(entity.territory_cells))
                entity.center_cell_id = new_capital
                
                description = f"{entity.name} has moved its capital"
            else:
                description = f"{entity.name} could not move its capital"
        
        else:
            description = f"Political changes have occurred in {entity.name}"
        
        # Add the event
        self.add_political_event(
            event_type=event_type,
            description=description,
            entity_id=entity_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert manager state to a dictionary for serialization
        
        Returns:
            Dictionary representation of the manager state
        """
        return {
            "entities": {str(entity_id): entity.to_dict() for entity_id, entity in self.entities.items()},
            "historical_entities": {str(entity_id): entity.to_dict() for entity_id, entity in self.historical_entities.items()},
            "next_entity_id": self.next_entity_id,
            "borders": [border.to_dict() for border in self.borders],
            "disputes": [dispute.to_dict() for dispute in self.disputes],
            "neutral_territories": list(self.neutral_territories),
            "political_events": self.political_events
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], world_state, region_manager) -> 'MapPoliticalManager':
        """
        Create a MapPoliticalManager from a dictionary
        
        Args:
            data: Dictionary representation of the manager state
            world_state: Reference to the world state
            region_manager: Reference to the region manager
            
        Returns:
            New MapPoliticalManager instance
        """
        manager = cls(world_state, region_manager)
        
        # Load entities
        manager.entities = {int(entity_id): PoliticalEntity.from_dict(entity_data) 
                          for entity_id, entity_data in data["entities"].items()}
        
        # Load historical entities
        manager.historical_entities = {int(entity_id): PoliticalEntity.from_dict(entity_data) 
                                     for entity_id, entity_data in data["historical_entities"].items()}
        
        # Load next entity ID
        manager.next_entity_id = data["next_entity_id"]
        
        # Load borders
        manager.borders = [Border.from_dict(border_data) for border_data in data["borders"]]
        
        # Load disputes
        manager.disputes = [TerritorialDispute.from_dict(dispute_data) for dispute_data in data["disputes"]]
        
        # Load neutral territories
        manager.neutral_territories = set(data["neutral_territories"])
        
        # Load political events
        manager.political_events = data["political_events"]
        
        return manager

    #region Unity-Python Interface Methods
    
    def GetCellIdFromPosition(self, x: float, y: float) -> int:
        """
        Unity interface method: Get the cell ID from a position
        This wraps the region manager's method to maintain consistent naming with the C# components
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The cell ID at this position
        """
        return self.region_manager.GetCellIdFromPosition(x, y)
    
    def GetPoliticalEntityAtPosition(self, x: float, y: float) -> Dict[str, Any]:
        """
        Unity interface method: Get the political entity at a position
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Dictionary containing entity data, or empty dict if no entity found
        """
        entity = self.get_entity_at_position(x, y)
        if entity:
            return {
                "id": entity.id,
                "name": entity.name,
                "formType": entity.form_type.value,
                "fullName": entity.full_name,
                "color": entity.color,
                "militaryStrength": entity.military_strength,
                "stability": entity.stability
            }
        return {}
    
    def GetEntityById(self, entity_id: int) -> Dict[str, Any]:
        """
        Unity interface method: Get entity data by ID
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            Dictionary containing entity data, or empty dict if not found
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            return {
                "id": entity.id,
                "name": entity.name,
                "formType": entity.form_type.value,
                "fullName": entity.full_name,
                "color": entity.color,
                "centerCellId": entity.center_cell_id,
                "capitalId": entity.capital_id,
                "cultureId": entity.culture_id,
                "expansionism": entity.expansionism,
                "militaryStrength": entity.military_strength,
                "economicPower": entity.economic_power,
                "stability": entity.stability,
                "territoryCellCount": len(entity.territory_cells),
                "foundationDate": entity.foundation_date
            }
        return {}
    
    def GetEntityRelations(self, entity_id: int) -> Dict[str, str]:
        """
        Unity interface method: Get all relations for an entity
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            Dictionary mapping entity IDs to relation types
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            return {str(k): v.value for k, v in entity.relations.items()}
        return {}
    
    def GetEntityTerritory(self, entity_id: int) -> List[int]:
        """
        Unity interface method: Get all cells belonging to an entity
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            List of cell IDs in the entity's territory
        """
        if entity_id in self.entities:
            return list(self.entities[entity_id].territory_cells)
        return []
    
    def GetBordersBetweenEntities(self, entity1_id: int, entity2_id: int) -> Dict[str, Any]:
        """
        Unity interface method: Get border information between two entities
        
        Args:
            entity1_id: ID of the first entity
            entity2_id: ID of the second entity
            
        Returns:
            Dictionary containing border data
        """
        for border in self.borders:
            if (border.entity1_id == entity1_id and border.entity2_id == entity2_id) or \
               (border.entity1_id == entity2_id and border.entity2_id == entity1_id):
                return {
                    "entity1Id": border.entity1_id,
                    "entity2Id": border.entity2_id,
                    "cells": list(border.cells),
                    "borderType": border.border_type.value,
                    "length": border.length,
                    "isContested": border.is_contested
                }
        return {}
    
    def GetAllPoliticalEntities(self) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all political entities
        
        Returns:
            List of dictionaries containing entity data
        """
        entities_data = []
        for entity_id, entity in self.entities.items():
            entities_data.append({
                "id": entity.id,
                "name": entity.name,
                "formType": entity.form_type.value,
                "fullName": entity.full_name,
                "color": entity.color,
                "centerCellId": entity.center_cell_id,
                "capitalId": entity.capital_id,
                "cultureId": entity.culture_id,
                "expansionism": entity.expansionism,
                "militaryStrength": entity.military_strength,
                "economicPower": entity.economic_power,
                "stability": entity.stability,
                "territoryCellCount": len(entity.territory_cells)
            })
        return entities_data
    
    def GetAllBorders(self) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all borders
        
        Returns:
            List of dictionaries containing border data
        """
        borders_data = []
        for border in self.borders:
            borders_data.append({
                "entity1Id": border.entity1_id,
                "entity2Id": border.entity2_id,
                "cells": list(border.cells),
                "borderType": border.border_type.value,
                "length": border.length,
                "isContested": border.is_contested
            })
        return borders_data
    
    def GetAllDisputes(self) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get all territorial disputes
        
        Returns:
            List of dictionaries containing dispute data
        """
        disputes_data = []
        for dispute in self.disputes:
            disputes_data.append({
                "disputedCells": list(dispute.disputed_cells),
                "claimantIds": dispute.claimant_ids,
                "currentControllerId": dispute.current_controller_id,
                "startDate": dispute.start_date,
                "intensity": dispute.intensity,
                "resolved": dispute.resolved,
                "resolutionDate": dispute.resolution_date,
                "resolutionWinnerId": dispute.resolution_winner_id
            })
        return disputes_data
    
    def GetPoliticalEvents(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Unity interface method: Get recent political events
        
        Args:
            count: Maximum number of events to return
            
        Returns:
            List of dictionaries containing event data
        """
        # Return the most recent events first
        events = self.political_events[-count:] if len(self.political_events) > count else self.political_events
        events.reverse()  # Most recent first
        return events
    
    def CreateNewEntity(self, name: str, form_type: str, color: str, center_cell_id: int) -> int:
        """
        Unity interface method: Create a new political entity
        
        Args:
            name: Name of the entity
            form_type: Form type string (e.g., "Monarchy")
            color: Hex color code
            center_cell_id: Cell ID of the entity's center
            
        Returns:
            ID of the created entity, or -1 if failed
        """
        try:
            # Convert form type string to enum
            form_enum = PoliticalFormType(form_type)
            
            # Create the entity
            entity = self.create_entity(
                name=name,
                form_type=form_enum,
                color=color,
                center_cell_id=center_cell_id
            )
            
            return entity.id
        except Exception as e:
            print(f"Error creating entity: {e}")
            return -1
    
    def ChangeEntityForm(self, entity_id: int, new_form: str) -> bool:
        """
        Unity interface method: Change an entity's form of government
        
        Args:
            entity_id: ID of the entity
            new_form: New form type string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert form type string to enum
            form_enum = PoliticalFormType(new_form)
            
            # Update the entity
            return self.update_entity_form(entity_id, form_enum)
        except Exception as e:
            print(f"Error changing entity form: {e}")
            return False
    
    def SetEntityRelation(self, entity1_id: int, entity2_id: int, relation: str) -> bool:
        """
        Unity interface method: Set relation between two entities
        
        Args:
            entity1_id: ID of the first entity
            entity2_id: ID of the second entity
            relation: Relation type string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert relation string to enum
            relation_enum = RelationType(relation)
            
            # Set the relation
            return self.set_relation(entity1_id, entity2_id, relation_enum)
        except Exception as e:
            print(f"Error setting entity relation: {e}")
            return False
    
    def AddEntityTerritory(self, entity_id: int, cell_ids: List[int]) -> bool:
        """
        Unity interface method: Add territory to an entity
        
        Args:
            entity_id: ID of the entity
            cell_ids: List of cell IDs to add to territory
            
        Returns:
            True if successful, False otherwise
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.add_territory(set(cell_ids))
            
            # Update borders
            self._update_borders_after_entity_change(entity_id)
            
            return True
        return False
    
    def RemoveEntityTerritory(self, entity_id: int, cell_ids: List[int]) -> bool:
        """
        Unity interface method: Remove territory from an entity
        
        Args:
            entity_id: ID of the entity
            cell_ids: List of cell IDs to remove from territory
            
        Returns:
            True if successful, False otherwise
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.remove_territory(set(cell_ids))
            
            # Add to neutral territories
            self.neutral_territories.update(cell_ids)
            
            # Update borders
            self._update_borders_after_entity_change(entity_id)
            
            return True
        return False
    
    def StartTerritorialDispute(self, cell_ids: List[int], claimant_ids: List[int], controller_id: int) -> bool:
        """
        Unity interface method: Start a new territorial dispute
        
        Args:
            cell_ids: List of disputed cell IDs
            claimant_ids: List of entity IDs claiming the territory
            controller_id: ID of the entity currently controlling the territory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dispute = self.create_dispute(
                disputed_cells=set(cell_ids),
                claimant_ids=claimant_ids,
                current_controller_id=controller_id
            )
            
            return dispute is not None
        except Exception as e:
            print(f"Error starting territorial dispute: {e}")
            return False
    
    def ResolveTerritorialDispute(self, dispute_index: int, winner_id: int) -> bool:
        """
        Unity interface method: Resolve a territorial dispute
        
        Args:
            dispute_index: Index of the dispute in the disputes list
            winner_id: ID of the winning entity
            
        Returns:
            True if successful, False otherwise
        """
        return self.resolve_dispute(dispute_index, winner_id)
    
    def GeneratePoliticalEntities(self, num_entities: int) -> bool:
        """
        Unity interface method: Generate random political entities
        
        Args:
            num_entities: Number of entities to generate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.generate_random_political_entities(num_entities)
            return True
        except Exception as e:
            print(f"Error generating political entities: {e}")
            return False
    
    def GenerateBorderConflicts(self, num_conflicts: int) -> bool:
        """
        Unity interface method: Generate random border conflicts
        
        Args:
            num_conflicts: Number of conflicts to generate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.generate_border_conflicts(num_conflicts)
            return True
        except Exception as e:
            print(f"Error generating border conflicts: {e}")
            return False
    
    def UpdatePoliticalState(self) -> bool:
        """
        Unity interface method: Update the political state
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.update()
            return True
        except Exception as e:
            print(f"Error updating political state: {e}")
            return False
    
    def SaveToJson(self, path: str) -> bool:
        """
        Unity interface method: Save the political state to a JSON file
        
        Args:
            path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            # Convert to dictionary
            data = self.to_dict()
            
            # Save to file
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving political state: {e}")
            return False
    
    def LoadFromJson(self, path: str) -> bool:
        """
        Unity interface method: Load the political state from a JSON file
        
        Args:
            path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            # Load from file
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Create from dictionary
            manager = self.from_dict(data, self.world_state, self.region_manager)
            
            # Copy all attributes
            self.entities = manager.entities
            self.historical_entities = manager.historical_entities
            self.next_entity_id = manager.next_entity_id
            self.borders = manager.borders
            self.disputes = manager.disputes
            self.neutral_territories = manager.neutral_territories
            self.political_events = manager.political_events
            
            return True
        except Exception as e:
            print(f"Error loading political state: {e}")
            return False
    #endregion