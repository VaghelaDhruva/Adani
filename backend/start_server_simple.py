#!/usr/bin/env python3
"""
Simple server startup without auto-reload to avoid file watching issues.
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Start server without reload for stability
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable auto-reload for stability
        log_level="info"
    )