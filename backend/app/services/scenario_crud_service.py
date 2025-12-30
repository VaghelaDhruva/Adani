"""
PHASE 3 - SCENARIO MANAGEMENT: Service layer for scenario CRUD operations

This service provides scenario metadata management with proper validation
and error handling.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
import logging
import uuid
from datetime import datetime

from app.utils.exceptions import DataValidationError
from app.schemas.scenario import ScenarioMetadata, ScenarioMetadataCreate, ScenarioMetadataUpdate

logger = logging.getLogger(__name__)


class ScenarioMetadataService:
    """Service for managing scenario metadata."""
    
    def __init__(self):
        # For now, we'll use in-memory storage since there's no ScenarioMetadata model
        # In a real implementation, this would use a database table
        self._scenarios: Dict[str, Dict[str, Any]] = {}
    
    def create_scenario(self, scenario_data: ScenarioMetadataCreate) -> ScenarioMetadata:
        """Create a new scenario metadata record."""
        try:
            # Check if scenario already exists
            if scenario_data.name in self._scenarios:
                raise DataValidationError(f"Scenario '{scenario_data.name}' already exists")
            
            # Create scenario metadata
            scenario_dict = {
                "name": scenario_data.name,
                "description": scenario_data.description,
                "created_by": getattr(scenario_data, 'created_by', 'system'),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "draft",
                "parameters": getattr(scenario_data, 'parameters', {}),
                "tags": getattr(scenario_data, 'tags', [])
            }
            
            self._scenarios[scenario_data.name] = scenario_dict
            
            logger.info(f"Created scenario: {scenario_data.name}")
            return ScenarioMetadata(**scenario_dict)
            
        except DataValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating scenario {scenario_data.name}: {e}")
            raise DataValidationError(f"Failed to create scenario: {str(e)}")
    
    def get_scenario(self, scenario_name: str) -> Optional[ScenarioMetadata]:
        """Get a scenario by name."""
        try:
            scenario_dict = self._scenarios.get(scenario_name)
            if not scenario_dict:
                return None
            
            return ScenarioMetadata(**scenario_dict)
            
        except Exception as e:
            logger.error(f"Error getting scenario {scenario_name}: {e}")
            raise DataValidationError(f"Failed to retrieve scenario: {str(e)}")
    
    def list_scenarios(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        created_by_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List scenarios with pagination and filtering."""
        try:
            # Apply filters
            filtered_scenarios = []
            for scenario_dict in self._scenarios.values():
                if status_filter and scenario_dict.get("status") != status_filter:
                    continue
                if created_by_filter and scenario_dict.get("created_by") != created_by_filter:
                    continue
                filtered_scenarios.append(scenario_dict)
            
            # Sort by created_at descending
            filtered_scenarios.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply pagination
            total = len(filtered_scenarios)
            paginated_scenarios = filtered_scenarios[skip:skip + limit]
            
            # Convert to Pydantic models
            scenario_models = [ScenarioMetadata(**s) for s in paginated_scenarios]
            
            return {
                "items": scenario_models,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            }
            
        except Exception as e:
            logger.error(f"Error listing scenarios: {e}")
            raise DataValidationError(f"Failed to list scenarios: {str(e)}")
    
    def update_scenario(
        self, 
        scenario_name: str, 
        scenario_update: ScenarioMetadataUpdate
    ) -> Optional[ScenarioMetadata]:
        """Update an existing scenario."""
        try:
            if scenario_name not in self._scenarios:
                return None
            
            scenario_dict = self._scenarios[scenario_name]
            
            # Update fields
            update_data = scenario_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field != "name":  # Don't allow name changes
                    scenario_dict[field] = value
            
            scenario_dict["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated scenario: {scenario_name}")
            return ScenarioMetadata(**scenario_dict)
            
        except Exception as e:
            logger.error(f"Error updating scenario {scenario_name}: {e}")
            raise DataValidationError(f"Failed to update scenario: {str(e)}")
    
    def delete_scenario(self, scenario_name: str) -> bool:
        """Delete a scenario by name."""
        try:
            if scenario_name not in self._scenarios:
                return False
            
            del self._scenarios[scenario_name]
            logger.info(f"Deleted scenario: {scenario_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting scenario {scenario_name}: {e}")
            raise DataValidationError(f"Failed to delete scenario: {str(e)}")
    
    def get_scenario_count(self) -> int:
        """Get total number of scenarios."""
        return len(self._scenarios)


# Global instance
scenario_service = ScenarioMetadataService()