"""
Data Cleaning Service

Implements comprehensive data cleaning and normalization before optimization.
Ensures all data is in consistent format with proper units and data types.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Comprehensive data cleaning service."""
    
    def __init__(self):
        self.cleaning_log = []
        
    def clean_all_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Clean all data tables."""
        
        cleaned_data = {}
        self.cleaning_log = []
        
        logger.info("Starting comprehensive data cleaning")
        
        # Clean each table
        for table_name, df in raw_data.items():
            if df is not None and not df.empty:
                cleaned_data[table_name] = self._clean_table(table_name, df.copy())
            else:
                cleaned_data[table_name] = df
        
        logger.info(f"Data cleaning completed. Applied {len(self.cleaning_log)} transformations")
        return cleaned_data
    
    def _clean_table(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Clean a specific table."""
        
        original_rows = len(df)
        
        # Apply general cleaning
        df = self._clean_strings(df)
        df = self._clean_numeric_columns(df)
        df = self._standardize_ids(df)
        df = self._handle_missing_values(df, table_name)
        
        # Apply table-specific cleaning
        if table_name == "plants_df":
            df = self._clean_plants_data(df)
        elif table_name == "demand_df":
            df = self._clean_demand_data(df)
        elif table_name == "routes_df":
            df = self._clean_routes_data(df)
        elif table_name == "production_df":
            df = self._clean_production_data(df)
        elif table_name == "inventory_df":
            df = self._clean_inventory_data(df)
        elif table_name == "safety_stock_df":
            df = self._clean_safety_stock_data(df)
        
        # Remove duplicates
        df = self._remove_duplicates(df, table_name)
        
        final_rows = len(df)
        if final_rows != original_rows:
            self.cleaning_log.append({
                "table": table_name,
                "transformation": "row_count_change",
                "original_rows": original_rows,
                "final_rows": final_rows,
                "change": final_rows - original_rows
            })
        
        return df
    
    def _clean_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean string columns."""
        
        for col in df.select_dtypes(include=['object']).columns:
            # Remove leading/trailing whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Replace multiple spaces with single space
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            
            # Handle empty strings
            df[col] = df[col].replace('', np.nan)
            df[col] = df[col].replace('nan', np.nan)
        
        return df
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean numeric columns."""
        
        numeric_patterns = [
            'capacity', 'demand', 'cost', 'distance', 'inventory', 
            'stock', 'tonnes', 'km', 'price', 'rate'
        ]
        
        for col in df.columns:
            # Check if column should be numeric
            if any(pattern in col.lower() for pattern in numeric_patterns):
                # Convert to numeric, handling errors
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Handle negative values where they shouldn't exist
                if any(pattern in col.lower() for pattern in ['capacity', 'demand', 'distance', 'inventory']):
                    negative_count = (df[col] < 0).sum()
                    if negative_count > 0:
                        self.cleaning_log.append({
                            "table": "unknown",
                            "column": col,
                            "transformation": "negative_values_set_to_zero",
                            "count": negative_count
                        })
                        df[col] = df[col].clip(lower=0)
        
        return df
    
    def _standardize_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize ID columns."""
        
        id_columns = [col for col in df.columns if 'id' in col.lower()]
        
        for col in id_columns:
            if col in df.columns:
                # Convert to string and uppercase
                df[col] = df[col].astype(str).str.upper().str.strip()
                
                # Remove special characters except underscore
                df[col] = df[col].str.replace(r'[^A-Z0-9_]', '', regex=True)
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Handle missing values based on business rules."""
        
        # Define default values for critical columns
        defaults = {
            "plants_df": {
                "plant_type": "grinding",
                "region": "unknown",
                "country": "India"
            },
            "demand_df": {
                "demand_tonnes": 0,
                "priority_level": "normal"
            },
            "routes_df": {
                "transport_mode": "road",
                "vehicle_capacity_tonnes": 25
            },
            "production_df": {
                "min_run_level": 0.3,
                "variable_cost_per_tonne": 1700
            }
        }
        
        if table_name in defaults:
            for col, default_value in defaults[table_name].items():
                if col in df.columns:
                    missing_count = df[col].isna().sum()
                    if missing_count > 0:
                        df[col] = df[col].fillna(default_value)
                        self.cleaning_log.append({
                            "table": table_name,
                            "column": col,
                            "transformation": "missing_values_filled",
                            "count": missing_count,
                            "default_value": default_value
                        })
        
        return df
    
    def _clean_plants_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean plant master data."""
        
        # Standardize plant types
        if "plant_type" in df.columns:
            type_mapping = {
                "clinker": "clinker",
                "grinding": "grinding", 
                "terminal": "terminal",
                "cement": "grinding",
                "warehouse": "terminal"
            }
            
            df["plant_type"] = df["plant_type"].str.lower().map(type_mapping).fillna("grinding")
        
        # Validate coordinates
        if "latitude" in df.columns and "longitude" in df.columns:
            # India bounds approximately
            df.loc[(df["latitude"] < 6) | (df["latitude"] > 38), "latitude"] = np.nan
            df.loc[(df["longitude"] < 68) | (df["longitude"] > 98), "longitude"] = np.nan
        
        return df
    
    def _clean_demand_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean demand forecast data."""
        
        # Standardize period format
        if "period" in df.columns:
            df["period"] = self._standardize_period_format(df["period"])
        
        # Handle extreme demand values
        if "demand_tonnes" in df.columns:
            # Cap extremely high demand (likely data entry errors)
            high_threshold = df["demand_tonnes"].quantile(0.99) * 3
            extreme_high = df["demand_tonnes"] > high_threshold
            if extreme_high.any():
                self.cleaning_log.append({
                    "table": "demand_forecast",
                    "transformation": "extreme_high_demand_capped",
                    "count": extreme_high.sum(),
                    "threshold": high_threshold
                })
                df.loc[extreme_high, "demand_tonnes"] = high_threshold
        
        return df
    
    def _clean_routes_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean transport routes data."""
        
        # Standardize transport modes
        if "transport_mode" in df.columns:
            mode_mapping = {
                "truck": "road",
                "lorry": "road", 
                "road": "road",
                "train": "rail",
                "railway": "rail",
                "rail": "rail",
                "ship": "sea",
                "sea": "sea",
                "pipeline": "pipeline"
            }
            
            df["transport_mode"] = df["transport_mode"].str.lower().map(mode_mapping).fillna("road")
        
        # Validate distance values
        if "distance_km" in df.columns:
            # Cap unrealistic distances (> 5000 km within India)
            extreme_distance = df["distance_km"] > 5000
            if extreme_distance.any():
                self.cleaning_log.append({
                    "table": "transport_routes_modes",
                    "transformation": "extreme_distance_capped",
                    "count": extreme_distance.sum()
                })
                df.loc[extreme_distance, "distance_km"] = 5000
        
        # Calculate missing cost_per_tonne_km if we have cost_per_tonne and distance
        if ("cost_per_tonne_km" not in df.columns or df["cost_per_tonne_km"].isna().any()) and \
           "cost_per_tonne" in df.columns and "distance_km" in df.columns:
            
            missing_mask = df["cost_per_tonne_km"].isna() if "cost_per_tonne_km" in df.columns else True
            df.loc[missing_mask, "cost_per_tonne_km"] = df.loc[missing_mask, "cost_per_tonne"] / df.loc[missing_mask, "distance_km"]
        
        return df
    
    def _clean_production_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean production capacity data."""
        
        # Standardize period format
        if "period" in df.columns:
            df["period"] = self._standardize_period_format(df["period"])
        
        # Ensure min_capacity <= max_capacity
        if "min_capacity_tonnes" in df.columns and "max_capacity_tonnes" in df.columns:
            invalid_capacity = df["min_capacity_tonnes"] > df["max_capacity_tonnes"]
            if invalid_capacity.any():
                self.cleaning_log.append({
                    "table": "production_capacity_cost",
                    "transformation": "min_capacity_adjusted",
                    "count": invalid_capacity.sum()
                })
                df.loc[invalid_capacity, "min_capacity_tonnes"] = df.loc[invalid_capacity, "max_capacity_tonnes"] * 0.3
        
        return df
    
    def _clean_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean inventory data."""
        
        # Standardize period format
        if "period" in df.columns:
            df["period"] = self._standardize_period_format(df["period"])
        
        return df
    
    def _clean_safety_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean safety stock data."""
        
        # Ensure safety stock is reasonable (not more than 90 days of average demand)
        if "safety_stock_tonnes" in df.columns:
            # This is a simplified check - in practice you'd compare with actual demand
            high_threshold = 50000  # 50K tonnes seems high for safety stock
            extreme_high = df["safety_stock_tonnes"] > high_threshold
            if extreme_high.any():
                self.cleaning_log.append({
                    "table": "safety_stock_policy",
                    "transformation": "extreme_safety_stock_capped",
                    "count": extreme_high.sum()
                })
                df.loc[extreme_high, "safety_stock_tonnes"] = high_threshold
        
        return df
    
    def _standardize_period_format(self, period_series: pd.Series) -> pd.Series:
        """Standardize period format to YYYY-MM."""
        
        def clean_period(period_str):
            if pd.isna(period_str):
                return period_str
            
            period_str = str(period_str).strip()
            
            # Handle YYYY-MM format
            if re.match(r'^\d{4}-\d{2}$', period_str):
                return period_str
            
            # Handle YYYY/MM format
            if re.match(r'^\d{4}/\d{2}$', period_str):
                return period_str.replace('/', '-')
            
            # Handle YYYYMM format
            if re.match(r'^\d{6}$', period_str):
                return f"{period_str[:4]}-{period_str[4:]}"
            
            # Handle Mon YYYY format
            month_mapping = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            for month_name, month_num in month_mapping.items():
                if month_name in period_str.lower():
                    year_match = re.search(r'\d{4}', period_str)
                    if year_match:
                        return f"{year_match.group()}-{month_num}"
            
            # Default: return as-is
            return period_str
        
        return period_series.apply(clean_period)
    
    def _remove_duplicates(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Remove duplicate records based on business keys."""
        
        # Define business keys for each table
        business_keys = {
            "plants_df": ["plant_id"],
            "demand_df": ["customer_node_id", "period"],
            "routes_df": ["origin_plant_id", "destination_node_id", "transport_mode"],
            "production_df": ["plant_id", "period"],
            "inventory_df": ["node_id", "period"],
            "safety_stock_df": ["node_id"]
        }
        
        if table_name in business_keys:
            key_columns = business_keys[table_name]
            # Only check for duplicates if all key columns exist
            if all(col in df.columns for col in key_columns):
                original_count = len(df)
                df = df.drop_duplicates(subset=key_columns, keep='first')
                final_count = len(df)
                
                if final_count != original_count:
                    self.cleaning_log.append({
                        "table": table_name,
                        "transformation": "duplicates_removed",
                        "original_count": original_count,
                        "final_count": final_count,
                        "duplicates_removed": original_count - final_count
                    })
        
        return df
    
    def get_cleaning_report(self) -> Dict[str, Any]:
        """Get comprehensive cleaning report."""
        
        return {
            "transformations_applied": len(self.cleaning_log),
            "cleaning_log": self.cleaning_log,
            "timestamp": datetime.utcnow().isoformat()
        }