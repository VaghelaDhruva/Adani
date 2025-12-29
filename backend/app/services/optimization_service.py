"""
Optimization Service

Executes supply chain optimization using Pyomo and stores results.
Integrates with KPI calculator to provide real calculated figures.
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
        """Load all data needed for optimization."""
        
        # Load plants
        plants_df = pd.DataFrame([
            {
                "plant_id": p.plant_id,
                "plant_name": p.plant_name,
                "plant_type": p.plant_type
            }
            for p in self.db.query(PlantMaster).all()
        ])
        
        # Load production capacity
        production_df = pd.DataFrame([
            {
                "plant_id": r.plant_id,
                "period": r.period,
                "max_capacity_tonnes": r.max_capacity_tonnes,
                "variable_cost_per_tonne": r.variable_cost_per_tonne,
                "fixed_cost_per_period": r.fixed_cost_per_period,
                "min_run_level": r.min_run_level,
                "holding_cost_per_tonne": r.holding_cost_per_tonne
            }
            for r in self.db.query(ProductionCapacityCost).all()
        ])
        
        # Load transport routes
        routes_df = pd.DataFrame([
            {
                "origin_plant_id": r.origin_plant_id,
                "destination_node_id": r.destination_node_id,
                "transport_mode": r.transport_mode,
                "distance_km": r.distance_km,
                "cost_per_tonne": r.cost_per_tonne,
                "cost_per_tonne_km": r.cost_per_tonne_km,
                "fixed_cost_per_trip": r.fixed_cost_per_trip,
                "vehicle_capacity_tonnes": r.vehicle_capacity_tonnes,
                "min_batch_quantity_tonnes": r.min_batch_quantity_tonnes,
                "lead_time_days": r.lead_time_days
            }
            for r in self.db.query(TransportRoutesModes).filter(TransportRoutesModes.is_active == "Y").all()
        ])
        
        # Load demand forecast
        demand_df = pd.DataFrame([
            {
                "customer_node_id": d.customer_node_id,
                "period": d.period,
                "demand_tonnes": d.demand_tonnes
            }
            for d in self.db.query(DemandForecast).all()
        ])
        
        # Apply scenario parameters
        if scenario_parameters:
            demand_multiplier = scenario_parameters.get("demand_multiplier", 1.0)
            demand_df["demand_tonnes"] *= demand_multiplier
            
            capacity_multiplier = scenario_parameters.get("capacity_multiplier", 1.0)
            production_df["max_capacity_tonnes"] *= capacity_multiplier
        
        # Load initial inventory
        inventory_df = pd.DataFrame([
            {
                "location_id": i.location_id,
                "initial_stock_tonnes": i.initial_stock_tonnes
            }
            for i in self.db.query(InitialInventory).all()
        ])
        
        # Load safety stock
        safety_stock_df = pd.DataFrame([
            {
                "location_id": s.location_id,
                "safety_stock_tonnes": s.safety_stock_tonnes,
                "penalty_cost_per_tonne": s.penalty_cost_per_tonne
            }
            for s in self.db.query(SafetyStockPolicy).all()
        ])
        
        return {
            "plants": plants_df,
            "production": production_df,
            "routes": routes_df,
            "demand": demand_df,
            "inventory": inventory_df,
            "safety_stock": safety_stock_df
        }
    
    def _build_optimization_model(self, data: Dict[str, Any]) -> pyo.ConcreteModel:
        """Build Pyomo optimization model."""
        
        model = pyo.ConcreteModel()
        
        # Sets
        model.plants = pyo.Set(initialize=data["plants"]["plant_id"].unique())
        model.periods = pyo.Set(initialize=data["production"]["period"].unique())
        model.customers = pyo.Set(initialize=data["demand"]["customer_node_id"].unique())
        model.routes = pyo.Set(initialize=[
            (row["origin_plant_id"], row["destination_node_id"], row["transport_mode"])
            for _, row in data["routes"].iterrows()
        ])
        
        # Parameters
        model.demand = pyo.Param(model.customers, model.periods, initialize=0.0, mutable=True)
        for _, row in data["demand"].iterrows():
            model.demand[row["customer_node_id"], row["period"]] = row["demand_tonnes"]
        
        model.capacity = pyo.Param(model.plants, model.periods, initialize=0.0, mutable=True)
        model.prod_cost = pyo.Param(model.plants, model.periods, initialize=0.0, mutable=True)
        for _, row in data["production"].iterrows():
            model.capacity[row["plant_id"], row["period"]] = row["max_capacity_tonnes"]
            model.prod_cost[row["plant_id"], row["period"]] = row["variable_cost_per_tonne"]
        
        model.transport_cost = pyo.Param(model.routes, initialize=0.0, mutable=True)
        for _, row in data["routes"].iterrows():
            route_key = (row["origin_plant_id"], row["destination_node_id"], row["transport_mode"])
            model.transport_cost[route_key] = row["cost_per_tonne"]
        
        # Decision Variables
        model.production = pyo.Var(model.plants, model.periods, domain=pyo.NonNegativeReals)
        model.shipment = pyo.Var(model.routes, model.periods, domain=pyo.NonNegativeReals)
        model.inventory = pyo.Var(model.plants.union(model.customers), model.periods, domain=pyo.NonNegativeReals)
        
        # Objective Function
        def objective_rule(model):
            production_cost = sum(
                model.production[p, t] * model.prod_cost[p, t]
                for p in model.plants for t in model.periods
            )
            
            transport_cost = sum(
                model.shipment[r, t] * model.transport_cost[r]
                for r in model.routes for t in model.periods
            )
            
            inventory_cost = sum(
                model.inventory[l, t] * 10.0  # Holding cost per tonne
                for l in model.plants.union(model.customers) for t in model.periods
            )
            
            return production_cost + transport_cost + inventory_cost
        
        model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
        
        # Constraints
        def capacity_constraint_rule(model, p, t):
            return model.production[p, t] <= model.capacity[p, t]
        model.capacity_constraint = pyo.Constraint(model.plants, model.periods, rule=capacity_constraint_rule)
        
        def demand_constraint_rule(model, c, t):
            inflow = sum(
                model.shipment[p, c, m, t]
                for p, dest, m in model.routes if dest == c
            )
            return inflow >= model.demand[c, t]
        model.demand_constraint = pyo.Constraint(model.customers, model.periods, rule=demand_constraint_rule)
        
        def inventory_balance_rule(model, p, t):
            if t == model.periods.first():
                # Initial inventory (assume 1000 tonnes)
                initial_inv = 1000.0
            else:
                prev_period = model.periods.prev(t)
                initial_inv = model.inventory[p, prev_period]
            
            production = model.production[p, t]
            
            outflow = sum(
                model.shipment[p, dest, m, t]
                for origin, dest, m in model.routes if origin == p
            )
            
            return model.inventory[p, t] == initial_inv + production - outflow
        
        model.inventory_balance = pyo.Constraint(model.plants, model.periods, rule=inventory_balance_rule)
        
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
        """Extract results from solved model."""
        
        # Extract objective value
        total_cost = pyo.value(model.total_cost)
        
        # Extract production plan
        production_plan = {}
        for p in model.plants:
            production_plan[p] = {}
            for t in model.periods:
                production_plan[p][t] = pyo.value(model.production[p, t])
        
        # Extract shipment plan
        shipment_plan = {}
        for r in model.routes:
            for t in model.periods:
                key = f"{r[0]}-{r[1]}-{r[2]}-{t}"
                shipment_plan[key] = pyo.value(model.shipment[r, t])
        
        # Extract inventory profile
        inventory_profile = {}
        for l in model.plants.union(model.customers):
            inventory_profile[l] = {}
            for t in model.periods:
                inventory_profile[l][t] = pyo.value(model.inventory[l, t])
        
        # Calculate cost breakdown
        production_cost = sum(
            pyo.value(model.production[p, t]) * pyo.value(model.prod_cost[p, t])
            for p in model.plants for t in model.periods
        )
        
        transport_cost = sum(
            pyo.value(model.shipment[r, t]) * pyo.value(model.transport_cost[r])
            for r in model.routes for t in model.periods
        )
        
        inventory_cost = sum(
            pyo.value(model.inventory[l, t]) * 10.0
            for l in model.plants.union(model.customers) for t in model.periods
        )
        
        # Calculate demand fulfillment
        demand_fulfillment = {}
        for c in model.customers:
            demand_fulfillment[c] = {}
            for t in model.periods:
                demand = pyo.value(model.demand[c, t])
                fulfilled = sum(
                    pyo.value(model.shipment[p, c, m, t])
                    for p, dest, m in model.routes if dest == c
                )
                demand_fulfillment[c][t] = {
                    "demand": demand,
                    "fulfilled": min(fulfilled, demand),
                    "backorder": max(0, demand - fulfilled)
                }
        
        # Calculate service level
        total_demand = sum(pyo.value(model.demand[c, t]) for c in model.customers for t in model.periods)
        total_fulfilled = sum(
            min(
                sum(pyo.value(model.shipment[p, c, m, t]) for p, dest, m in model.routes if dest == c),
                pyo.value(model.demand[c, t])
            )
            for c in model.customers for t in model.periods
        )
        service_level = total_fulfilled / total_demand if total_demand > 0 else 1.0
        
        return {
            "total_cost": total_cost,
            "production_cost": production_cost,
            "transport_cost": transport_cost,
            "inventory_cost": inventory_cost,
            "penalty_cost": 0.0,  # No penalties in this simple model
            "production_plan": production_plan,
            "shipment_plan": shipment_plan,
            "inventory_profile": inventory_profile,
            "demand_fulfillment": demand_fulfillment,
            "service_level": service_level,
            "stockout_events": 0  # Calculate from demand fulfillment
        }
    
    def _save_results(self, run_id: str, results: Dict[str, Any], solver_result):
        """Save optimization results to database."""
        
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
        
        self.db.add(opt_results)
        self.db.commit()
        
        logger.info(f"Saved optimization results for run {run_id}")
    
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