#!/usr/bin/env python3
"""
Minimal FastAPI app to test basic functionality.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Clinker Supply Chain Optimization",
    version="1.0.0",
    description="Minimal version for testing"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Minimal backend is running", "status": "ok"}

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "timestamp": "2025-01-05T12:00:00"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)