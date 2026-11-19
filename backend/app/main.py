import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all models are registered
from app.services.notification_service import notification_service

# Routers
from app.routers import (
    auth, profile, subjects, topics, exams, plans, progress, ai, revision, notifications
)

# APScheduler instance
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is created if not in testing mode
    if os.getenv("TESTING") != "true":
        Base.metadata.create_all(bind=engine)
        try:
            scheduler.add_job(
                notification_service.run_scheduled_checks,
                "interval",
                minutes=30,
                id="notification_checks",
                replace_existing=True
            )
            scheduler.start()
            notification_service.run_scheduled_checks()
        except Exception as e:
            print(f"APScheduler startup notice: {e}")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent AI-powered study planning and academic productivity management platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(subjects.router, prefix=settings.API_V1_STR)
app.include_router(topics.router, prefix=settings.API_V1_STR)
app.include_router(exams.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(progress.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(revision.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

# Also mount under root paths for direct API access if requested
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(subjects.router)
app.include_router(topics.router)
app.include_router(exams.router)
app.include_router(plans.router)
app.include_router(progress.router)
app.include_router(ai.router)
app.include_router(revision.router)
app.include_router(notifications.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "ai_enabled": bool(settings.OPENAI_API_KEY)
    }

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to AI Study Planner API",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
