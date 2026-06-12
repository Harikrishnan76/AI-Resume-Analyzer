"""
AI Resume Analyzer — Candidates Router

Handles resume upload, parsing, and candidate profile management.
"""

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth import get_current_user, require_admin
from backend.config import settings
from backend.database import get_db
from backend.models import Candidate, ParseStatus, Resume, User, UserRole
from backend.schemas import CandidateListItem, CandidateResponse, ResumeResponse
from backend.services.llm_extractor import extract_with_llm
from backend.services.parser import extract_structured, parse_resume

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def _validate_upload(file: UploadFile) -> str:
    """Validate uploaded file type and size. Returns file extension."""
    # Check by extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Only PDF and DOCX are accepted.",
        )

    # Check content type if available
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        # Some clients send wrong content types, so we also accept by extension
        logger.warning("Unexpected content type %s for %s", file.content_type, file.filename)

    return suffix.lstrip(".")


@router.post("/candidates/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file. Parses text, extracts structured data
    (skills, experience, education) using LLM + traditional parsing.
    """
    file_ext = _validate_upload(file)

    # Get or verify candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    candidate = result.scalar_one_or_none()

    if candidate is None:
        # Auto-create candidate profile if user is a candidate
        if user.role == UserRole.candidate:
            candidate = Candidate(
                user_id=user.id,
                full_name=user.username,
                email=user.email,
            )
            db.add(candidate)
            await db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin users cannot upload resumes. Use a candidate account.",
            )

    # Save file to disk
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = settings.upload_path / unique_name

    try:
        content = await file.read()
        file_size = len(content)

        # Check file size
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
            )

        with open(file_path, "wb") as f:
            f.write(content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("File save failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Create resume record
    resume = Resume(
        candidate_id=candidate.id,
        filename=file.filename or "unknown",
        file_path=str(file_path),
        file_type=file_ext,
        file_size_bytes=file_size,
        parse_status=ParseStatus.pending,
    )
    db.add(resume)
    await db.flush()

    # Parse resume text
    try:
        raw_text = parse_resume(str(file_path))

        if not raw_text:
            resume.parse_status = ParseStatus.failed
            await db.flush()
            await db.refresh(resume)
            return resume

        # Try LLM-assisted extraction first
        llm_result = await extract_with_llm(raw_text)

        if llm_result:
            # Use LLM results
            candidate.extracted_text = raw_text
            candidate.extracted_skills = llm_result.get("skills", [])
            candidate.extracted_experience = llm_result.get("experience", {})
            candidate.extracted_education = llm_result.get("education", [])
            if llm_result.get("full_name"):
                candidate.full_name = llm_result["full_name"]
            if llm_result.get("contact", {}).get("phone"):
                candidate.phone = llm_result["contact"]["phone"]
            logger.info("Used LLM extraction for candidate %d", candidate.id)
        else:
            # Fallback to traditional extraction
            structured = extract_structured(raw_text)
            candidate.extracted_text = raw_text
            candidate.extracted_skills = structured.get("skills", [])
            candidate.extracted_experience = structured.get("experience", {})
            candidate.extracted_education = structured.get("education", [])
            if structured.get("contact", {}).get("phone"):
                candidate.phone = structured["contact"]["phone"]
            logger.info("Used traditional extraction for candidate %d", candidate.id)

        resume.parse_status = ParseStatus.parsed

    except Exception as e:
        logger.error("Parsing failed for resume %d: %s", resume.id, e)
        resume.parse_status = ParseStatus.failed

    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("/candidates/me", response_model=CandidateResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current candidate's profile with extracted data."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    candidate = result.scalar_one_or_none()

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    return candidate


@router.get("/candidates/", response_model=list[CandidateListItem])
async def list_candidates(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all candidates (admin only)."""
    result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.resumes))
        .order_by(Candidate.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    candidates = result.scalars().all()

    return [
        CandidateListItem(
            id=c.id,
            full_name=c.full_name,
            email=c.email,
            skills_count=len(c.extracted_skills) if c.extracted_skills else 0,
            resume_count=len(c.resumes),
            created_at=c.created_at,
        )
        for c in candidates
    ]


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a candidate's full profile (admin only)."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return candidate


@router.get("/candidates/{candidate_id}/resumes", response_model=list[ResumeResponse])
async def list_candidate_resumes(
    candidate_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all resumes for a candidate."""
    # Candidates can only view their own; admins can view any
    if user.role != UserRole.admin:
        result = await db.execute(
            select(Candidate).where(Candidate.user_id == user.id)
        )
        own_candidate = result.scalar_one_or_none()
        if not own_candidate or own_candidate.id != candidate_id:
            raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Resume)
        .where(Resume.candidate_id == candidate_id)
        .order_by(Resume.uploaded_at.desc())
    )
    return result.scalars().all()
