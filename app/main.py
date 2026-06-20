from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import members, books, borrowings, auth
from app.db.database import engine
from app.models import models
from app.core.logging import setup_logging, get_logger
from app.core.middleware import LoggingMiddleware
import os

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)
logger = get_logger(__name__)

# Create database tables (skip in test mode with SQLite in memory)
if not os.getenv("DATABASE_URL", "").startswith("sqlite:///:memory:"):
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neighborhood Library API",
    description="A library management system for tracking books, members, and borrowing operations",
    version="2.0.0"
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(books.router)
app.include_router(borrowings.router)

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Neighborhood Library API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": ["JWT Authentication", "Structured Logging"]
    }

@app.get("/health")
def health_check():
    logger.info("Health check")
    return {"status": "healthy"}
