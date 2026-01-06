#!/usr/bin/env python3
"""
Stable server startup script that avoids the auto-reload issues.
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Start server with minimal reload watching
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],  # Only watch the app directory, not .venv
        reload_excludes=[
            "*.pyc",
            "*.pyo", 
            "*.pyd",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "*.log"
        ],
        log_level="info"
    )