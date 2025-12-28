"""
Simplified test script to verify core dashboard components work.
This test doesn't require database connections or full environment setup.
"""

import sys
import os
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set minimal environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["BROKER_URL"] = "redis://localhost:6379"
os.environ["RESULT_BACKEND"] = "redis://localhost:6379"

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

def test_core_imports():
    """Test that core modules import correctly."""
    print("🧪 Testing Core Imports...")
    
    try:
        # Test config
        from app.core.config import get_settings
        settings = get_settings()
        assert settings.PROJECT_NAME == "Clinker Supply Chain Optimization"
        
        # Test security
        from app.core.security import create_access_token, verify_token
        token = create_access_token({"sub": "testuser"})
        assert isinstance(token, str)
        
        # Test RBAC
        from app.core.rbac import Role, Permission, role_has_permission
        assert role_has_permission(Role.ADMIN, Permission.READ_DATA)
        
        print("✅ Core modules import correctly")
        
    except Exception as e:
        print(f"❌ Core imports test failed: {e}")
        return False
    
    return True

def test_data_models():
    """Test that data models are defined correctly."""
    print("🧪 Testing Data Models...")
    
    try:
        from app.db.models.plant_master import PlantMaster
        from app.db.models.demand_forecast import DemandForecast
        from app.db.models.transport_routes_modes import TransportRoutesModes
        
        # Test that models have the expected table names
        assert PlantMaster.__tablename__ == "plant_master"
        assert DemandForecast.__tablename__ == "demand_forecast"
        assert TransportRoutesModes.__tablename__ == "transport_routes_modes"
        
        print("✅ Data models are defined correctly")
        
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False
    
    return True

def test_schemas():
    """Test that Pydantic schemas work correctly."""
    print("🧪 Testing Pydantic Schemas...")
    
    try:
        from app.schemas.plant import PlantMasterCreate
        from app.schemas.demand import DemandForecastCreate
        
        # Test plant schema
        plant_data = {
            "plant_id": "PLANT_001",
            "plant_name": "Test Plant",
            "plant_type": "clinker"
        }
        plant = PlantMasterCreate(**plant_data)
        assert plant.plant_id == "PLANT_001"
        
        # Test demand schema
        demand_data = {
            "customer_node_id": "CUST_001",
            "period": "2025-01",
            "demand_tonnes": 1000.0
        }
        demand = DemandForecastCreate(**demand_data)
        assert demand.demand_tonnes == 1000.0
        
        print("✅ Pydantic schemas work correctly")
        
    except Exception as e:
        print(f"❌ Schemas test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting Simplified Dashboard System Tests...\n")
    
    tests = [
        test_core_imports,
        test_data_models,
        test_schemas,
        test_data_health_service,
        test_data_validation_service,
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
        print("🎉 All tests passed! Dashboard system core components are working.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)