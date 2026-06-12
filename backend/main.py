"""
AI Resume Analyzer — FastAPI Application Entry Point

Configures CORS, lifespan events, and mounts all routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting %s", settings.app_name)
    await init_db()
    logger.info("✅ Database initialized")

    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("📁 Upload directory: %s", settings.upload_path.resolve())

    if settings.llm_enabled:
        logger.info("🤖 LLM-assisted extraction: ENABLED (model: %s)", settings.openai_model)
    else:
        logger.info("🤖 LLM-assisted extraction: DISABLED (no API key)")

    yield

    logger.info("🛑 Shutting down %s", settings.app_name)


# ── Create FastAPI app ──
app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered resume screening and scoring system. "
        "Upload resumes, define job requirements, and get ranked candidate shortlists "
        "with explainable scoring."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
from backend.routers import candidates, jobs, scoring, emails  # noqa: E402

app.include_router(candidates.router, prefix="/api", tags=["Candidates & Resumes"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(scoring.router, prefix="/api", tags=["Scoring"])
app.include_router(emails.router, prefix="/api", tags=["Emails"])


# ── Health check ──
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "llm_enabled": settings.llm_enabled,
    }


# ── Auth endpoints (inline for simplicity) ──
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User, UserRole, Candidate
from backend.schemas import UserRegister, UserLogin, Token, UserResponse
from backend.auth import (
    hash_password, verify_password, create_access_token, get_current_user
)


@app.post("/api/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username or email already exists
    existing = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    await db.flush()

    # Auto-create candidate profile for candidate users
    if user.role == UserRole.candidate:
        candidate = Candidate(
            user_id=user.id,
            full_name=data.full_name or data.username,
            email=data.email,
        )
        db.add(candidate)

    await db.flush()
    await db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=Token, tags=["Auth"])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive a JWT token."""
    from fastapi import HTTPException

    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)


@app.get("/api/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return user
