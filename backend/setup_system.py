#!/usr/bin/env python3
"""
Complete system setup script.
Sets up database, loads sample data, and runs a test optimization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from init_db import init_db
from load_sample_data import load_sample_data
from sqlalchemy.orm import sessionmaker
from app.db.session import engine
from app.services.optimization_service import OptimizationService

def run_test_optimization():
    """Run a test optimization to verify the system works."""
    
    print("\n" + "="*50)
    print("RUNNING TEST OPTIMIZATION")
    print("="*50)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        optimization_service = OptimizationService(db)
        
        print("Starting test optimization for 'base' scenario...")
        run_id = optimization_service.run_optimization(
            scenario_name="base",
            solver_name="HiGHS",
            time_limit=60,  # Short time limit for testing
            mip_gap=0.05,   # Relaxed gap for faster solving
            scenario_parameters={"demand_multiplier": 1.0, "capacity_multiplier": 1.0}
        )
        
        print(f"✓ Test optimization completed successfully!")
        print(f"  Run ID: {run_id}")
        
        # Get KPI data
        kpi_data = optimization_service.get_kpi_data("base")
        if kpi_data:
            print(f"  Total Cost: ₹{kpi_data['total_cost']:,.2f}")
            print(f"  Service Level: {kpi_data['service_performance']['service_level']:.1%}")
            print(f"  Production Utilization: {len(kpi_data['production_utilization'])} plants")
            print(f"  Transport Routes: {len(kpi_data['transport_utilization'])} routes")
        
        return True
        
    except Exception as e:
        print(f"✗ Test optimization failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Run complete system setup."""
    
    print("SUPPLY CHAIN OPTIMIZATION SYSTEM SETUP")
    print("="*50)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Step 2: Load sample data
    print("\n2. Loading sample data...")
    try:
        load_sample_data()
        print("✓ Sample data loaded successfully")
    except Exception as e:
        print(f"✗ Sample data loading failed: {e}")
        return False
    
    # Step 3: Run test optimization
    print("\n3. Running test optimization...")
    try:
        success = run_test_optimization()
        if not success:
            return False
    except Exception as e:
        print(f"✗ Test optimization setup failed: {e}")
        return False
    
    # Success message
    print("\n" + "="*50)
    print("✓ SYSTEM SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nYour supply chain optimization system is ready!")
    print("\nNext steps:")
    print("1. Start the backend server:")
    print("   python3 -m uvicorn app.main:app --reload")
    print("\n2. Start the frontend dashboard:")
    print("   cd ../frontend")
    print("   streamlit run streamlit_app/main.py")
    print("\n3. Open your browser to:")
    print("   Backend API: http://localhost:8000")
    print("   Frontend Dashboard: http://localhost:8501")
    print("\n4. Try the KPI Dashboard with real calculated data!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)