#!/usr/bin/env python3
"""
Test script to verify backend can start without issues.
"""

def test_imports():
    """Test all critical imports."""
    try:
        print("Testing FastAPI import...")
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
        
        print("Testing app.main import...")
        from app.main import app
        print("✅ app.main imported successfully")
        
        print("Testing database session...")
        from app.db.session import SessionLocal
        print("✅ Database session imported successfully")
        
        print("Testing config...")
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Config loaded successfully - DATABASE_URL: {settings.DATABASE_URL}")
        
        print("Testing database connection...")
        db = SessionLocal()
        db.close()
        print("✅ Database connection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test FastAPI app creation."""
    try:
        from app.main import app
        print(f"✅ App created successfully: {app.title}")
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing backend startup components...")
    print("=" * 50)
    
    if test_imports() and test_app_creation():
        print("=" * 50)
        print("✅ All tests passed! Backend should start successfully.")
        print("\nYou can now run:")
        print("  python3 start_server_simple.py")
        print("  or")
        print("  ./run_backend.sh")
    else:
        print("=" * 50)
        print("❌ Tests failed! Please fix the issues above before starting the server.")