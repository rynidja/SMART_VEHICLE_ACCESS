# Smart Vehicle License Scanner
# Main FastAPI application entry point

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
from loguru import logger

from backend.database import init_db
from backend.routers import plates, cameras, dashboard, auth
from backend.core.config import settings
from backend.core.security import verify_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add("logs/app.log", rotation="1 day", retention="30 days")

# Security scheme
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Initializes database and other resources on startup.
    """
    # Startup
    logger.info("Starting Smart Vehicle License Scanner API...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Smart Vehicle License Scanner API...")

# Create FastAPI application
app = FastAPI(
    title="Smart Vehicle License Scanner API",
    description="Local license plate recognition system for Algerian license plates",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(plates.router, prefix="/api/plates", tags=["License Plates"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    """
    Root endpoint providing API information and health status.
    """
    return {
        "message": "Smart Vehicle License Scanner API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
