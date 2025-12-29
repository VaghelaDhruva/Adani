"""
Data Quality Service

Provides comprehensive data quality checks and validation for the supply chain system.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DataQualityService:
    """Service for data quality checks and validation."""
    
    def __init__(self):
        self.quality_rules = {
            "plants": {
                "required_fields": ["plant_id", "capacity_tonnes"],
                "numeric_fields": ["capacity_tonnes", "initial_inventory", "safety_stock_tonnes"],
                "positive_fields": ["capacity_tonnes"],
                "unique_fields": ["plant_id"]
            },
            "customers": {
                "required_fields": ["customer_id", "location"],
                "unique_fields": ["customer_id"]
            },
            "demand": {
                "required_fields": ["customer_id", "period", "demand_tonnes"],
                "numeric_fields": ["demand_tonnes"],
                "positive_fields": ["demand_tonnes"]
            },
            "routes": {
                "required_fields": ["from", "to", "mode"],
                "numeric_fields": ["distance_km"],
                "positive_fields": ["distance_km"]
            }
        }
    
    def run_comprehensive_quality_check(self, db: Session) -> Dict[str, Any]:
        """Run comprehensive data quality checks."""
        try:
            logger.info("Running comprehensive data quality checks")
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "issues": [],
                "table_results": {}
            }
            
            # Check each data type
            for table_name, rules in self.quality_rules.items():
                table_result = self._check_table_quality(table_name, rules, db)
                results["table_results"][table_name] = table_result
                
                results["total_checks"] += table_result["total_checks"]
                results["passed_checks"] += table_result["passed_checks"]
                results["failed_checks"] += table_result["failed_checks"]
                results["issues"].extend(table_result["issues"])
            
            # Overall quality score
            if results["total_checks"] > 0:
                results["quality_score"] = results["passed_checks"] / results["total_checks"]
            else:
                results["quality_score"] = 1.0
            
            logger.info(f"Data quality check completed: {results['quality_score']:.2%} passed")
            return results
            
        except Exception as e:
            logger.error(f"Error running data quality checks: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 1,
                "issues": [{"severity": "critical", "description": f"Quality check system error: {str(e)}"}]
            }
    
    def _check_table_quality(self, table_name: str, rules: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check data quality for a specific table."""
        result = {
            "table_name": table_name,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "issues": []
        }
        
        try:
            # For demo purposes, simulate data quality checks
            # In a real implementation, this would query actual database tables
            
            sample_data = self._get_sample_data(table_name)
            
            if not sample_data:
                result["issues"].append({
                    "severity": "warning",
                    "description": f"No data found for table {table_name}",
                    "table": table_name
                })
                result["total_checks"] = 1
                result["failed_checks"] = 1
                return result
            
            df = pd.DataFrame(sample_data)
            
            # Check required fields
            if "required_fields" in rules:
                for field in rules["required_fields"]:
                    result["total_checks"] += 1
                    if field not in df.columns:
                        result["failed_checks"] += 1
                        result["issues"].append({
                            "severity": "critical",
                            "description": f"Missing required field: {field}",
                            "table": table_name,
                            "field": field
                        })
                    else:
                        # Check for null values
                        null_count = df[field].isnull().sum()
                        if null_count > 0:
                            result["failed_checks"] += 1
                            result["issues"].append({
                                "severity": "critical",
                                "description": f"Null values in required field: {field} ({null_count} records)",
                                "table": table_name,
                                "field": field,
                                "count": null_count
                            })
                        else:
                            result["passed_checks"] += 1
            
            # Check numeric fields
            if "numeric_fields" in rules:
                for field in rules["numeric_fields"]:
                    if field in df.columns:
                        result["total_checks"] += 1
                        try:
                            pd.to_numeric(df[field], errors='raise')
                            result["passed_checks"] += 1
                        except:
                            result["failed_checks"] += 1
                            result["issues"].append({
                                "severity": "error",
                                "description": f"Non-numeric values in numeric field: {field}",
                                "table": table_name,
                                "field": field
                            })
            
            # Check positive fields
            if "positive_fields" in rules:
                for field in rules["positive_fields"]:
                    if field in df.columns:
                        result["total_checks"] += 1
                        negative_count = (df[field] < 0).sum()
                        if negative_count > 0:
                            result["failed_checks"] += 1
                            result["issues"].append({
                                "severity": "error",
                                "description": f"Negative values in positive field: {field} ({negative_count} records)",
                                "table": table_name,
                                "field": field,
                                "count": negative_count
                            })
                        else:
                            result["passed_checks"] += 1
            
            # Check unique fields
            if "unique_fields" in rules:
                for field in rules["unique_fields"]:
                    if field in df.columns:
                        result["total_checks"] += 1
                        duplicate_count = df[field].duplicated().sum()
                        if duplicate_count > 0:
                            result["failed_checks"] += 1
                            result["issues"].append({
                                "severity": "error",
                                "description": f"Duplicate values in unique field: {field} ({duplicate_count} duplicates)",
                                "table": table_name,
                                "field": field,
                                "count": duplicate_count
                            })
                        else:
                            result["passed_checks"] += 1
            
        except Exception as e:
            result["issues"].append({
                "severity": "critical",
                "description": f"Error checking table {table_name}: {str(e)}",
                "table": table_name
            })
            result["total_checks"] += 1
            result["failed_checks"] += 1
        
        return result
    
    def _get_sample_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get sample data for quality checks."""
        
        if table_name == "plants":
            return [
                {"plant_id": "PLANT_MUM", "capacity_tonnes": 100000, "initial_inventory": 5000, "safety_stock_tonnes": 2000},
                {"plant_id": "PLANT_DEL", "capacity_tonnes": 80000, "initial_inventory": 3000, "safety_stock_tonnes": 1500},
                {"plant_id": "PLANT_CHE", "capacity_tonnes": 90000, "initial_inventory": 4000, "safety_stock_tonnes": 1800}
            ]
        
        elif table_name == "customers":
            return [
                {"customer_id": "CUST_MUM", "location": "Mumbai"},
                {"customer_id": "CUST_DEL", "location": "Delhi"},
                {"customer_id": "CUST_CHE", "location": "Chennai"},
                {"customer_id": "CUST_PUN", "location": "Pune"}
            ]
        
        elif table_name == "demand":
            return [
                {"customer_id": "CUST_MUM", "period": "2025-01", "demand_tonnes": 25000},
                {"customer_id": "CUST_MUM", "period": "2025-02", "demand_tonnes": 28000},
                {"customer_id": "CUST_DEL", "period": "2025-01", "demand_tonnes": 30000},
                {"customer_id": "CUST_DEL", "period": "2025-02", "demand_tonnes": 32000}
            ]
        
        elif table_name == "routes":
            return [
                {"from": "PLANT_MUM", "to": "CUST_MUM", "mode": "road", "distance_km": 50},
                {"from": "PLANT_MUM", "to": "CUST_PUN", "mode": "road", "distance_km": 150},
                {"from": "PLANT_DEL", "to": "CUST_DEL", "mode": "road", "distance_km": 30}
            ]
        
        return []
    
    def validate_optimization_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optimization input data."""
        try:
            validation_result = {
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Check required top-level keys
            required_keys = ["plants", "customers", "periods", "demand", "costs"]
            for key in required_keys:
                if key not in input_data:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Missing required key: {key}")
            
            # Validate plants data
            if "plants" in input_data:
                plants = input_data["plants"]
                if not isinstance(plants, list) or len(plants) == 0:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Plants data must be a non-empty list")
                else:
                    for i, plant in enumerate(plants):
                        if not isinstance(plant, dict):
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Plant {i} must be a dictionary")
                        elif "plant_id" not in plant:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Plant {i} missing plant_id")
                        elif "capacity_tonnes" not in plant:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Plant {plant.get('plant_id', i)} missing capacity_tonnes")
            
            # Validate customers data
            if "customers" in input_data:
                customers = input_data["customers"]
                if not isinstance(customers, list) or len(customers) == 0:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Customers data must be a non-empty list")
                else:
                    for i, customer in enumerate(customers):
                        if not isinstance(customer, dict):
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Customer {i} must be a dictionary")
                        elif "customer_id" not in customer:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Customer {i} missing customer_id")
            
            # Validate demand data
            if "demand" in input_data:
                demand = input_data["demand"]
                if not isinstance(demand, list) or len(demand) == 0:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Demand data must be a non-empty list")
                else:
                    for i, demand_record in enumerate(demand):
                        if not isinstance(demand_record, dict):
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Demand record {i} must be a dictionary")
                        else:
                            required_demand_fields = ["customer_id", "period", "demand_tonnes"]
                            for field in required_demand_fields:
                                if field not in demand_record:
                                    validation_result["valid"] = False
                                    validation_result["issues"].append(f"Demand record {i} missing {field}")
            
            # Check data consistency
            if "plants" in input_data and "customers" in input_data and "demand" in input_data:
                plant_ids = {p["plant_id"] for p in input_data["plants"] if "plant_id" in p}
                customer_ids = {c["customer_id"] for c in input_data["customers"] if "customer_id" in c}
                demand_customer_ids = {d["customer_id"] for d in input_data["demand"] if "customer_id" in d}
                
                # Check if all demand customers exist
                missing_customers = demand_customer_ids - customer_ids
                if missing_customers:
                    validation_result["warnings"].append(f"Demand references unknown customers: {missing_customers}")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": []
            }