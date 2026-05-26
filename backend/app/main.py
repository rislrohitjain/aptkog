import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.api import ingestion, filter, pivot, join, diagnostics

# Set up logging configuration
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("antigravity_backend")

# Initialize FastAPI application
app = FastAPI(
    title="AptKogMatrix Backend",
    description="Data Analytics Engine - Decoupled REST API",
    version="2.0.0"
)

# Configure CORS for Streamlit client requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production, but open for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under both /api and /api/v1 prefixes for client versioning compatibility
for prefix in ["/api", "/api/v1"]:
    app.include_router(ingestion.router, prefix=prefix, tags=["Data Ingestion"])
    app.include_router(filter.router, prefix=prefix, tags=["Universal Filter Engine"])
    app.include_router(pivot.router, prefix=prefix, tags=["Dynamic Pivot Engine"])
    app.include_router(join.router, prefix=prefix, tags=["Vectorized Dataset Builder"])
    app.include_router(diagnostics.router, prefix=prefix, tags=["Infrastructure Diagnostics"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global error handling middleware for formatting exceptions to JSON.
    """
    logger.error(f"Global exception caught on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

@app.get("/")
async def root():
    return {
        "status": "online",
        "engine": "AptKogMatrix Data Analytics Engine",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    logger.info(f"Starting AptKogMatrix Backend on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True if settings.LOG_LEVEL.lower() == "debug" else False
    )
