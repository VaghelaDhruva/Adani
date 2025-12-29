#!/usr/bin/env python3
"""
Install additional packages required for optimization.
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    """Install all required optimization packages."""
    
    packages = [
        "pyomo>=6.7.0",
        "highspy>=1.6.0",  # HiGHS solver
        "pandas>=2.1.4",
        "numpy>=1.24.0"
    ]
    
    print("Installing optimization packages...")
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\nInstallation complete: {success_count}/{len(packages)} packages installed successfully")
    
    if success_count == len(packages):
        print("✓ All packages installed successfully!")
        print("\nYou can now run optimizations using:")
        print("  python3 init_db.py")
        print("  python3 load_sample_data.py")
        print("  python3 -m uvicorn app.main:app --reload")
    else:
        print("⚠ Some packages failed to install. Please check the errors above.")

if __name__ == "__main__":
    main()