"""
Automated Data Refresh Service

Handles scheduled data refresh from various sources:
- ERP system synchronization
- External API data updates
- Real-time data aggregation
- Data quality monitoring
- Automated alerts and notifications
"""

import asyncio
import logging
import schedule
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import pandas as pd

from app.core.config import get_settings
<<<<<<< HEAD
from app.db.base import SessionLocal
from app.services.integrations.erp_integration import erp_service
from app.services.integrations.external_apis import external_api_service
from app.services.integrations.realtime_streams import realtime_service
=======
from app.db.session import SessionLocal
from app.services.integrations.erp_integration import erp_service
from app.services.integrations.external_apis import external_api_service
# from app.services.integrations.realtime_streams import realtime_service
>>>>>>> d4196135 (Fixed Bug)
from app.services.validation.data_quality import DataQualityService
from app.utils.exceptions import IntegrationError

logger = logging.getLogger(__name__)
settings = get_settings()


class AutomatedRefreshService:
    """Service for automated data refresh and synchronization."""
    
    def __init__(self):
        self.is_running = False
        self.refresh_schedules = {
            'erp_master_data': {'interval': 'daily', 'time': '02:00'},
            'erp_transactional_data': {'interval': 'hourly', 'time': None},
            'external_weather': {'interval': 'hourly', 'time': None},
            'external_market_data': {'interval': 'daily', 'time': '06:00'},
            'external_fuel_prices': {'interval': 'daily', 'time': '07:00'},
            'realtime_aggregation': {'interval': 'every_15_minutes', 'time': None},
            'data_quality_check': {'interval': 'every_30_minutes', 'time': None}
        }
        
        self.data_quality_service = DataQualityService()
        self.last_refresh_times = {}
        self.refresh_statistics = {}
    
    def start_automated_refresh(self):
        """Start the automated data refresh scheduler."""
        try:
            logger.info("Starting automated data refresh service")
            
            # Schedule ERP data refresh
            schedule.every().day.at("02:00").do(self._refresh_erp_master_data)
            schedule.every().hour.do(self._refresh_erp_transactional_data)
            
            # Schedule external API refresh
            schedule.every().hour.do(self._refresh_weather_data)
            schedule.every().day.at("06:00").do(self._refresh_market_data)
            schedule.every().day.at("07:00").do(self._refresh_fuel_prices)
            
            # Schedule real-time data aggregation
            schedule.every(15).minutes.do(self._aggregate_realtime_data)
            
            # Schedule data quality checks
            schedule.every(30).minutes.do(self._run_data_quality_checks)
            
            # Schedule cleanup tasks
            schedule.every().day.at("01:00").do(self._cleanup_old_data)
            
            self.is_running = True
            
            # Start the scheduler loop
            asyncio.create_task(self._scheduler_loop())
            
            logger.info("Automated data refresh service started successfully")
            
        except Exception as e:
            logger.error(f"Error starting automated refresh service: {e}")
            raise IntegrationError(f"Failed to start automated refresh: {str(e)}")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    def _refresh_erp_master_data(self):
        """Refresh master data from ERP systems."""
        try:
            logger.info("Starting ERP master data refresh")
            start_time = datetime.now()
            
            db = SessionLocal()
            try:
                # Sync master data from ERP
                results = erp_service.sync_all_master_data(db)
                
                # Update statistics
                self._update_refresh_statistics('erp_master_data', start_time, results)
                
                logger.info(f"ERP master data refresh completed: {results}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"ERP master data refresh failed: {e}")
            self._update_refresh_statistics('erp_master_data', start_time, {'error': str(e)})
    
    def _refresh_erp_transactional_data(self):
        """Refresh transactional data from ERP systems."""
        try:
            logger.info("Starting ERP transactional data refresh")
            start_time = datetime.now()
            
            db = SessionLocal()
            try:
                # Get current period
                current_period = datetime.now().strftime('%Y-%m')
                next_period = (datetime.now() + timedelta(days=32)).strftime('%Y-%m')
                
                # Fetch production capacity
                capacity_df = erp_service.fetch_production_capacity_from_oracle(
                    current_period, next_period
                )
                
                # Fetch demand forecast
                demand_df = erp_service.fetch_demand_forecast_from_sap()
                
                # Fetch inventory levels
                inventory_df = erp_service.fetch_inventory_levels_from_erp()
                
                results = {
                    'capacity_records': len(capacity_df),
                    'demand_records': len(demand_df),
                    'inventory_records': len(inventory_df)
                }
                
                # Update statistics
                self._update_refresh_statistics('erp_transactional_data', start_time, results)
                
                logger.info(f"ERP transactional data refresh completed: {results}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"ERP transactional data refresh failed: {e}")
            self._update_refresh_statistics('erp_transactional_data', start_time, {'error': str(e)})
    
    def _refresh_weather_data(self):
        """Refresh weather data from external APIs."""
        try:
            logger.info("Starting weather data refresh")
            start_time = datetime.now()
            
            # Fetch weather data asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            weather_df = loop.run_until_complete(
                external_api_service.fetch_weather_data(days_ahead=7)
            )
            
            loop.close()
            
            results = {'weather_records': len(weather_df)}
            
            # Store weather data in database
            db = SessionLocal()
            try:
                # Here you would insert weather data into database
                # weather_df.to_sql('weather_data', db.bind, if_exists='append', index=False)
                pass
            finally:
                db.close()
            
            # Update statistics
            self._update_refresh_statistics('external_weather', start_time, results)
            
            logger.info(f"Weather data refresh completed: {results}")
            
        except Exception as e:
            logger.error(f"Weather data refresh failed: {e}")
            self._update_refresh_statistics('external_weather', start_time, {'error': str(e)})
    
    def _refresh_market_data(self):
        """Refresh market data from external APIs."""
        try:
            logger.info("Starting market data refresh")
            start_time = datetime.now()
            
            # Fetch market data
            market_df = external_api_service.fetch_cement_market_data()
            economic_df = external_api_service.fetch_economic_indicators()
            
            results = {
                'market_records': len(market_df),
                'economic_records': len(economic_df)
            }
            
            # Store market data in database
            db = SessionLocal()
            try:
                # Here you would insert market data into database
                # market_df.to_sql('market_data', db.bind, if_exists='append', index=False)
                # economic_df.to_sql('economic_indicators', db.bind, if_exists='append', index=False)
                pass
            finally:
                db.close()
            
            # Update statistics
            self._update_refresh_statistics('external_market_data', start_time, results)
            
            logger.info(f"Market data refresh completed: {results}")
            
        except Exception as e:
            logger.error(f"Market data refresh failed: {e}")
            self._update_refresh_statistics('external_market_data', start_time, {'error': str(e)})
    
    def _refresh_fuel_prices(self):
        """Refresh fuel price data from external APIs."""
        try:
            logger.info("Starting fuel price data refresh")
            start_time = datetime.now()
            
            # Fetch fuel price data
            fuel_df = external_api_service.fetch_fuel_price_data()
            
            results = {'fuel_price_records': len(fuel_df)}
            
            # Store fuel price data in database
            db = SessionLocal()
            try:
                # Here you would insert fuel price data into database
                # fuel_df.to_sql('fuel_prices', db.bind, if_exists='append', index=False)
                pass
            finally:
                db.close()
            
            # Update statistics
            self._update_refresh_statistics('external_fuel_prices', start_time, results)
            
            logger.info(f"Fuel price data refresh completed: {results}")
            
        except Exception as e:
            logger.error(f"Fuel price data refresh failed: {e}")
            self._update_refresh_statistics('external_fuel_prices', start_time, {'error': str(e)})
    
    def _aggregate_realtime_data(self):
        """Aggregate real-time data for reporting."""
        try:
            logger.info("Starting real-time data aggregation")
            start_time = datetime.now()
            
            # Get latest real-time data
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            production_data = loop.run_until_complete(
                realtime_service.get_latest_data('production')
            )
            vehicle_data = loop.run_until_complete(
                realtime_service.get_latest_data('vehicle')
            )
            inventory_data = loop.run_until_complete(
                realtime_service.get_latest_data('inventory')
            )
            
            loop.close()
            
            # Aggregate data
            aggregated_data = self._perform_data_aggregation(
                production_data, vehicle_data, inventory_data
            )
            
            results = {
                'production_records': len(production_data),
                'vehicle_records': len(vehicle_data),
                'inventory_records': len(inventory_data),
                'aggregated_records': len(aggregated_data)
            }
            
            # Store aggregated data
            db = SessionLocal()
            try:
                # Here you would insert aggregated data into database
                pass
            finally:
                db.close()
            
            # Update statistics
            self._update_refresh_statistics('realtime_aggregation', start_time, results)
            
            logger.info(f"Real-time data aggregation completed: {results}")
            
        except Exception as e:
            logger.error(f"Real-time data aggregation failed: {e}")
            self._update_refresh_statistics('realtime_aggregation', start_time, {'error': str(e)})
    
    def _run_data_quality_checks(self):
        """Run automated data quality checks."""
        try:
            logger.info("Starting data quality checks")
            start_time = datetime.now()
            
            db = SessionLocal()
            try:
                # Run comprehensive data quality checks
                quality_results = self.data_quality_service.run_comprehensive_quality_check(db)
                
                # Check for critical issues
                critical_issues = [
                    issue for issue in quality_results.get('issues', [])
                    if issue.get('severity') == 'critical'
                ]
                
                if critical_issues:
                    self._send_data_quality_alerts(critical_issues)
                
                results = {
                    'total_checks': quality_results.get('total_checks', 0),
                    'passed_checks': quality_results.get('passed_checks', 0),
                    'failed_checks': quality_results.get('failed_checks', 0),
                    'critical_issues': len(critical_issues)
                }
                
                # Update statistics
                self._update_refresh_statistics('data_quality_check', start_time, results)
                
                logger.info(f"Data quality checks completed: {results}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Data quality checks failed: {e}")
            self._update_refresh_statistics('data_quality_check', start_time, {'error': str(e)})
    
    def _cleanup_old_data(self):
        """Clean up old data to maintain database performance."""
        try:
            logger.info("Starting data cleanup")
            start_time = datetime.now()
            
            db = SessionLocal()
            try:
                # Define retention periods
                retention_periods = {
                    'weather_data': 90,  # 90 days
                    'market_data': 365,  # 1 year
                    'fuel_prices': 365,  # 1 year
                    'realtime_aggregated': 30,  # 30 days
                    'audit_logs': 180  # 6 months
                }
                
                cleanup_results = {}
                
                for table, days in retention_periods.items():
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Here you would execute cleanup queries
                    # deleted_count = db.execute(
                    #     f"DELETE FROM {table} WHERE created_date < :cutoff_date",
                    #     {'cutoff_date': cutoff_date}
                    # ).rowcount
                    
                    deleted_count = 0  # Placeholder
                    cleanup_results[table] = deleted_count
                
                db.commit()
                
                # Update statistics
                self._update_refresh_statistics('data_cleanup', start_time, cleanup_results)
                
                logger.info(f"Data cleanup completed: {cleanup_results}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            self._update_refresh_statistics('data_cleanup', start_time, {'error': str(e)})
    
    def _perform_data_aggregation(self, production_data: List[Dict], 
                                vehicle_data: List[Dict], 
                                inventory_data: List[Dict]) -> List[Dict]:
        """Perform data aggregation on real-time data."""
        aggregated_data = []
        
        try:
            # Aggregate production data by plant
            if production_data:
                production_df = pd.DataFrame(production_data)
                production_agg = production_df.groupby('plant_id').agg({
                    'production_rate_tph': 'mean',
                    'efficiency_percent': 'mean',
                    'temperature_celsius': 'mean'
                }).reset_index()
                
                for _, row in production_agg.iterrows():
                    aggregated_data.append({
                        'type': 'production_summary',
                        'plant_id': row['plant_id'],
                        'avg_production_rate': row['production_rate_tph'],
                        'avg_efficiency': row['efficiency_percent'],
                        'avg_temperature': row['temperature_celsius'],
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Aggregate vehicle data
            if vehicle_data:
                vehicle_df = pd.DataFrame(vehicle_data)
                vehicle_agg = vehicle_df.groupby('vehicle_type').agg({
                    'speed_kmh': 'mean',
                    'fuel_level_percent': 'mean',
                    'load_tonnes': 'mean'
                }).reset_index()
                
                for _, row in vehicle_agg.iterrows():
                    aggregated_data.append({
                        'type': 'vehicle_summary',
                        'vehicle_type': row['vehicle_type'],
                        'avg_speed': row['speed_kmh'],
                        'avg_fuel_level': row['fuel_level_percent'],
                        'avg_load': row['load_tonnes'],
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Aggregate inventory data
            if inventory_data:
                inventory_df = pd.DataFrame(inventory_data)
                inventory_agg = inventory_df.groupby('plant_id').agg({
                    'level_percent': 'mean',
                    'current_tonnes': 'sum'
                }).reset_index()
                
                for _, row in inventory_agg.iterrows():
                    aggregated_data.append({
                        'type': 'inventory_summary',
                        'plant_id': row['plant_id'],
                        'avg_level_percent': row['level_percent'],
                        'total_inventory_tonnes': row['current_tonnes'],
                        'timestamp': datetime.now().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Data aggregation error: {e}")
        
        return aggregated_data
    
    def _send_data_quality_alerts(self, critical_issues: List[Dict]):
        """Send alerts for critical data quality issues."""
        try:
            for issue in critical_issues:
                alert_message = f"CRITICAL DATA QUALITY ISSUE: {issue.get('description', 'Unknown issue')}"
                
                # Here you would send alerts via email, SMS, or notification system
                logger.critical(alert_message)
                
                # You could also integrate with alerting systems like:
                # - Email notifications
                # - Slack/Teams notifications
                # - SMS alerts
                # - Dashboard notifications
                
        except Exception as e:
            logger.error(f"Error sending data quality alerts: {e}")
    
    def _update_refresh_statistics(self, refresh_type: str, start_time: datetime, results: Dict):
        """Update refresh statistics."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.last_refresh_times[refresh_type] = end_time
        
        if refresh_type not in self.refresh_statistics:
            self.refresh_statistics[refresh_type] = {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'avg_duration_seconds': 0,
                'last_run_time': None,
                'last_run_status': None,
                'last_run_results': None
            }
        
        stats = self.refresh_statistics[refresh_type]
        stats['total_runs'] += 1
        stats['last_run_time'] = end_time
        stats['last_run_results'] = results
        
        if 'error' in results:
            stats['failed_runs'] += 1
            stats['last_run_status'] = 'failed'
        else:
            stats['successful_runs'] += 1
            stats['last_run_status'] = 'success'
        
        # Update average duration
        stats['avg_duration_seconds'] = (
            (stats['avg_duration_seconds'] * (stats['total_runs'] - 1) + duration) / 
            stats['total_runs']
        )
    
    def get_refresh_statistics(self) -> Dict[str, Any]:
        """Get refresh statistics for monitoring."""
        return {
            'service_status': 'running' if self.is_running else 'stopped',
            'last_refresh_times': self.last_refresh_times,
            'refresh_statistics': self.refresh_statistics,
            'next_scheduled_runs': self._get_next_scheduled_runs()
        }
    
    def _get_next_scheduled_runs(self) -> Dict[str, str]:
        """Get next scheduled run times."""
        next_runs = {}
        
        for job in schedule.jobs:
            job_name = job.job_func.__name__
            next_run = job.next_run
            if next_run:
                next_runs[job_name] = next_run.isoformat()
        
        return next_runs
    
    def stop_automated_refresh(self):
        """Stop the automated data refresh service."""
        try:
            logger.info("Stopping automated data refresh service")
            
            self.is_running = False
            schedule.clear()
            
            logger.info("Automated data refresh service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping automated refresh service: {e}")


# Singleton instance
automated_refresh_service = AutomatedRefreshService()