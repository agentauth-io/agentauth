#!/usr/bin/env python3
"""
Railway-compatible server startup script.
Properly reads PORT from environment and starts uvicorn.
"""
import os
import sys

# Get port from environment (Railway sets this)
port = int(os.environ.get("PORT", 8000))

print(f"Starting AgentAuth on port {port}...")

# Start uvicorn programmatically
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
