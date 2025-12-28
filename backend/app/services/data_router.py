"""
Dual-source data architecture with preference routing and provenance tracking.
Prefers internal cleaned data, falls back to external sources when needed.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.services.ingestion.tabular_ingestion import ingest_table
from app.services.validation.validators import validate_schema, detect_missing_or_inconsistent
from app.services.audit_service import log_event
from app.utils.exceptions import DataValidationError


class DataSource(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    FALLBACK = "fallback"


class DataRouter:
    """
    Routes data requests between internal and external sources with preference logic.
    Maintains full auditability of which source was used.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.run_id = str(uuid.uuid4())
        self.source_usage_log: List[Dict[str, Any]] = []
    
    def get_data(
        self,
        table_name: str,
        external_connectors: Optional[Dict[str, Any]] = None,
        force_external: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Get data with dual-source routing.
        
        Args:
            table_name: Name of the data table to retrieve
            external_connectors: Dict of external data connectors
            force_external: Force use of external source even if internal available
            
        Returns:
            Tuple of (DataFrame, metadata including source used)
        """
        metadata = {
            "table_name": table_name,
            "run_id": self.run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source_used": None,
            "validation_status": None,
            "records_count": 0
        }
        
        # Step 1: Try internal data first (unless forced external)
        if not force_external:
            try:
                internal_data = self._get_internal_data(table_name)
                if internal_data is not None and not internal_data.empty:
                    validation_result = self._validate_data(internal_data, table_name)
                    if validation_result["is_valid"]:
                        metadata["source_used"] = DataSource.INTERNAL.value
                        metadata["validation_status"] = "passed"
                        metadata["records_count"] = len(internal_data)
                        self._log_source_usage(table_name, DataSource.INTERNAL, "success")
                        return internal_data, metadata
                    else:
                        self._log_source_usage(table_name, DataSource.INTERNAL, f"validation_failed: {validation_result['errors']}")
            except Exception as e:
                self._log_source_usage(table_name, DataSource.INTERNAL, f"error: {str(e)}")
        
        # Step 2: Try external data if internal failed or forced
        if external_connectors and table_name in external_connectors:
            try:
                external_data = self._get_external_data(table_name, external_connectors[table_name])
                if external_data is not None and not external_data.empty:
                    validation_result = self._validate_data(external_data, table_name)
                    if validation_result["is_valid"]:
                        metadata["source_used"] = DataSource.EXTERNAL.value
                        metadata["validation_status"] = "passed"
                        metadata["records_count"] = len(external_data)
                        self._log_source_usage(table_name, DataSource.EXTERNAL, "success")
                        return external_data, metadata
                    else:
                        self._log_source_usage(table_name, DataSource.EXTERNAL, f"validation_failed: {validation_result['errors']}")
                        # Quarantine invalid external data
                        self._quarantine_data(external_data, table_name, DataSource.EXTERNAL, validation_result["errors"])
            except Exception as e:
                self._log_source_usage(table_name, DataSource.EXTERNAL, f"error: {str(e)}")
        
        # Step 3: Return empty dataframe with metadata if all sources failed
        metadata["source_used"] = DataSource.FALLBACK.value
        metadata["validation_status"] = "no_data_available"
        self._log_source_usage(table_name, DataSource.FALLBACK, "no_data_available")
        return pd.DataFrame(), metadata
    
    def _get_internal_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """Retrieve data from internal database."""
        try:
            # Query the appropriate model based on table name
            if table_name == "plant_master":
                from app.db.models.plant_master import PlantMaster
                data = pd.read_sql(self.db.query(PlantMaster).statement, self.db.bind)
            elif table_name == "demand_forecast":
                from app.db.models.demand_forecast import DemandForecast
                data = pd.read_sql(self.db.query(DemandForecast).statement, self.db.bind)
            elif table_name == "transport_routes_modes":
                from app.db.models.transport_routes_modes import TransportRoutesModes
                data = pd.read_sql(self.db.query(TransportRoutesModes).statement, self.db.bind)
            elif table_name == "production_capacity_cost":
                from app.db.models.production_capacity_cost import ProductionCapacityCost
                data = pd.read_sql(self.db.query(ProductionCapacityCost).statement, self.db.bind)
            elif table_name == "safety_stock_policy":
                from app.db.models.safety_stock_policy import SafetyStockPolicy
                data = pd.read_sql(self.db.query(SafetyStockPolicy).statement, self.db.bind)
            elif table_name == "initial_inventory":
                from app.db.models.initial_inventory import InitialInventory
                data = pd.read_sql(self.db.query(InitialInventory).statement, self.db.bind)
            else:
                raise ValueError(f"Unknown internal table: {table_name}")
            
            return data
        except Exception:
            return None
    
    def _get_external_data(self, table_name: str, connector_config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Retrieve data from external source."""
        try:
            source_type = connector_config.get("type")
            
            if source_type == "api":
                return self._get_api_data(connector_config)
            elif source_type == "database":
                return self._get_database_data(connector_config)
            elif source_type == "file":
                return self._get_file_data(connector_config)
            else:
                raise ValueError(f"Unsupported external source type: {source_type}")
        except Exception:
            return None
    
    def _get_api_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from REST API."""
        import requests
        
        url = config["url"]
        headers = config.get("headers", {})
        params = config.get("params", {})
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame(data)
    
    def _get_database_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from external database."""
        from sqlalchemy import create_engine
        
        connection_string = config["connection_string"]
        query = config["query"]
        
        engine = create_engine(connection_string)
        return pd.read_sql(query, engine)
    
    def _get_file_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from file (CSV, Excel, etc.)."""
        file_path = config["path"]
        file_type = config.get("type", "csv").lower()
        
        if file_type == "csv":
            return pd.read_csv(file_path)
        elif file_type in ["xlsx", "xls"]:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _validate_data(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Validate data against schema and business rules."""
        try:
            # Schema validation
            schema_valid = validate_schema(data, table_name)
            
            # Business rule validation
            consistency_check = detect_missing_or_inconsistent(data, table_name)
            
            is_valid = schema_valid and not consistency_check["has_issues"]
            errors = []
            
            if not schema_valid:
                errors.append("Schema validation failed")
            if consistency_check["has_issues"]:
                errors.extend(consistency_check["issues"])
            
            return {
                "is_valid": is_valid,
                "errors": errors,
                "schema_valid": schema_valid,
                "consistency_check": consistency_check
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "schema_valid": False,
                "consistency_check": {"has_issues": True, "issues": [str(e)]}
            }
    
    def _quarantine_data(self, data: pd.DataFrame, table_name: str, source: DataSource, errors: List[str]):
        """Move invalid data to quarantine for review."""
        quarantine_record = {
            "run_id": self.run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "table_name": table_name,
            "source": source.value,
            "errors": errors,
            "record_count": len(data),
            "sample_data": data.head().to_dict() if not data.empty else {}
        }
        
        # Log quarantine event
        log_event(
            user="system",
            action="data_quarantine",
            status="failed",
            details=quarantine_record
        )
    
    def _log_source_usage(self, table_name: str, source: DataSource, status: str):
        """Log which data source was used for auditability."""
        log_entry = {
            "table_name": table_name,
            "source": source.value,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id
        }
        self.source_usage_log.append(log_entry)
        
        # Also log to audit service
        log_event(
            user="system",
            action="data_source_usage",
            status="success" if status == "success" else "failed",
            details=log_entry
        )
    
    def get_source_usage_summary(self) -> Dict[str, Any]:
        """Get summary of data source usage for this run."""
        summary = {
            "run_id": self.run_id,
            "total_tables_requested": len(self.source_usage_log),
            "source_breakdown": {},
            "failed_attempts": [],
            "usage_log": self.source_usage_log
        }
        
        for entry in self.source_usage_log:
            source = entry["source"]
            if source not in summary["source_breakdown"]:
                summary["source_breakdown"][source] = {"success": 0, "failed": 0}
            
            if entry["status"] == "success":
                summary["source_breakdown"][source]["success"] += 1
            else:
                summary["source_breakdown"][source]["failed"] += 1
                summary["failed_attempts"].append(entry)
        
        return summary
