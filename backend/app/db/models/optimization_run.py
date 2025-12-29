from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func

from app.db.base import Base


class OptimizationRun(Base):
    __tablename__ = "optimization_run"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(255), unique=True, nullable=False, index=True)
    scenario_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed
    solver_name = Column(String(100), nullable=False)  # HiGHS, CBC, Gurobi
    solver_status = Column(String(100))  # optimal, infeasible, timeout, etc.
    objective_value = Column(Float)  # total cost
    solve_time_seconds = Column(Float)
    mip_gap = Column(Float)
    time_limit_seconds = Column(Integer)
    
    # Scenario parameters
    scenario_parameters = Column(JSON)  # demand multipliers, capacity changes, etc.
    
    # Execution metadata
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Data validation status
    validation_passed = Column(Boolean, default=False)
    validation_report = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())