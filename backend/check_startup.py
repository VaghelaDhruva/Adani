#!/usr/bin/env python3
"""
Check if the application can start without errors.
"""

import sys
import traceback

print("Checking application startup...")
print("=" * 50)

try:
    print("1. Importing app.main...")
    from app.main import app
    print("   ✓ App imported successfully")
    
    print("\n2. Checking app routes...")
    routes = [r.path for r in app.routes]
    print(f"   ✓ Found {len(routes)} routes")
    
    print("\n3. Testing database connection...")
    from app.db.session import SessionLocal
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("   ✓ Database connection OK")
    
    print("\n" + "=" * 50)
    print("✓ Application startup check PASSED")
    print("=" * 50)
    print("\nYou can start the server with:")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nFull traceback:")
    print("=" * 50)
    traceback.print_exc()
    print("=" * 50)
    sys.exit(1)

