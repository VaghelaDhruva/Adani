"""
Optimization Service

Executes supply chain optimization using Pyomo and stores results.
Integrates with KPI calculator to provide real calculated figures.

PHASE 4 - IMPROVED OPTIMIZATION MODEL:
- SBQ (minimum batch quantity) as hard constraints
- Integer trip counts with vehicle capacity linking
- Fixed trip costs per dispatch
- Multi-period inventory balance
- Safety stock enforcement at end of each period
- Trips * vehicle_capacity >= shipped_volume
- SBQ <= shipped volume OR no shipment at all
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import uuid
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

from app.db.models.optimization_run import OptimizationRun
from app.db.models.optimization_results import OptimizationResults
from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.services.data_validation_service import run_comprehensive_validation
from app.services.kpi_calculator import KPICalculator
from app.services.optimization.model_builder import build_clinker_model
from app.utils.exceptions import OptimizationError, DataValidationError

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for executing supply chain optimization."""
    
    def __init__(self, db: Session):
        self.db = db
        self.kpi_calculator = KPICalculator(db)
    
    def run_optimization(
        self,
        scenario_name: str,
        solver_name: str = "HiGHS",
        time_limit: int = 600,
        mip_gap: float = 0.01,
        scenario_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run complete optimization and return run_id."""
        
        run_id = f"{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create optimization run record
        opt_run = OptimizationRun(
            run_id=run_id,
            scenario_name=scenario_name,
            status="running",
            solver_name=solver_name,
            time_limit_seconds=time_limit,
            scenario_parameters=scenario_parameters or {},
            started_at=datetime.utcnow()
        )
        
        self.db.add(opt_run)
        self.db.commit()
        
        try:
            # Step 1: Validate data
            logger.info(f"Starting optimization run {run_id} - validating data")
            validation_result = run_comprehensive_validation(self.db)
            
            if validation_result["overall_status"] != "PASS":
                opt_run.status = "failed"
                opt_run.error_message = "Data validation failed"
                opt_run.validation_report = validation_result
                opt_run.completed_at = datetime.utcnow()
                self.db.commit()
                raise DataValidationError("Data validation failed - cannot run optimization")
            
            opt_run.validation_passed = True
            opt_run.validation_report = validation_result
            self.db.commit()
            
            # Step 2: Load and prepare data
            logger.info(f"Run {run_id} - loading optimization data")
            model_data = self._load_optimization_data(scenario_parameters)
            
            # Step 3: Build and solve optimization model
            logger.info(f"Run {run_id} - building optimization model")
            model = self._build_optimization_model(model_data)
            
            logger.info(f"Run {run_id} - solving with {solver_name}")
            solver_result = self._solve_model(model, solver_name, time_limit, mip_gap)
            
            # Step 4: Extract and store results
            logger.info(f"Run {run_id} - extracting results")
            results = self._extract_results(model, solver_result, model_data)
            
            # Step 5: Save results to database
            self._save_results(run_id, results, solver_result)
            
            # Step 6: Update run status
            opt_run.status = "completed"
            opt_run.solver_status = str(solver_result.solver.termination_condition)
            opt_run.objective_value = results["total_cost"]
            opt_run.solve_time_seconds = solver_result.solver.time if hasattr(solver_result.solver, 'time') else None
            opt_run.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Optimization run {run_id} completed successfully")
            return run_id
            
        except Exception as e:
            logger.error(f"Optimization run {run_id} failed: {e}")
            opt_run.status = "failed"
            opt_run.error_message = str(e)
            opt_run.completed_at = datetime.utcnow()
            self.db.commit()
            raise OptimizationError(f"Optimization failed: {e}")
    
    def _load_optimization_data(self, scenario_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load all data needed for optimization using the SAFE data access guard."""
        
        # PHASE 1 DATA SAFETY: Use data access guard to prevent staging table access
        from app.services.data_access_guard import get_safe_optimization_data
        
        logger.info("Loading optimization data through data access guard (production tables only)")
        dataset = get_safe_optimization_data(self.db)
        
        # Convert to pandas DataFrames for compatibility with existing code
        plants_df = pd.DataFrame(dataset["plants"])
        production_df = pd.DataFrame(dataset["production_capacity"])
        routes_df = pd.DataFrame(dataset["transport_routes"])
        demand_df = pd.DataFrame(dataset["demand_forecast"])
        inventory_df = pd.DataFrame(dataset["initial_inventory"])
        safety_stock_df = pd.DataFrame(dataset["safety_stock_policies"])
        
        # Apply scenario parameters
        if scenario_parameters:
            demand_multiplier = scenario_parameters.get("demand_multiplier", 1.0)
            if demand_multiplier != 1.0:
                logger.info(f"Applying demand multiplier: {demand_multiplier}")
                demand_df["demand_tonnes"] *= demand_multiplier
            
            capacity_multiplier = scenario_parameters.get("capacity_multiplier", 1.0)
            if capacity_multiplier != 1.0:
                logger.info(f"Applying capacity multiplier: {capacity_multiplier}")
                production_df["max_capacity_tonnes"] *= capacity_multiplier
        
        logger.info(f"Loaded optimization data: {len(plants_df)} plants, {len(production_df)} capacity records, "
                   f"{len(routes_df)} routes, {len(demand_df)} demand records")
        
        return {
            "plants": plants_df,
            "production": production_df,
            "routes": routes_df,
            "demand": demand_df,
            "inventory": inventory_df,
            "safety_stock": safety_stock_df
        }
    
    def _build_optimization_model(self, data: Dict[str, Any]) -> pyo.ConcreteModel:
        """
        PHASE 4: Build advanced Pyomo optimization model with all required constraints.
        
        This model includes:
        - SBQ (minimum batch quantity) as hard constraints
        - Integer trip counts
        - Fixed trip costs per dispatch  
        - Multi-period inventory balance
        - Safety stock enforcement at end of each period
        - Vehicle capacity constraints: Trips * vehicle_capacity >= shipped_volume
        - SBQ constraints: SBQ <= shipped volume OR no shipment at all
        """
        
        logger.info("Building advanced optimization model with Phase 4 improvements")
        
        # Prepare data in the format expected by model_builder
        model_data = {
            "plants": data["plants"],
            "production_capacity_cost": data["production"],
            "transport_routes_modes": data["routes"],
            "demand_forecast": data["demand"],
            "safety_stock_policy": data["safety_stock"],
            "initial_inventory": data["inventory"],
            "time_periods": sorted(data["production"]["period"].unique().tolist()) if not data["production"].empty else []
        }
        
        # Configure penalty system for soft constraints (optional)
        penalty_config = {
            "unmet_demand": 10000.0,  # High penalty for unmet demand
            "safety_stock_violation": 5000.0,  # Penalty for safety stock violations
            "capacity_violation": 8000.0  # Penalty for capacity violations
        }
        
        # Build the advanced model using the model builder
        model = build_clinker_model(model_data, penalty_config)
        
        logger.info("Advanced optimization model built successfully with:")
        logger.info(f"- Plants: {len(model.I)}")
        logger.info(f"- Customers: {len(model.J)}")
        logger.info(f"- Time periods: {len(model.T)}")
        logger.info(f"- Routes: {len(model.R)}")
        logger.info(f"- Transport modes: {len(model.M)}")
        logger.info("- Integer trip variables with vehicle capacity constraints")
        logger.info("- SBQ (minimum batch quantity) hard constraints")
        logger.info("- Multi-period inventory balance")
        logger.info("- Safety stock enforcement")
        logger.info("- Fixed trip costs per dispatch")
        
        return model
    
    def _solve_model(self, model: pyo.ConcreteModel, solver_name: str, time_limit: int, mip_gap: float):
        """Solve the optimization model."""
        
        # Try different solvers in order of preference
        solvers_to_try = [solver_name.lower()]
        if solver_name.lower() != "highs":
            solvers_to_try.append("highs")
        if "cbc" not in solvers_to_try:
            solvers_to_try.append("cbc")
        
        for solver in solvers_to_try:
            try:
                opt = pyo.SolverFactory(solver)
                
                # Set solver options
                if solver == "highs":
                    opt.options["time_limit"] = time_limit
                    opt.options["mip_rel_gap"] = mip_gap
                elif solver == "cbc":
                    opt.options["seconds"] = time_limit
                    opt.options["ratio"] = mip_gap
                
                logger.info(f"Attempting to solve with {solver}")
                result = opt.solve(model, tee=True)
                
                if result.solver.termination_condition == TerminationCondition.optimal:
                    logger.info(f"Optimal solution found with {solver}")
                    return result
                elif result.solver.termination_condition == TerminationCondition.feasible:
                    logger.info(f"Feasible solution found with {solver}")
                    return result
                else:
                    logger.warning(f"Solver {solver} failed: {result.solver.termination_condition}")
                    
            except Exception as e:
                logger.warning(f"Solver {solver} not available or failed: {e}")
                continue
        
        raise OptimizationError("All solvers failed to find a solution")
    
    def _extract_results(self, model: pyo.ConcreteModel, solver_result, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 4: Extract results from advanced optimization model.
        
        Extracts results from the improved model including:
        - Integer trip counts
        - SBQ compliance
        - Safety stock levels
        - Multi-period inventory profiles
        - Fixed trip costs
        """
        
        # Extract objective value
        total_cost = pyo.value(model.total_cost)
        
        # Extract production plan
        production_plan = {}
        for i in model.I:  # Plants
            production_plan[i] = {}
            for t in model.T:  # Periods
                production_plan[i][t] = pyo.value(model.prod[i, t])
        
        # Extract shipment plan with trip information
        shipment_plan = {}
        trip_plan = {}
        for (i, j, mode) in model.R:  # Routes
            for t in model.T:  # Periods
                shipment_key = f"{i}-{j}-{mode}-{t}"
                trip_key = f"{i}-{j}-{mode}-{t}"
                
                shipment_qty = pyo.value(model.ship[i, j, mode, t])
                trip_count = pyo.value(model.trips[i, j, mode, t])
                use_mode = pyo.value(model.use_mode[i, j, mode, t])
                
                shipment_plan[shipment_key] = {
                    "shipment_tonnes": shipment_qty,
                    "trips": int(trip_count) if trip_count else 0,
                    "mode_activated": bool(use_mode),
                    "vehicle_capacity": pyo.value(model.vehicle_cap[i, j, mode]),
                    "sbq_requirement": pyo.value(model.sbq[i, j, mode])
                }
                
                trip_plan[trip_key] = {
                    "trips": int(trip_count) if trip_count else 0,
                    "shipment_tonnes": shipment_qty,
                    "utilization": (shipment_qty / (trip_count * pyo.value(model.vehicle_cap[i, j, mode]))) 
                                  if trip_count and pyo.value(model.vehicle_cap[i, j, mode]) > 0 else 0
                }
        
        # Extract inventory profile with safety stock compliance
        inventory_profile = {}
        safety_stock_compliance = {}
        for i in model.I:  # Plants
            inventory_profile[i] = {}
            safety_stock_compliance[i] = {}
            for t in model.T:  # Periods
                inventory_level = pyo.value(model.inv[i, t])
                safety_stock_req = pyo.value(model.ss[i])
                
                inventory_profile[i][t] = inventory_level
                safety_stock_compliance[i][t] = {
                    "inventory_level": inventory_level,
                    "safety_stock_requirement": safety_stock_req,
                    "compliance": inventory_level >= safety_stock_req,
                    "shortage": max(0, safety_stock_req - inventory_level)
                }
        
        # Calculate detailed cost breakdown
        production_cost = sum(
            pyo.value(model.prod[i, t]) * pyo.value(model.prod_cost[i, t])
            for i in model.I for t in model.T
        )
        
        transport_cost = sum(
            pyo.value(model.ship[i, j, mode, t]) * pyo.value(model.trans_cost[i, j, mode])
            for (i, j, mode) in model.R for t in model.T
        )
        
        # PHASE 4: Fixed trip costs (new in advanced model)
        fixed_trip_cost = sum(
            pyo.value(model.trips[i, j, mode, t]) * pyo.value(model.fixed_trip_cost[i, j, mode])
            for (i, j, mode) in model.R for t in model.T
        )
        
        inventory_cost = sum(
            pyo.value(model.inv[i, t]) * pyo.value(model.hold_cost[i])
            for i in model.I for t in model.T
        )
        
        # Calculate penalty costs (if penalty variables exist)
        penalty_cost = 0.0
        unmet_demand_total = 0.0
        safety_violations_total = 0.0
        
        if hasattr(model, 'unmet_demand'):
            unmet_demand_total = sum(
                pyo.value(model.unmet_demand[j, t])
                for j in model.J for t in model.T
            )
            penalty_cost += unmet_demand_total * 10000.0  # Penalty rate
        
        if hasattr(model, 'ss_violation'):
            safety_violations_total = sum(
                pyo.value(model.ss_violation[i, t])
                for i in model.I for t in model.T
            )
            penalty_cost += safety_violations_total * 5000.0  # Penalty rate
        
        # Calculate demand fulfillment metrics
        demand_fulfillment = {}
        total_demand = 0.0
        total_fulfilled = 0.0
        
        for j in model.J:  # Customers
            demand_fulfillment[j] = {}
            for t in model.T:  # Periods
                demand_qty = pyo.value(model.demand[j, t])
                fulfilled_qty = sum(
                    pyo.value(model.ship[i, j2, mode, t])
                    for (i, j2, mode) in model.R if j2 == j
                )
                
                # Account for unmet demand if penalty variables exist
                unmet_qty = 0.0
                if hasattr(model, 'unmet_demand'):
                    unmet_qty = pyo.value(model.unmet_demand[j, t])
                
                demand_fulfillment[j][t] = {
                    "demand": demand_qty,
                    "fulfilled": fulfilled_qty,
                    "unmet": unmet_qty,
                    "fulfillment_rate": (fulfilled_qty / demand_qty) if demand_qty > 0 else 1.0
                }
                
                total_demand += demand_qty
                total_fulfilled += fulfilled_qty
        
        # Calculate overall service level
        service_level = (total_fulfilled / total_demand) if total_demand > 0 else 1.0
        
        # Calculate SBQ compliance metrics
        sbq_compliance = {}
        for (i, j, mode) in model.R:
            for t in model.T:
                shipment_qty = pyo.value(model.ship[i, j, mode, t])
                sbq_req = pyo.value(model.sbq[i, j, mode])
                use_mode = pyo.value(model.use_mode[i, j, mode, t])
                
                key = f"{i}-{j}-{mode}-{t}"
                sbq_compliance[key] = {
                    "shipment_tonnes": shipment_qty,
                    "sbq_requirement": sbq_req,
                    "mode_activated": bool(use_mode),
                    "sbq_compliant": (shipment_qty >= sbq_req) if use_mode else True,
                    "violation": max(0, sbq_req - shipment_qty) if use_mode else 0
                }
        
        return {
            "total_cost": total_cost,
            "production_cost": production_cost,
            "transport_cost": transport_cost,
            "fixed_trip_cost": fixed_trip_cost,  # PHASE 4: New cost component
            "inventory_cost": inventory_cost,
            "penalty_cost": penalty_cost,
            "production_plan": production_plan,
            "shipment_plan": shipment_plan,
            "trip_plan": trip_plan,  # PHASE 4: New trip information
            "inventory_profile": inventory_profile,
            "safety_stock_compliance": safety_stock_compliance,  # PHASE 4: New compliance tracking
            "demand_fulfillment": demand_fulfillment,
            "sbq_compliance": sbq_compliance,  # PHASE 4: New SBQ compliance tracking
            "service_level": service_level,
            "unmet_demand_total": unmet_demand_total,
            "safety_violations_total": safety_violations_total,
            "stockout_events": int(unmet_demand_total > 0.001)
        }
    
    def _save_results(self, run_id: str, results: Dict[str, Any], solver_result):
        """
        PHASE 4: Save advanced optimization results to database.
        
        Saves results from the improved model including trip plans,
        SBQ compliance, and safety stock tracking.
        """
        
        opt_results = OptimizationResults(
            run_id=run_id,
            total_cost=results["total_cost"],
            production_cost=results["production_cost"],
            transport_cost=results["transport_cost"],
            inventory_cost=results["inventory_cost"],
            penalty_cost=results["penalty_cost"],
            production_plan=results["production_plan"],
            shipment_plan=results["shipment_plan"],
            inventory_profile=results["inventory_profile"],
            demand_fulfillment=results["demand_fulfillment"],
            service_level=results["service_level"],
            stockout_events=results["stockout_events"]
        )
        
        # PHASE 4: Add new result components to the JSON fields
        if hasattr(opt_results, 'additional_metrics'):
            opt_results.additional_metrics = {
                "fixed_trip_cost": results.get("fixed_trip_cost", 0.0),
                "trip_plan": results.get("trip_plan", {}),
                "safety_stock_compliance": results.get("safety_stock_compliance", {}),
                "sbq_compliance": results.get("sbq_compliance", {}),
                "unmet_demand_total": results.get("unmet_demand_total", 0.0),
                "safety_violations_total": results.get("safety_violations_total", 0.0)
            }
        else:
            # Store in shipment_plan as extended data if additional_metrics field doesn't exist
            extended_shipment_plan = results["shipment_plan"].copy()
            extended_shipment_plan["_metadata"] = {
                "fixed_trip_cost": results.get("fixed_trip_cost", 0.0),
                "trip_plan": results.get("trip_plan", {}),
                "safety_stock_compliance": results.get("safety_stock_compliance", {}),
                "sbq_compliance": results.get("sbq_compliance", {}),
                "unmet_demand_total": results.get("unmet_demand_total", 0.0),
                "safety_violations_total": results.get("safety_violations_total", 0.0)
            }
            opt_results.shipment_plan = extended_shipment_plan
        
        self.db.add(opt_results)
        self.db.commit()
        
        logger.info(f"Saved advanced optimization results for run {run_id}")
        logger.info(f"- Total cost: {results['total_cost']:,.2f}")
        logger.info(f"- Fixed trip cost: {results.get('fixed_trip_cost', 0):,.2f}")
        logger.info(f"- Service level: {results['service_level']:.1%}")
        logger.info(f"- Unmet demand: {results.get('unmet_demand_total', 0):,.2f} tonnes")
        logger.info(f"- Safety violations: {results.get('safety_violations_total', 0):,.2f} tonnes")
    
    def get_kpi_data(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get KPI data for the latest run of a scenario."""
        
        # Get latest completed run for scenario
        latest_run = self.db.query(OptimizationRun).filter(
            OptimizationRun.scenario_name == scenario_name,
            OptimizationRun.status == "completed"
        ).order_by(OptimizationRun.completed_at.desc()).first()
        
        if not latest_run:
            return None
        
        # Calculate and return KPIs
        return self.kpi_calculator.calculate_kpis_for_run(latest_run.run_id)