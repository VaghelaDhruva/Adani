"""
KPI Precomputation Service

Precomputes KPIs after optimization runs for fast dashboard loading.
Avoids expensive calculations on every dashboard request.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.kpi_precomputed import KPIPrecomputed, KPIAggregated
from app.db.models.optimization_run import OptimizationRun
from app.utils.currency import format_rupees

logger = logging.getLogger(__name__)


class KPIPrecomputationService:
    """Service for precomputing and caching KPIs."""
    
    @staticmethod
    def precompute_kpis(
        db: Session,
        optimization_run_id: int,
        scenario_name: str,
        optimization_results: Dict[str, Any]
    ) -> None:
        """
        Precompute KPIs from optimization results and store in database.
        
        Args:
            db: Database session
            optimization_run_id: ID of optimization run
            scenario_name: Scenario name
            optimization_results: Results from optimizer
        """
        try:
            logger.info(f"Precomputing KPIs for run {optimization_run_id}, scenario {scenario_name}")
            
            # Extract data from results
            cost_breakdown = optimization_results.get("cost_breakdown", {})
            production_plan = optimization_results.get("production_plan", [])
            shipment_plan = optimization_results.get("shipment_plan", [])
            trip_plan = optimization_results.get("trip_plan", [])
            inventory_profile = optimization_results.get("inventory_profile", [])
            service_metrics = optimization_results.get("service_metrics", {})
            utilization_metrics = optimization_results.get("utilization_metrics", {})
            
            # Aggregate by period
            periods = set()
            for plan in production_plan:
                periods.add(plan.get("period"))
            for plan in shipment_plan:
                periods.add(plan.get("period"))
            
            # Create KPI records for each period
            for period in periods:
                # Calculate period-specific KPIs
                period_production = sum(
                    p.get("production_tonnes", 0)
                    for p in production_plan
                    if p.get("period") == period
                )
                
                period_shipment = sum(
                    s.get("shipment_tonnes", 0)
                    for s in shipment_plan
                    if s.get("period") == period
                )
                
                period_trips = sum(
                    t.get("trips", 0)
                    for t in trip_plan
                    if t.get("period") == period
                )
                
                period_inventory = sum(
                    inv.get("inventory_tonnes", 0)
                    for inv in inventory_profile
                    if inv.get("period") == period
                ) / max(len([inv for inv in inventory_profile if inv.get("period") == period]), 1)
                
                # Create KPI record
                kpi = KPIPrecomputed(
                    optimization_run_id=optimization_run_id,
                    scenario_name=scenario_name,
                    period=period,
                    total_cost=optimization_results.get("objective_value", 0),
                    production_cost=cost_breakdown.get("production_cost", 0),
                    transport_cost=cost_breakdown.get("transport_cost", 0),
                    fixed_trip_cost=cost_breakdown.get("fixed_trip_cost", 0),
                    holding_cost=cost_breakdown.get("holding_cost", 0),
                    penalty_cost=cost_breakdown.get("penalty_cost", 0),
                    total_production_tonnes=period_production,
                    production_utilization=utilization_metrics.get("production_utilization", 0),
                    total_shipment_tonnes=period_shipment,
                    total_trips=period_trips,
                    transport_utilization=utilization_metrics.get("transport_utilization", 0),
                    sbq_compliance_rate=1.0,  # Calculate from actual data
                    average_inventory_tonnes=period_inventory,
                    inventory_turns=utilization_metrics.get("inventory_turns", 12.0),
                    total_demand_tonnes=0,  # Would need to load from demand data
                    total_unmet_demand_tonnes=0,  # Would need to calculate
                    demand_fulfillment_rate=service_metrics.get("demand_fulfillment_rate", 1.0),
                    service_level=service_metrics.get("service_level", 1.0),
                    stockout_events=service_metrics.get("stockout_events", 0),
                    computed_at=datetime.now()
                )
                
                db.add(kpi)
            
            # Create aggregated KPI record
            aggregated = KPIAggregated(
                scenario_name=scenario_name,
                total_cost=optimization_results.get("objective_value", 0),
                cost_breakdown=cost_breakdown,
                total_production=sum(p.get("production_tonnes", 0) for p in production_plan),
                total_shipment=sum(s.get("shipment_tonnes", 0) for s in shipment_plan),
                total_trips=sum(t.get("trips", 0) for t in trip_plan),
                average_service_level=service_metrics.get("service_level", 1.0),
                last_updated=datetime.now()
            )
            
            # Update or insert aggregated
            existing = db.query(KPIAggregated).filter(
                KPIAggregated.scenario_name == scenario_name
            ).first()
            
            if existing:
                existing.total_cost = aggregated.total_cost
                existing.cost_breakdown = aggregated.cost_breakdown
                existing.total_production = aggregated.total_production
                existing.total_shipment = aggregated.total_shipment
                existing.total_trips = aggregated.total_trips
                existing.average_service_level = aggregated.average_service_level
                existing.last_updated = datetime.now()
            else:
                db.add(aggregated)
            
            db.commit()
            logger.info(f"KPIs precomputed successfully for scenario {scenario_name}")
            
        except Exception as e:
            logger.error(f"Failed to precompute KPIs: {e}", exc_info=True)
            db.rollback()
            raise
    
    @staticmethod
    def get_kpis_for_scenario(
        db: Session,
        scenario_name: str,
        period: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get precomputed KPIs for a scenario.
        
        Fast query - uses indexes for instant loading.
        """
        query = db.query(KPIPrecomputed).filter(
            KPIPrecomputed.scenario_name == scenario_name
        )
        
        if period:
            query = query.filter(KPIPrecomputed.period == period)
        
        kpis = query.order_by(KPIPrecomputed.period).all()
        
        return [
            {
                "period": kpi.period,
                "total_cost": kpi.total_cost,
                "total_cost_formatted": format_rupees(kpi.total_cost),
                "production_cost": kpi.production_cost,
                "transport_cost": kpi.transport_cost,
                "fixed_trip_cost": kpi.fixed_trip_cost,
                "holding_cost": kpi.holding_cost,
                "penalty_cost": kpi.penalty_cost,
                "total_production_tonnes": kpi.total_production_tonnes,
                "production_utilization": kpi.production_utilization,
                "total_shipment_tonnes": kpi.total_shipment_tonnes,
                "total_trips": kpi.total_trips,
                "transport_utilization": kpi.transport_utilization,
                "sbq_compliance_rate": kpi.sbq_compliance_rate,
                "average_inventory_tonnes": kpi.average_inventory_tonnes,
                "inventory_turns": kpi.inventory_turns,
                "demand_fulfillment_rate": kpi.demand_fulfillment_rate,
                "service_level": kpi.service_level,
                "stockout_events": kpi.stockout_events
            }
            for kpi in kpis
        ]
    
    @staticmethod
    def get_aggregated_kpis(db: Session) -> List[Dict[str, Any]]:
        """Get aggregated KPIs for all scenarios (for comparison)."""
        kpis = db.query(KPIAggregated).order_by(KPIAggregated.last_updated.desc()).all()
        
        return [
            {
                "scenario_name": kpi.scenario_name,
                "total_cost": kpi.total_cost,
                "total_cost_formatted": format_rupees(kpi.total_cost),
                "cost_breakdown": kpi.cost_breakdown,
                "total_production": kpi.total_production,
                "total_shipment": kpi.total_shipment,
                "total_trips": kpi.total_trips,
                "average_service_level": kpi.average_service_level,
                "last_updated": kpi.last_updated.isoformat() if kpi.last_updated else None
            }
            for kpi in kpis
        ]

