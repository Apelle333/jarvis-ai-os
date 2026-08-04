"""
JARVIS Main Entry Point
Main application entry point for the JARVIS AI Operating System
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from core.brain import JARVIS_Brain
from api.websocket import router as websocket_router, system_snapshot_broadcast_loop
from api.chat import router as chat_router
from api.voice import router as voice_router
from api.system import router as system_router
from api.dependencies import set_brain

# Base directory of the backend
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure the logs directory exists
os.makedirs(os.path.join(BACKEND_DIR, "logs"), exist_ok=True)

# Configure logging
_handlers = [
    logging.FileHandler(os.path.join(BACKEND_DIR, "logs", "jarvis.log")),
]
if sys.stdout is not None:
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=_handlers
)
logger = logging.getLogger(__name__)

# Global brain instance
brain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global brain
    # Startup
    logger.info("Starting JARVIS AI Operating System...")
    brain = JARVIS_Brain()
    await brain.initialize()
    set_brain(brain)
    broadcast_task = asyncio.create_task(
        system_snapshot_broadcast_loop(brain)
    )
    logger.info("JARVIS AI Operating System started successfully")

    yield

    # Shutdown
    logger.info("Shutting down JARVIS AI Operating System...")
    broadcast_task.cancel()
    if brain:
        await brain.shutdown()
    logger.info("JARVIS AI Operating System stopped")


# Create FastAPI app
app = FastAPI(
    title="JARVIS AI Operating System",
    description="An autonomous personal AI operating system",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://tauri.localhost",
        "tauri://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "JARVIS AI"}

# Mount static files (for frontend) - registered last so it does not shadow routes
_frontend_dir = os.path.join(BACKEND_DIR, "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="static")


if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )