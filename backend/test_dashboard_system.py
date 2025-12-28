"""
Simple test script to verify the dashboard system components work correctly.
Run this to test the core functionality without requiring a full database setup.
"""

import sys
import os
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_data_health_service():
    """Test data health service components."""
    print("🧪 Testing Data Health Service...")
    
    try:
        from app.services.data_health_service import DataHealthStatus
        
        # Test DataHealthStatus class
        status = DataHealthStatus(
            table_name="test_table",
            record_count=100,
            validation_status="PASS",
            missing_key_fields=0,
            referential_integrity_issues=0
        )
        
        status_dict = status.to_dict()
        assert status_dict["table_name"] == "test_table"
        assert status_dict["record_count"] == 100
        assert status_dict["validation_status"] == "PASS"
        
        print("✅ DataHealthStatus class works correctly")
        
    except Exception as e:
        print(f"❌ Data Health Service test failed: {e}")
        return False
    
    return True

def test_data_validation_service():
    """Test data validation service components."""
    print("🧪 Testing Data Validation Service...")
    
    try:
        from app.services.data_validation_service import ValidationResult
        
        # Test ValidationResult class
        result = ValidationResult(
            stage="test_stage",
            status="PASS",
            errors=[],
            warnings=[],
            row_level_errors=[]
        )
        
        result_dict = result.to_dict()
        assert result_dict["stage"] == "test_stage"
        assert result_dict["status"] == "PASS"
        assert result_dict["error_count"] == 0
        
        print("✅ ValidationResult class works correctly")
        
    except Exception as e:
        print(f"❌ Data Validation Service test failed: {e}")
        return False
    
    return True

def test_clean_data_service():
    """Test clean data service components."""
    print("🧪 Testing Clean Data Service...")
    
    try:
        # Test that the module imports correctly
        from app.services import clean_data_service
        
        # Test helper functions exist
        assert hasattr(clean_data_service, 'get_clean_data_for_optimization')
        assert hasattr(clean_data_service, 'get_clean_data_preview')
        assert hasattr(clean_data_service, 'get_all_clean_data_previews')
        
        print("✅ Clean Data Service imports correctly")
        
    except Exception as e:
        print(f"❌ Clean Data Service test failed: {e}")
        return False
    
    return True

def test_dashboard_routes():
    """Test dashboard routes import correctly."""
    print("🧪 Testing Dashboard Routes...")
    
    try:
        from app.api.v1 import routes_dashboard
        
        # Test that the router exists
        assert hasattr(routes_dashboard, 'router')
        
        print("✅ Dashboard Routes import correctly")
        
    except Exception as e:
        print(f"❌ Dashboard Routes test failed: {e}")
        return False
    
    return True

def test_validation_rules():
    """Test validation rules work correctly."""
    print("🧪 Testing Validation Rules...")
    
    try:
        import pandas as pd
        from app.services.validation.rules import reject_negative_demand
        from app.utils.exceptions import DataValidationError
        
        # Test with valid data
        valid_df = pd.DataFrame({
            'customer_node_id': ['CUST_1', 'CUST_2'],
            'period': ['2025-01', '2025-02'],
            'demand_tonnes': [100, 200]
        })
        
        result = reject_negative_demand(valid_df)
        assert len(result) == 2
        
        # Test with invalid data
        invalid_df = pd.DataFrame({
            'customer_node_id': ['CUST_1', 'CUST_2'],
            'period': ['2025-01', '2025-02'],
            'demand_tonnes': [100, -50]  # Negative demand
        })
        
        try:
            reject_negative_demand(invalid_df)
            assert False, "Should have raised DataValidationError"
        except DataValidationError:
            pass  # Expected
        
        print("✅ Validation Rules work correctly")
        
    except Exception as e:
        print(f"❌ Validation Rules test failed: {e}")
        return False
    
    return True

def test_model_builder():
    """Test that model builder imports correctly."""
    print("🧪 Testing Model Builder...")
    
    try:
        from app.services.optimization.model_builder import build_clinker_model
        
        # Test that the function exists and is callable
        assert callable(build_clinker_model)
        
        print("✅ Model Builder imports correctly")
        
    except Exception as e:
        print(f"❌ Model Builder test failed: {e}")
        return False
    
    return True

def test_kpi_calculator():
    """Test KPI calculator with sample data."""
    print("🧪 Testing KPI Calculator...")
    
    try:
        from app.services.kpi_calculator import compute_kpis
        
        # Test with sample data
        costs = {
            "production_cost": 1000.0,
            "transport_cost": 500.0,
            "fixed_trip_cost": 200.0,
            "holding_cost": 100.0
        }
        
        demand = {("CUST_1", "2025-01"): 100.0, ("CUST_2", "2025-01"): 200.0}
        fulfilled = {("CUST_1", "2025-01"): 100.0, ("CUST_2", "2025-01"): 180.0}
        plant_production = {"PLANT_A": 150.0, "PLANT_B": 130.0}
        plant_capacity = {"PLANT_A": 200.0, "PLANT_B": 150.0}
        
        kpis = compute_kpis(
            costs=costs,
            demand=demand,
            fulfilled=fulfilled,
            plant_production=plant_production,
            plant_capacity=plant_capacity
        )
        
        assert "total_cost" in kpis
        assert "service_level" in kpis
        assert "capacity_utilization" in kpis
        assert kpis["total_cost"] == 1800.0
        
        print("✅ KPI Calculator works correctly")
        
    except Exception as e:
        print(f"❌ KPI Calculator test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting Dashboard System Tests...\n")
    
    tests = [
        test_data_health_service,
        test_data_validation_service,
        test_clean_data_service,
        test_dashboard_routes,
        test_validation_rules,
        test_model_builder,
        test_kpi_calculator
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Dashboard system is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)