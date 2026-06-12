"""
AI Resume Analyzer — Jobs Router

CRUD operations for job descriptions. Admin-only write access.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import get_current_user, require_admin
from backend.database import get_db
from backend.models import Job, JobStatus, User
from backend.schemas import JobCreate, JobResponse, JobUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/jobs/", response_model=JobResponse, status_code=201)
async def create_job(
    data: JobCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job description (admin only)."""
    job = Job(
        created_by=user.id,
        title=data.title,
        description=data.description,
        required_skills=data.required_skills,
        preferred_skills=data.preferred_skills,
        experience_level=data.experience_level,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    logger.info("Job created: %s (id=%d) by user %d", job.title, job.id, user.id)
    return job


@router.get("/jobs/", response_model=list[JobResponse])
async def list_jobs(
    status_filter: str = Query(None, alias="status", pattern="^(active|closed)$"),
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all jobs. Optionally filter by status.
    Both candidates and admins can view jobs.
    """
    query = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)

    if status_filter:
        query = query.where(Job.status == JobStatus(status_filter))

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a job description by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    data: JobUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a job description (admin only)."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Apply partial updates
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(job, field, JobStatus(value))
        else:
            setattr(job, field, value)

    await db.flush()
    await db.refresh(job)
    logger.info("Job updated: %s (id=%d)", job.title, job.id)
    return job


@router.delete("/jobs/{job_id}", status_code=200)
async def close_job(
    job_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-close a job (set status to closed). Does not delete data.
    Admin only.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job.status = JobStatus.closed
    await db.flush()
    logger.info("Job closed: %s (id=%d)", job.title, job.id)
    return {"message": f"Job '{job.title}' has been closed", "job_id": job.id}
