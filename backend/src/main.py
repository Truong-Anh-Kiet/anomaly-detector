"""FastAPI application initialization and configuration"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from src.config import get_settings
from src.database import init_db
from src.api.websocket import router as websocket_router
from src.api.anomalies import router as anomalies_router
from src.api.audit_logs import router as audit_logs_router
from src.api.users import router as users_router
from src.api.categories import router as categories_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager - run on startup and shutdown"""
    # Startup
    logger.info("Starting Anomaly Detector API...")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Anomaly Detector API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API for Anomaly Detection Dashboard with ML and statistical hybrid detection",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Health check endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "ok", "version": settings.app_version}

    @app.get("/")
    async def root():
        """Root endpoint with API info"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    # Include WebSocket routes
    app.include_router(websocket_router)
    
    # Include API routers
    app.include_router(anomalies_router)
    app.include_router(audit_logs_router)
    app.include_router(users_router)
    app.include_router(categories_router)

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
