"""
Tests for transport optimization validator.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from app.services.optimization.transport_validator import TransportValidator
from app.utils.exceptions import OptimizationError


class TestTransportValidator:
    """Test cases for TransportValidator."""
    
    @pytest.fixture
    def sample_model_data(self):
        """Sample model data for testing."""
        return {
            "plants": pd.DataFrame([
                {"plant_id": "PLANT_001", "plant_name": "Plant 1", "plant_type": "production"}
            ]),
            "transport_routes_modes": pd.DataFrame([
                {
                    "origin_plant_id": "PLANT_001",
                    "destination_node_id": "CUST_001",
                    "transport_mode": "TRUCK",
                    "distance_km": 100,
                    "cost_per_tonne": 10.0,
                    "fixed_cost_per_trip": 100.0,
                    "vehicle_capacity_tonnes": 20.0,
                    "min_batch_quantity_tonnes": 10.0
                },
                {
                    "origin_plant_id": "PLANT_001",
                    "destination_node_id": "CUST_002",
                    "transport_mode": "RAIL",
                    "distance_km": 200,
                    "cost_per_tonne": 5.0,
                    "fixed_cost_per_trip": 500.0,
                    "vehicle_capacity_tonnes": 50.0,
                    "min_batch_quantity_tonnes": 25.0
                }
            ]),
            "production_capacity_cost": pd.DataFrame([
                {
                    "plant_id": "PLANT_001",
                    "period": "P01",
                    "max_capacity_tonnes": 1000.0,
                    "variable_cost_per_tonne": 50.0
                }
            ]),
            "demand_forecast": pd.DataFrame([
                {
                    "customer_node_id": "CUST_001",
                    "period": "P01",
                    "demand_tonnes": 100.0
                },
                {
                    "customer_node_id": "CUST_002",
                    "period": "P01",
                    "demand_tonnes": 150.0
                }
            ])
        }
    
    @pytest.fixture
    def valid_solution(self):
        """Valid solution for testing."""
        return {
            "shipments": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "tonnes": 100.0
                },
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_002",
                    "mode": "RAIL",
                    "period": "P01",
                    "tonnes": 150.0
                }
            ],
            "trips": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "trips": 5
                },
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_002",
                    "mode": "RAIL",
                    "period": "P01",
                    "trips": 3
                }
            ],
            "production": [
                {
                    "plant": "PLANT_001",
                    "period": "P01",
                    "tonnes": 250.0
                }
            ],
            "costs": {
                "production_cost": 12500.0,  # 250 × 50
                "transport_cost": 1750.0,     # 100 × 10 + 150 × 5
                "fixed_trip_cost": 2000.0,   # 5 × 100 + 3 × 500
                "holding_cost": 0.0
            }
        }
    
    @pytest.fixture
    def invalid_solution(self):
        """Invalid solution with SBQ violations."""
        return {
            "shipments": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "tonnes": 5.0  # Below SBQ of 10
                }
            ],
            "trips": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "trips": 1
                }
            ],
            "production": [
                {
                    "plant": "PLANT_001",
                    "period": "P01",
                    "tonnes": 5.0
                }
            ],
            "costs": {
                "production_cost": 250.0,
                "transport_cost": 50.0,
                "fixed_trip_cost": 100.0,
                "holding_cost": 0.0
            }
        }
    
    def test_validator_initialization(self, sample_model_data, valid_solution):
        """Test validator initialization."""
        validator = TransportValidator(sample_model_data, valid_solution)
        assert validator.model_data == sample_model_data
        assert validator.solution == valid_solution
        assert validator.validation_results == {}
    
    def test_validate_solution_success(self, sample_model_data, valid_solution):
        """Test successful validation."""
        validator = TransportValidator(sample_model_data, valid_solution)
        results = validator.validate_solution()
        
        # Debug output
        print(f"Overall status: {results['overall_status']}")
        for key, value in results.items():
            if key != 'overall_status' and isinstance(value, dict) and 'passed' in value:
                print(f"{key}: passed={value['passed']}")
                if not value['passed']:
                    print(f"  Issues: {value.get('issues', [])}")
        
        assert results["overall_status"] == "passed"
        assert results["sbq_feasibility"]["passed"] == True
        assert results["integer_trip_consistency"]["passed"] == True
        assert results["capacity_constraints"]["passed"] == True
        assert results["cost_consistency"]["passed"] == True
    
    def test_validate_sbq_violations(self, sample_model_data, invalid_solution):
        """Test SBQ violation detection."""
        validator = TransportValidator(sample_model_data, invalid_solution)
        results = validator.validate_solution()
        
        assert results["overall_status"] == "failed"
        assert results["sbq_feasibility"]["passed"] == False
        assert len(results["sbq_feasibility"]["issues"]) > 0
        
        # Check specific issue
        issue = results["sbq_feasibility"]["issues"][0]
        assert "Shipment 5.00 < SBQ 10.00" in issue["issue"]
    
    def test_validate_integer_trips(self, sample_model_data):
        """Test integer trip validation."""
        # Solution with non-integer trips
        invalid_trips_solution = {
            "shipments": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "tonnes": 100.0
                }
            ],
            "trips": [
                {
                    "origin": "PLANT_001",
                    "destination": "CUST_001",
                    "mode": "TRUCK",
                    "period": "P01",
                    "trips": 5.5  # Non-integer
                }
            ]
        }
        
        validator = TransportValidator(sample_model_data, invalid_trips_solution)
        results = validator.validate_solution()
        
        assert results["overall_status"] == "failed"
        assert results["integer_trip_consistency"]["passed"] == False
        assert len(results["integer_trip_consistency"]["issues"]) > 0
    
    def test_validate_capacity_violations(self, sample_model_data):
        """Test capacity violation detection."""
        # Solution with production exceeding capacity
        over_capacity_solution = {
            "production": [
                {
                    "plant": "PLANT_001",
                    "period": "P01",
                    "tonnes": 1500.0  # Exceeds capacity of 1000
                }
            ],
            "shipments": [],
            "trips": []
        }
        
        validator = TransportValidator(sample_model_data, over_capacity_solution)
        results = validator.validate_solution()
        
        assert results["overall_status"] == "failed"
        assert results["capacity_constraints"]["passed"] == False
        assert len(results["capacity_constraints"]["issues"]) > 0
    
    def test_detect_infeasible_routes(self, sample_model_data):
        """Test infeasible route detection."""
        # Add infeasible route to model data
        infeasible_routes = sample_model_data["transport_routes_modes"].copy()
        infeasible_routes.loc[len(infeasible_routes)] = {
            "origin_plant_id": "PLANT_001",
            "destination_node_id": "CUST_003",
            "transport_mode": "TRUCK",
            "distance_km": 50,
            "cost_per_tonne": 10.0,
            "fixed_cost_per_trip": 100.0,
            "vehicle_capacity_tonnes": 20.0,
            "min_batch_quantity_tonnes": 25.0  # SBQ > capacity
        }
        
        sample_model_data["transport_routes_modes"] = infeasible_routes
        
        validator = TransportValidator(sample_model_data, {"shipments": [], "trips": []})
        results = validator.validate_solution()
        
        infeasible_result = results["infeasible_routes"]
        assert infeasible_result["total_infeasible"] > 0
        
        # Find the infeasible route
        infeasible_route = None
        for route in infeasible_result["infeasible_routes"]:
            if "SBQ 25.0 > vehicle capacity 20.0" in str(route["issues"]):
                infeasible_route = route
                break
        
        assert infeasible_route is not None
    
    def test_suggest_fixes(self, sample_model_data, invalid_solution):
        """Test fix suggestions."""
        validator = TransportValidator(sample_model_data, invalid_solution)
        validator.validate_solution()
        
        fixes = validator.suggest_fixes()
        assert len(fixes) > 0
        
        # Check that fixes contain relevant suggestions
        fix_types = [fix["type"] for fix in fixes]
        assert "sbq_adjustment" in fix_types
    
    def test_cost_consistency_validation(self, sample_model_data, valid_solution):
        """Test cost consistency validation."""
        validator = TransportValidator(sample_model_data, valid_solution)
        results = validator.validate_solution()
        
        cost_result = results["cost_consistency"]
        assert cost_result["passed"] == True
        
        # Check that recalculated costs match
        assert "solution_costs" in cost_result
        assert "recalculated_costs" in cost_result


if __name__ == "__main__":
    pytest.main([__file__])
