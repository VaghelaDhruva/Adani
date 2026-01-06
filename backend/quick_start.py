#!/usr/bin/env python3
"""
Quick start script using the virtual environment directly.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # No reload to avoid file watching issues
        log_level="info"
    )