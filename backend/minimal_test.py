#!/usr/bin/env python3
"""
Minimal test to find what's causing the hang.
"""
import sys
import time

def test_step(step_name, import_func):
    print(f"Testing {step_name}...", end="", flush=True)
    start_time = time.time()
    try:
        import_func()
        elapsed = time.time() - start_time
        print(f" ✅ ({elapsed:.2f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f" ❌ ({elapsed:.2f}s): {e}")
        return False

def test_basic_imports():
    test_step("FastAPI", lambda: __import__('fastapi'))
    test_step("SQLAlchemy", lambda: __import__('sqlalchemy'))
    test_step("Pydantic", lambda: __import__('pydantic'))

def test_app_imports():
    test_step("app.core.config", lambda: __import__('app.core.config'))
    test_step("app.db.session", lambda: __import__('app.db.session'))
    test_step("app.core.deps", lambda: __import__('app.core.deps'))

def test_route_imports():
    test_step("app.api.v1.routes_health", lambda: __import__('app.api.v1.routes_health'))
    test_step("app.api.v1.routes_dashboard_demo", lambda: __import__('app.api.v1.routes_dashboard_demo'))

if __name__ == "__main__":
    print("🔍 Running minimal import tests...")
    print("=" * 50)
    
    print("\n1. Basic library imports:")
    test_basic_imports()
    
    print("\n2. App core imports:")
    test_app_imports()
    
    print("\n3. Route imports:")
    test_route_imports()
    
    print("\n4. Full app import:")
    test_step("app.main", lambda: __import__('app.main'))
    
    print("=" * 50)
    print("Test completed!")