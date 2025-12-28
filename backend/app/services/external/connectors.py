"""
External data connectors for API, database, and file sources.
Integrates with the existing validation and quarantine logic.
"""

from typing import Dict, Any, List, Optional, Union
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from app.services.data_router import DataSource
from app.services.validation.validators import validate_schema, detect_missing_or_inconsistent
from app.services.audit_service import log_event
from app.utils.exceptions import DataValidationError


logger = logging.getLogger(__name__)


class BaseConnector:
    """Base class for all external data connectors."""
    
    def __init__(self, config: Dict[str, Any], connector_id: str):
        """
        Initialize connector.
        
        Args:
            config: Connector configuration
            connector_id: Unique identifier for this connector
        """
        self.config = config
        self.connector_id = connector_id
        self.last_ingestion_time = None
        self.ingestion_stats = {
            "total_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "validation_errors": 0
        }
    
    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """
        Fetch data from external source.
        
        Args:
            table_name: Name of the table/data to fetch
            
        Returns:
            DataFrame with fetched data
        """
        raise NotImplementedError("Subclasses must implement fetch_data")
    
    def validate_and_tag_data(self, data: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Validate data and add source tagging.
        
        Args:
            data: Raw data to validate
            table_name: Name of the table for schema validation
            
        Returns:
            Validated and tagged DataFrame
        """
        if data.empty:
            return data
        
        # Add source tagging columns
        data["data_source"] = DataSource.EXTERNAL.value
        data["source_connector_id"] = self.connector_id
        data["ingestion_timestamp"] = datetime.utcnow().isoformat()
        data["ingestion_run_id"] = str(uuid.uuid4())
        
        # Validate data
        try:
            schema_valid = validate_schema(data, table_name)
            consistency_check = detect_missing_or_inconsistent(data, table_name)
            
            if not schema_valid or consistency_check["has_issues"]:
                self.ingestion_stats["validation_errors"] += 1
                
                # Log validation failure
                log_event(
                    user="system",
                    action="external_data_validation_failed",
                    status="failed",
                    details={
                        "connector_id": self.connector_id,
                        "table_name": table_name,
                        "schema_valid": schema_valid,
                        "consistency_issues": consistency_check.get("issues", []),
                        "record_count": len(data)
                    }
                )
                
                # Quarantine invalid data
                self._quarantine_invalid_data(data, table_name, schema_valid, consistency_check)
                
                # Return only valid records if possible
                if consistency_check.get("valid_indices"):
                    return data.iloc[consistency_check["valid_indices"]].copy()
                else:
                    return pd.DataFrame()  # No valid records
            
            self.ingestion_stats["successful_records"] += len(data)
            return data
            
        except Exception as e:
            self.ingestion_stats["validation_errors"] += 1
            logger.error(f"Validation error for {table_name}: {e}")
            
            # Quarantine due to validation error
            self._quarantine_validation_error(data, table_name, str(e))
            return pd.DataFrame()
    
    def _quarantine_invalid_data(
        self,
        data: pd.DataFrame,
        table_name: str,
        schema_valid: bool,
        consistency_check: Dict[str, Any]
    ):
        """Move invalid data to quarantine."""
        quarantine_record = {
            "connector_id": self.connector_id,
            "table_name": table_name,
            "timestamp": datetime.utcnow().isoformat(),
            "schema_valid": schema_valid,
            "consistency_issues": consistency_check.get("issues", []),
            "record_count": len(data),
            "sample_data": data.head().to_dict() if not data.empty else {}
        }
        
        log_event(
            user="system",
            action="external_data_quarantine",
            status="failed",
            details=quarantine_record
        )
    
    def _quarantine_validation_error(self, data: pd.DataFrame, table_name: str, error: str):
        """Quarantine data due to validation error."""
        quarantine_record = {
            "connector_id": self.connector_id,
            "table_name": table_name,
            "timestamp": datetime.utcnow().isoformat(),
            "validation_error": error,
            "record_count": len(data),
            "sample_data": data.head().to_dict() if not data.empty else {}
        }
        
        log_event(
            user="system",
            action="external_data_validation_error",
            status="failed",
            details=quarantine_record
        )
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        return {
            "connector_id": self.connector_id,
            "last_ingestion_time": self.last_ingestion_time,
            "ingestion_stats": self.ingestion_stats.copy()
        }


class APIConnector(BaseConnector):
    """Connector for REST API data sources."""
    
    def __init__(self, config: Dict[str, Any], connector_id: str):
        super().__init__(config, connector_id)
        self.base_url = config["base_url"]
        self.headers = config.get("headers", {})
        self.auth = config.get("auth")
        self.timeout = config.get("timeout", 30)
        
        # Setup authentication if provided
        if self.auth:
            if self.auth["type"] == "bearer":
                self.headers["Authorization"] = f"Bearer {self.auth['token']}"
            elif self.auth["type"] == "api_key":
                self.headers[self.auth["header"]] = self.auth["key"]
    
    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """Fetch data from REST API."""
        try:
            # Build endpoint URL
            endpoint = self.config.get("endpoints", {}).get(table_name, f"/{table_name}")
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Add query parameters
            params = self.config.get("parameters", {}).get(table_name, {})
            
            # Make request
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if "data" in data:
                    df = pd.DataFrame(data["data"])
                elif "results" in data:
                    df = pd.DataFrame(data["results"])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError(f"Unexpected response format: {type(data)}")
            
            self.last_ingestion_time = datetime.utcnow()
            self.ingestion_stats["total_records"] = len(df)
            
            logger.info(f"Successfully fetched {len(df)} records from API for {table_name}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {table_name}: {e}")
            raise DataValidationError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Error processing API response for {table_name}: {e}")
            raise DataValidationError(f"Response processing failed: {e}")


class DatabaseConnector(BaseConnector):
    """Connector for external database sources."""
    
    def __init__(self, config: Dict[str, Any], connector_id: str):
        super().__init__(config, connector_id)
        self.connection_string = config["connection_string"]
        self.engine = create_engine(self.connection_string)
    
    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """Fetch data from external database."""
        try:
            # Get query for table
            query = self.config.get("queries", {}).get(table_name)
            if not query:
                # Default query - select all from table
                query = f"SELECT * FROM {table_name}"
            
            # Execute query
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
            
            self.last_ingestion_time = datetime.utcnow()
            self.ingestion_stats["total_records"] = len(df)
            
            logger.info(f"Successfully fetched {len(df)} records from database for {table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Database query failed for {table_name}: {e}")
            raise DataValidationError(f"Database query failed: {e}")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


class FileConnector(BaseConnector):
    """Connector for file-based data sources."""
    
    def __init__(self, config: Dict[str, Any], connector_id: str):
        super().__init__(config, connector_id)
        self.base_path = Path(config["base_path"])
        self.file_patterns = config.get("file_patterns", {})
    
    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """Fetch data from files."""
        try:
            # Get file pattern for table
            pattern = self.file_patterns.get(table_name, f"{table_name}.*")
            file_paths = list(self.base_path.glob(pattern))
            
            if not file_paths:
                raise FileNotFoundError(f"No files found for {table_name} with pattern {pattern}")
            
            # Read and combine files
            dfs = []
            for file_path in file_paths:
                df = self._read_file(file_path)
                df["source_file"] = file_path.name
                dfs.append(df)
            
            if not dfs:
                return pd.DataFrame()
            
            # Combine all files
            combined_df = pd.concat(dfs, ignore_index=True)
            
            self.last_ingestion_time = datetime.utcnow()
            self.ingestion_stats["total_records"] = len(combined_df)
            
            logger.info(f"Successfully fetched {len(combined_df)} records from {len(dfs)} files for {table_name}")
            return combined_df
            
        except Exception as e:
            logger.error(f"File reading failed for {table_name}: {e}")
            raise DataValidationError(f"File reading failed: {e}")
    
    def _read_file(self, file_path: Path) -> pd.DataFrame:
        """Read a single file based on its extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == ".csv":
            return pd.read_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        elif suffix == ".json":
            with open(file_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        elif suffix == ".parquet":
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")


class ConnectorManager:
    """Manages multiple external data connectors."""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.connector_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_connector(self, connector_id: str, config: Dict[str, Any]) -> None:
        """
        Register a new external connector.
        
        Args:
            connector_id: Unique identifier for the connector
            config: Connector configuration
        """
        connector_type = config.get("type")
        
        if connector_type == "api":
            connector = APIConnector(config, connector_id)
        elif connector_type == "database":
            connector = DatabaseConnector(config, connector_id)
        elif connector_type == "file":
            connector = FileConnector(config, connector_id)
        else:
            raise ValueError(f"Unsupported connector type: {connector_type}")
        
        self.connectors[connector_id] = connector
        self.connector_configs[connector_id] = config
        
        logger.info(f"Registered {connector_type} connector: {connector_id}")
    
    def fetch_data(
        self,
        table_name: str,
        connector_id: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Fetch data using specified or all available connectors.
        
        Args:
            table_name: Name of the table to fetch
            connector_id: Specific connector to use (optional)
            
        Returns:
            Tuple of (DataFrame, metadata)
        """
        metadata = {
            "table_name": table_name,
            "timestamp": datetime.utcnow().isoformat(),
            "connectors_used": [],
            "records_fetched": 0,
            "validation_errors": 0,
            "source": DataSource.EXTERNAL.value
        }
        
        if connector_id:
            # Use specific connector
            if connector_id not in self.connectors:
                raise ValueError(f"Connector not found: {connector_id}")
            
            connector = self.connectors[connector_id]
            raw_data = connector.fetch_data(table_name)
            validated_data = connector.validate_and_tag_data(raw_data, table_name)
            
            metadata["connectors_used"].append(connector_id)
            metadata["records_fetched"] = len(validated_data)
            metadata["validation_errors"] = connector.ingestion_stats["validation_errors"]
            
            return validated_data, metadata
        else:
            # Try all connectors
            all_data = []
            total_validation_errors = 0
            
            for conn_id, connector in self.connectors.items():
                try:
                    raw_data = connector.fetch_data(table_name)
                    validated_data = connector.validate_and_tag_data(raw_data, table_name)
                    
                    if not validated_data.empty:
                        all_data.append(validated_data)
                    
                    metadata["connectors_used"].append(conn_id)
                    metadata["records_fetched"] += len(validated_data)
                    total_validation_errors += connector.ingestion_stats["validation_errors"]
                    
                except Exception as e:
                    logger.warning(f"Connector {conn_id} failed for {table_name}: {e}")
                    continue
            
            # Combine data from all successful connectors
            if all_data:
                combined_data = pd.concat(all_data, ignore_index=True)
                metadata["validation_errors"] = total_validation_errors
                return combined_data, metadata
            else:
                return pd.DataFrame(), metadata
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get status of all registered connectors."""
        status = {
            "total_connectors": len(self.connectors),
            "connector_types": {},
            "connectors": {}
        }
        
        for conn_id, connector in self.connectors.items():
            conn_type = self.connector_configs[conn_id]["type"]
            
            if conn_type not in status["connector_types"]:
                status["connector_types"][conn_type] = 0
            status["connector_types"][conn_type] += 1
            
            stats = connector.get_ingestion_stats()
            status["connectors"][conn_id] = {
                "type": conn_type,
                "last_ingestion": stats["last_ingestion_time"],
                "total_records": stats["ingestion_stats"]["total_records"],
                "success_rate": (
                    stats["ingestion_stats"]["successful_records"] /
                    max(stats["ingestion_stats"]["total_records"], 1)
                )
            }
        
        return status
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all connector connections."""
        results = {}
        
        for conn_id, connector in self.connectors.items():
            try:
                if isinstance(connector, DatabaseConnector):
                    results[conn_id] = connector.test_connection()
                else:
                    # For API and file connectors, try a simple fetch
                    connector.fetch_data("test")  # This may fail, but we catch it
                    results[conn_id] = True
            except Exception:
                results[conn_id] = False
        
        return results
