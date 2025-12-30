from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .core.config import settings
from .core.database import init_db
from .routers import user, student, teacher, admin
from .auth.router import auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create upload directories
    os.makedirs("uploads/avatars", exist_ok=True)
    os.makedirs("uploads/justifications", exist_ok=True)
    os.makedirs("uploads/bulk", exist_ok=True)
    
    yield
    
    # Shutdown: clean up resources
    logger.info("Shutting down")

app = FastAPI(
    title="Attendance Management System API",
    description="API for managing student attendance with role-based access",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "detail": str(exc)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "detail": exc.detail
        }
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user.router, prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(teacher.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Attendance Management System API",
        "version": "2.0.0",
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
