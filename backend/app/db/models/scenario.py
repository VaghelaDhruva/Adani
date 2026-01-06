"""
Scenario and Approved Plan Models

Supports:
- Scenario versioning
- Scenario comparison
- Approved plan state
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Float, Index
from sqlalchemy.sql import func

from app.db.base import Base


class Scenario(Base):
    """Scenario definition and metadata."""
    
    __tablename__ = "scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    parent_scenario_id = Column(Integer, nullable=True)  # Reference to parent scenario
    
    # Scenario parameters
    parameters = Column(JSON, nullable=True)  # Demand multipliers, capacity changes, etc.
    
    # Status
    is_approved = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_scenario_version', 'scenario_name', 'version'),
        Index('idx_approved', 'is_approved', 'is_active'),
    )


class ScenarioComparison(Base):
    """Stores comparison data between scenarios."""
    
    __tablename__ = "scenario_comparison"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Scenarios being compared
    scenario_1_name = Column(String(255), nullable=False, index=True)
    scenario_2_name = Column(String(255), nullable=False, index=True)
    
    # Comparison metrics
    cost_difference = Column(Integer, nullable=True)  # scenario_2 - scenario_1 (in RUPEES)
    cost_difference_percent = Column(Float, nullable=True)
    
    # Detailed comparison
    comparison_data = Column(JSON, nullable=True)  # Full comparison breakdown
    
    # Timestamps
    compared_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_scenario_pair', 'scenario_1_name', 'scenario_2_name'),
    )

