"""
ERP System Integration Service

Connects to SAP, Oracle, and other ERP systems to fetch master data,
production data, demand forecasts, and inventory levels.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import DataValidationError, IntegrationError

logger = logging.getLogger(__name__)
settings = get_settings()


class ERPIntegrationService:
    """Service for integrating with various ERP systems."""
    
    def __init__(self):
        self.sap_config = {
            'base_url': settings.SAP_BASE_URL,
            'username': settings.SAP_USERNAME,
            'password': settings.SAP_PASSWORD,
            'client': settings.SAP_CLIENT,
            'timeout': 30
        }
        
        self.oracle_config = {
            'host': settings.ORACLE_HOST,
            'port': settings.ORACLE_PORT,
            'service_name': settings.ORACLE_SERVICE_NAME,
            'username': settings.ORACLE_USERNAME,
            'password': settings.ORACLE_PASSWORD
        }
    
    def fetch_plant_master_from_sap(self) -> pd.DataFrame:
        """Fetch plant master data from SAP system."""
        try:
            logger.info("Fetching plant master data from SAP")
            
            # SAP OData API call
            url = f"{self.sap_config['base_url']}/sap/opu/odata/sap/ZMM_PLANT_MASTER_SRV/PlantSet"
            
            auth = (self.sap_config['username'], self.sap_config['password'])
            headers = {
                'Accept': 'application/json',
                'X-CSRF-Token': 'Fetch'
            }
            
            response = requests.get(url, auth=auth, headers=headers, timeout=self.sap_config['timeout'])
            
            if response.status_code != 200:
                raise IntegrationError(f"SAP API error: {response.status_code} - {response.text}")
            
            data = response.json()
            plants_data = data.get('d', {}).get('results', [])
            
            # Transform SAP data to our schema
            plants_df = pd.DataFrame([
                {
                    'plant_id': plant['Werks'],
                    'plant_name': plant['Name1'],
                    'plant_type': self._map_sap_plant_type(plant['Fabkl']),
                    'latitude': float(plant.get('Latitude', 0)) if plant.get('Latitude') else None,
                    'longitude': float(plant.get('Longitude', 0)) if plant.get('Longitude') else None,
                    'region': plant.get('Regio', ''),
                    'country': plant.get('Land1', 'IN'),
                    'created_date': datetime.now(),
                    'last_updated': datetime.now()
                }
                for plant in plants_data
            ])
            
            logger.info(f"Successfully fetched {len(plants_df)} plants from SAP")
            return plants_df
            
        except requests.exceptions.Timeout:
            raise IntegrationError("SAP connection timeout")
        except requests.exceptions.ConnectionError:
            raise IntegrationError("Cannot connect to SAP system")
        except Exception as e:
            logger.error(f"Error fetching plant data from SAP: {e}")
            raise IntegrationError(f"SAP integration failed: {str(e)}")
    
    def fetch_production_capacity_from_oracle(self, start_period: str, end_period: str) -> pd.DataFrame:
        """Fetch production capacity data from Oracle ERP."""
        try:
            import cx_Oracle
            
            logger.info(f"Fetching production capacity from Oracle for {start_period} to {end_period}")
            
            # Oracle connection
            dsn = cx_Oracle.makedsn(
                self.oracle_config['host'],
                self.oracle_config['port'],
                service_name=self.oracle_config['service_name']
            )
            
            connection = cx_Oracle.connect(
                user=self.oracle_config['username'],
                password=self.oracle_config['password'],
                dsn=dsn
            )
            
            # SQL query for production capacity
            query = """
            SELECT 
                pc.PLANT_CODE as plant_id,
                pc.PERIOD_CODE as period,
                pc.MAX_CAPACITY_TONNES as max_capacity_tonnes,
                pc.MIN_CAPACITY_TONNES as min_capacity_tonnes,
                pc.VARIABLE_COST_PER_TONNE as variable_cost_per_tonne,
                pc.FIXED_COST_PER_PERIOD as fixed_cost_per_period,
                pc.MAINTENANCE_FLAG as maintenance_scheduled,
                pc.LAST_UPDATED
            FROM PRODUCTION_CAPACITY pc
            WHERE pc.PERIOD_CODE BETWEEN :start_period AND :end_period
            AND pc.ACTIVE_FLAG = 'Y'
            ORDER BY pc.PLANT_CODE, pc.PERIOD_CODE
            """
            
            capacity_df = pd.read_sql(
                query, 
                connection, 
                params={'start_period': start_period, 'end_period': end_period}
            )
            
            # Data type conversions
            capacity_df['maintenance_scheduled'] = capacity_df['maintenance_scheduled'] == 'Y'
            capacity_df['last_updated'] = pd.to_datetime(capacity_df['last_updated'])
            
            connection.close()
            
            logger.info(f"Successfully fetched {len(capacity_df)} capacity records from Oracle")
            return capacity_df
            
        except ImportError:
            raise IntegrationError("cx_Oracle package not installed. Install with: pip install cx_Oracle")
        except Exception as e:
            logger.error(f"Error fetching capacity data from Oracle: {e}")
            raise IntegrationError(f"Oracle integration failed: {str(e)}")
    
    def fetch_demand_forecast_from_sap(self, forecast_horizon_months: int = 6) -> pd.DataFrame:
        """Fetch demand forecast data from SAP APO/IBP."""
        try:
            logger.info(f"Fetching demand forecast from SAP for {forecast_horizon_months} months")
            
            # SAP APO/IBP API call
            url = f"{self.sap_config['base_url']}/sap/bc/rest/zdemand_forecast"
            
            auth = (self.sap_config['username'], self.sap_config['password'])
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                'horizon_months': forecast_horizon_months,
                'product_group': 'CLINKER',
                'version': 'ACTIVE'
            }
            
            response = requests.post(url, json=payload, auth=auth, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise IntegrationError(f"SAP Demand API error: {response.status_code}")
            
            forecast_data = response.json()
            
            # Transform to our schema
            demand_df = pd.DataFrame([
                {
                    'customer_node_id': item['customer_id'],
                    'period': item['period'],
                    'demand_tonnes': float(item['forecast_qty']),
                    'demand_low_tonnes': float(item['forecast_qty']) * 0.9,
                    'demand_high_tonnes': float(item['forecast_qty']) * 1.1,
                    'confidence_level': float(item.get('confidence', 0.8)),
                    'source': 'SAP_APO',
                    'created_date': datetime.now()
                }
                for item in forecast_data.get('forecasts', [])
            ])
            
            logger.info(f"Successfully fetched {len(demand_df)} demand forecasts from SAP")
            return demand_df
            
        except Exception as e:
            logger.error(f"Error fetching demand forecast from SAP: {e}")
            raise IntegrationError(f"SAP demand forecast failed: {str(e)}")
    
    def fetch_inventory_levels_from_erp(self) -> pd.DataFrame:
        """Fetch current inventory levels from ERP system."""
        try:
            logger.info("Fetching current inventory levels from ERP")
            
            # This could be SAP, Oracle, or other ERP system
            url = f"{self.sap_config['base_url']}/sap/opu/odata/sap/ZMM_INVENTORY_SRV/InventorySet"
            
            auth = (self.sap_config['username'], self.sap_config['password'])
            headers = {'Accept': 'application/json'}
            
            response = requests.get(url, auth=auth, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise IntegrationError(f"ERP Inventory API error: {response.status_code}")
            
            data = response.json()
            inventory_data = data.get('d', {}).get('results', [])
            
            # Transform to our schema
            inventory_df = pd.DataFrame([
                {
                    'node_id': inv['Plant'],
                    'period': datetime.now().strftime('%Y-%m'),
                    'inventory_tonnes': float(inv['UnrestrictedStock']),
                    'safety_stock_tonnes': float(inv.get('SafetyStock', 0)),
                    'last_updated': datetime.now()
                }
                for inv in inventory_data
            ])
            
            logger.info(f"Successfully fetched {len(inventory_df)} inventory records from ERP")
            return inventory_df
            
        except Exception as e:
            logger.error(f"Error fetching inventory from ERP: {e}")
            raise IntegrationError(f"ERP inventory fetch failed: {str(e)}")
    
    def _map_sap_plant_type(self, sap_plant_category: str) -> str:
        """Map SAP plant category to our plant types."""
        mapping = {
            'CLIN': 'clinker',
            'GRND': 'grinding',
            'TERM': 'terminal',
            'CUST': 'customer'
        }
        return mapping.get(sap_plant_category, 'unknown')
    
    def sync_all_master_data(self, db: Session) -> Dict[str, Any]:
        """Sync all master data from ERP systems."""
        results = {
            'plants': 0,
            'capacity': 0,
            'demand': 0,
            'inventory': 0,
            'errors': []
        }
        
        try:
            # Fetch and sync plants
            plants_df = self.fetch_plant_master_from_sap()
            # Here you would insert into database
            results['plants'] = len(plants_df)
            
            # Fetch and sync capacity
            capacity_df = self.fetch_production_capacity_from_oracle('2025-01', '2025-12')
            results['capacity'] = len(capacity_df)
            
            # Fetch and sync demand
            demand_df = self.fetch_demand_forecast_from_sap()
            results['demand'] = len(demand_df)
            
            # Fetch and sync inventory
            inventory_df = self.fetch_inventory_levels_from_erp()
            results['inventory'] = len(inventory_df)
            
            logger.info(f"ERP sync completed: {results}")
            
        except Exception as e:
            error_msg = f"ERP sync failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results


# Singleton instance
erp_service = ERPIntegrationService()