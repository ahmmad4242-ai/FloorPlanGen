"""
Minimal FastAPI app for Railway testing
"""
from fastapi import FastAPI
import os

app = FastAPI(title="FloorPlanGen Generator (Minimal)")

@app.get("/")
def root():
    return {
        "service": "FloorPlanGen Generator",
        "version": "1.0.0-minimal",
        "status": "healthy",
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "FloorPlanGen Generator Service (Minimal)",
        "version": "1.0.0",
        "port": os.getenv("PORT"),
        "message": "Minimal version without dependencies"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
