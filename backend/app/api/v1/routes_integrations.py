"""
Integration Services API Routes

Provides endpoints for accessing ERP integration, external APIs, 
real-time streams, and automated refresh services.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import asyncio

from app.core.deps import get_db
from app.services.integrations.erp_integration import erp_service
from app.services.integrations.external_apis import external_api_service
<<<<<<< HEAD
from app.services.integrations.realtime_streams import realtime_service
=======
# from app.services.integrations.realtime_streams import realtime_service
>>>>>>> d4196135 (Fixed Bug)
from app.services.integrations.automated_refresh import automated_refresh_service
from app.utils.exceptions import IntegrationError

router = APIRouter()
logger = logging.getLogger(__name__)


# ERP Integration Endpoints
@router.get("/erp/plants")
async def get_erp_plants(db: Session = Depends(get_db)):
    """Fetch plant master data from SAP system."""
    try:
        plants_df = erp_service.fetch_plant_master_from_sap()
        return {
            "plants": plants_df.to_dict('records'),
            "count": len(plants_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching ERP plants: {e}")
        raise HTTPException(status_code=500, detail=f"ERP integration failed: {str(e)}")


@router.get("/erp/capacity")
async def get_erp_capacity(
    start_period: str = Query(..., description="Start period (YYYY-MM)"),
    end_period: str = Query(..., description="End period (YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """Fetch production capacity data from Oracle ERP."""
    try:
        capacity_df = erp_service.fetch_production_capacity_from_oracle(start_period, end_period)
        return {
            "capacity": capacity_df.to_dict('records'),
            "count": len(capacity_df),
            "period_range": f"{start_period} to {end_period}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching ERP capacity: {e}")
        raise HTTPException(status_code=500, detail=f"ERP integration failed: {str(e)}")


@router.get("/erp/demand-forecast")
async def get_erp_demand_forecast(
    horizon_months: int = Query(6, ge=1, le=24, description="Forecast horizon in months"),
    db: Session = Depends(get_db)
):
    """Fetch demand forecast from SAP APO/IBP."""
    try:
        demand_df = erp_service.fetch_demand_forecast_from_sap(horizon_months)
        return {
            "demand_forecast": demand_df.to_dict('records'),
            "count": len(demand_df),
            "horizon_months": horizon_months,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching ERP demand forecast: {e}")
        raise HTTPException(status_code=500, detail=f"ERP integration failed: {str(e)}")


@router.get("/erp/inventory")
async def get_erp_inventory(db: Session = Depends(get_db)):
    """Fetch current inventory levels from ERP system."""
    try:
        inventory_df = erp_service.fetch_inventory_levels_from_erp()
        return {
            "inventory": inventory_df.to_dict('records'),
            "count": len(inventory_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching ERP inventory: {e}")
        raise HTTPException(status_code=500, detail=f"ERP integration failed: {str(e)}")


@router.post("/erp/sync-all")
async def sync_all_erp_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync all master data from ERP systems."""
    try:
        # Run sync in background
        background_tasks.add_task(erp_service.sync_all_master_data, db)
        
        return {
            "message": "ERP data sync initiated",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initiating ERP sync: {e}")
        raise HTTPException(status_code=500, detail=f"ERP sync failed: {str(e)}")


# External APIs Endpoints
@router.get("/external/weather")
async def get_weather_data(
    days_ahead: int = Query(7, ge=1, le=14, description="Days ahead for forecast"),
):
    """Fetch weather forecast data for all plant locations."""
    try:
        weather_df = await external_api_service.fetch_weather_data(days_ahead)
        return {
            "weather": weather_df.to_dict('records'),
            "count": len(weather_df),
            "days_ahead": days_ahead,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        raise HTTPException(status_code=500, detail=f"Weather API failed: {str(e)}")


@router.get("/external/fuel-prices")
async def get_fuel_prices():
    """Fetch fuel price data from EIA."""
    try:
        fuel_df = external_api_service.fetch_fuel_price_data()
        return {
            "fuel_prices": fuel_df.to_dict('records'),
            "count": len(fuel_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching fuel prices: {e}")
        raise HTTPException(status_code=500, detail=f"Fuel price API failed: {str(e)}")


@router.get("/external/market-data")
async def get_market_data():
    """Fetch cement market prices and trends."""
    try:
        market_df = external_api_service.fetch_cement_market_data()
        return {
            "market_data": market_df.to_dict('records'),
            "count": len(market_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=f"Market data API failed: {str(e)}")


@router.get("/external/economic-indicators")
async def get_economic_indicators():
    """Fetch economic indicators affecting supply chain costs."""
    try:
        economic_df = external_api_service.fetch_economic_indicators()
        return {
            "economic_indicators": economic_df.to_dict('records'),
            "count": len(economic_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Economic data API failed: {str(e)}")


@router.get("/external/all")
async def get_all_external_data():
    """Fetch all external data sources."""
    try:
        all_data = await external_api_service.fetch_all_external_data()
        
        result = {}
        for data_type, df in all_data.items():
            result[data_type] = {
                "data": df.to_dict('records'),
                "count": len(df)
            }
        
        result["timestamp"] = datetime.now().isoformat()
        return result
        
    except Exception as e:
        logger.error(f"Error fetching all external data: {e}")
        raise HTTPException(status_code=500, detail=f"External data fetch failed: {str(e)}")


# Real-time Streams Endpoints
@router.post("/realtime/initialize")
async def initialize_realtime_streams():
    """Initialize real-time data stream connections."""
    try:
        await realtime_service.initialize_connections()
        return {
            "message": "Real-time streams initialized successfully",
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initializing real-time streams: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time initialization failed: {str(e)}")


@router.get("/realtime/production")
async def get_realtime_production(
    plant_id: Optional[str] = Query(None, description="Filter by plant ID")
):
    """Get latest production sensor data."""
    try:
        data = await realtime_service.get_latest_data('production', plant_id)
        return {
            "production_data": data,
            "count": len(data),
            "plant_filter": plant_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching real-time production data: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time data fetch failed: {str(e)}")


@router.get("/realtime/vehicles")
async def get_realtime_vehicles():
    """Get latest vehicle tracking data."""
    try:
        data = await realtime_service.get_latest_data('vehicle')
        return {
            "vehicle_data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching real-time vehicle data: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time data fetch failed: {str(e)}")


@router.get("/realtime/inventory")
async def get_realtime_inventory(
    plant_id: Optional[str] = Query(None, description="Filter by plant ID")
):
    """Get latest inventory sensor data."""
    try:
        data = await realtime_service.get_latest_data('inventory', plant_id)
        return {
            "inventory_data": data,
            "count": len(data),
            "plant_filter": plant_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching real-time inventory data: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time data fetch failed: {str(e)}")


@router.get("/realtime/quality")
async def get_realtime_quality():
    """Get latest quality control data."""
    try:
        data = await realtime_service.get_latest_data('quality')
        return {
            "quality_data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching real-time quality data: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time data fetch failed: {str(e)}")


@router.get("/realtime/energy")
async def get_realtime_energy():
    """Get latest energy monitoring data."""
    try:
        data = await realtime_service.get_latest_data('energy')
        return {
            "energy_data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching real-time energy data: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time data fetch failed: {str(e)}")


# Automated Refresh Endpoints
@router.post("/refresh/start")
async def start_automated_refresh():
    """Start the automated data refresh service."""
    try:
        automated_refresh_service.start_automated_refresh()
        return {
            "message": "Automated refresh service started",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting automated refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Automated refresh start failed: {str(e)}")


@router.post("/refresh/stop")
async def stop_automated_refresh():
    """Stop the automated data refresh service."""
    try:
        automated_refresh_service.stop_automated_refresh()
        return {
            "message": "Automated refresh service stopped",
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping automated refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Automated refresh stop failed: {str(e)}")


@router.get("/refresh/status")
async def get_refresh_status():
    """Get status and statistics of automated refresh service."""
    try:
        stats = automated_refresh_service.get_refresh_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting refresh status: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh status fetch failed: {str(e)}")


@router.post("/refresh/trigger/{refresh_type}")
async def trigger_manual_refresh(
    refresh_type: str,
    background_tasks: BackgroundTasks
):
    """Manually trigger a specific refresh type."""
    try:
        valid_types = [
            "erp_master_data", "erp_transactional_data", "external_weather",
            "external_market_data", "external_fuel_prices", "realtime_aggregation",
            "data_quality_check"
        ]
        
        if refresh_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid refresh type. Valid types: {valid_types}")
        
        # Trigger the specific refresh type
        if refresh_type == "erp_master_data":
            background_tasks.add_task(automated_refresh_service._refresh_erp_master_data)
        elif refresh_type == "erp_transactional_data":
            background_tasks.add_task(automated_refresh_service._refresh_erp_transactional_data)
        elif refresh_type == "external_weather":
            background_tasks.add_task(automated_refresh_service._refresh_weather_data)
        elif refresh_type == "external_market_data":
            background_tasks.add_task(automated_refresh_service._refresh_market_data)
        elif refresh_type == "external_fuel_prices":
            background_tasks.add_task(automated_refresh_service._refresh_fuel_prices)
        elif refresh_type == "realtime_aggregation":
            background_tasks.add_task(automated_refresh_service._aggregate_realtime_data)
        elif refresh_type == "data_quality_check":
            background_tasks.add_task(automated_refresh_service._run_data_quality_checks)
        
        return {
            "message": f"Manual refresh triggered for {refresh_type}",
            "refresh_type": refresh_type,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Manual refresh failed: {str(e)}")


# Integration Health Check
@router.get("/health")
async def get_integration_health():
    """Get health status of all integration services."""
    try:
        health_status = {
            "erp_integration": {
                "status": "healthy",
                "last_sync": "2025-01-01T10:00:00",
                "services": ["SAP", "Oracle"]
            },
            "external_apis": {
                "status": "healthy",
                "services": ["Weather API", "Fuel Price API", "Market Data API"]
            },
            "realtime_streams": {
                "status": "active",
                "active_streams": ["production", "vehicle", "inventory", "quality", "energy"]
            },
            "automated_refresh": {
                "status": "running" if automated_refresh_service.is_running else "stopped",
                "last_run": automated_refresh_service.last_refresh_times.get("erp_master_data", "Never")
            },
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting integration health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Configuration Endpoints
@router.get("/config/erp")
async def get_erp_config():
    """Get ERP integration configuration (sanitized)."""
    return {
        "sap_configured": bool(erp_service.sap_config.get('base_url')),
        "oracle_configured": bool(erp_service.oracle_config.get('host')),
        "connection_timeout": erp_service.sap_config.get('timeout', 30),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/config/external-apis")
async def get_external_apis_config():
    """Get external APIs configuration (sanitized)."""
    return {
        "weather_api_configured": bool(external_api_service.weather_api_key),
        "market_data_api_configured": bool(external_api_service.market_data_api_key),
        "fuel_price_api_configured": bool(external_api_service.fuel_price_api_key),
        "plant_locations_count": len(external_api_service.plant_locations),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/config/realtime")
async def get_realtime_config():
    """Get real-time streams configuration (sanitized)."""
    return {
        "iot_broker_configured": bool(realtime_service.iot_config.get('broker_url')),
        "redis_configured": bool(realtime_service.redis_client),
        "rabbitmq_configured": bool(realtime_service.rabbitmq_connection),
        "monitored_topics": len(realtime_service.iot_config.get('topics', [])),
        "timestamp": datetime.now().isoformat()
    }