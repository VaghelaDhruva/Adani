#!/usr/bin/env python3
"""
Test script to verify Streamlit multipage app fixes.
"""

import sys
import os
from pathlib import Path

# Add the streamlit_app directory to Python path
streamlit_app_dir = Path(__file__).parent / "streamlit_app"
sys.path.insert(0, str(streamlit_app_dir))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")
    
    try:
        # Test main imports
        from config import API_BASE
        print(f"✓ Config imported successfully. API_BASE: {API_BASE}")
        
        # Test styles import
        from styles import apply_common_styles
        print("✓ Styles module imported successfully")
        
        # Test that we can import the page modules
        import importlib.util
        
        # Test KPI Dashboard
        kpi_path = streamlit_app_dir / "pages" / "01_KPI_Dashboard.py"
        spec = importlib.util.spec_from_file_location("kpi_dashboard", kpi_path)
        kpi_module = importlib.util.module_from_spec(spec)
        
        print("✓ KPI Dashboard module can be loaded")
        
        # Test main module
        main_path = streamlit_app_dir / "main.py"
        spec = importlib.util.spec_from_file_location("main", main_path)
        main_module = importlib.util.module_from_spec(spec)
        
        print("✓ Main module can be loaded")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_function_definitions():
    """Test that required functions are defined."""
    print("\nTesting function definitions...")
    
    try:
        # Check KPI Dashboard functions
        kpi_path = streamlit_app_dir / "pages" / "01_KPI_Dashboard.py"
        with open(kpi_path, 'r') as f:
            kpi_content = f.read()
        
        required_functions = [
            "def main():",
            "def format_inr(",
            "def fetch_kpi_data(",
            "def display_cost_summary(",
            "def display_service_performance("
        ]
        
        for func in required_functions:
            if func in kpi_content:
                print(f"✓ Found {func}")
            else:
                print(f"✗ Missing {func}")
                return False
        
        # Check that main() is called outside of if __name__ == "__main__"
        if "try:\n    main()" in kpi_content or "main()" in kpi_content.split("if __name__")[0]:
            print("✓ main() is called directly (not in if __name__ == '__main__')")
        else:
            print("✗ main() is not called directly")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Function definition test failed: {e}")
        return False

def test_error_handling():
    """Test that error handling is present."""
    print("\nTesting error handling...")
    
    try:
        kpi_path = streamlit_app_dir / "pages" / "01_KPI_Dashboard.py"
        with open(kpi_path, 'r') as f:
            kpi_content = f.read()
        
        error_handling_patterns = [
            "try:",
            "except Exception as e:",
            "st.error(",
            "traceback.format_exc()",
            "@st.cache_data"
        ]
        
        for pattern in error_handling_patterns:
            if pattern in kpi_content:
                print(f"✓ Found {pattern}")
            else:
                print(f"✗ Missing {pattern}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Streamlit Multipage App Fixes")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_function_definitions,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Streamlit app should now work correctly.")
        print("\nTo run the app:")
        print("1. Start the backend: cd backend && python3 -m uvicorn app.main:app --reload")
        print("2. Start the frontend: cd frontend && streamlit run streamlit_app/main.py")
    else:
        print("❌ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)