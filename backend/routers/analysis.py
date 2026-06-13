"""
AI Resume Analyzer — Analysis Router

Endpoints for resume improvement recommendations, skill gap analysis, and ATS scoring.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import Candidate, Job, User
from backend.schemas import (
    ResumeImprovementResponse,
    EvaluationResponse,
    AnalysisEvaluateRequest,
    SkillGapResponse,
    ATSScoreResponse,
)
from backend.services.analyzer import (
    analyze_resume_improvement,
    analyze_skill_gap,
    calculate_ats_score,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/improve", response_model=ResumeImprovementResponse)
async def improve_resume(
    job_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI improvement suggestions for the logged-in candidate's resume.
    Can optionally be contextualized to a target Job ID.
    """
    # Find candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Please upload a resume first.",
        )

    if not candidate.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No parsed resume text available. Please upload a resume first.",
        )

    # Fetch job description if job_id is provided
    job_desc = None
    if job_id:
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if job:
            job_desc = job.description

    try:
        suggestions = await analyze_resume_improvement(
            resume_text=candidate.extracted_text,
            job_description=job_desc,
        )
        return suggestions
    except Exception as e:
        logger.error("Resume improvement endpoint failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/analysis/evaluate", response_model=EvaluationResponse)
async def evaluate_against_job(
    request: AnalysisEvaluateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform a skill gap analysis and compute detailed ATS scores
    for the candidate's resume against a targeted job description.
    """
    # Find candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Please upload a resume first.",
        )

    if not candidate.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No parsed resume text available. Please upload a resume first.",
        )

    # Find job
    job_result = await db.execute(select(Job).where(Job.id == request.job_id))
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target job not found.",
        )

    try:
        # 1. Skill Gap Analysis
        skill_gap_result = analyze_skill_gap(
            candidate_skills=candidate.extracted_skills or [],
            required_skills=job.required_skills or [],
            preferred_skills=job.preferred_skills or [],
        )

        # 2. ATS Score Calculation
        ats_score_result = calculate_ats_score(
            candidate_skills=candidate.extracted_skills or [],
            experience_data=candidate.extracted_experience or {},
            education_data=candidate.extracted_education or [],
            resume_text=candidate.extracted_text or "",
            job_description=job.description or "",
            required_skills=job.required_skills or [],
            preferred_skills=job.preferred_skills or [],
            job_experience_level=job.experience_level,
        )

        return EvaluationResponse(
            job_id=job.id,
            job_title=job.title,
            skill_gap=SkillGapResponse(**skill_gap_result),
            ats_score=ATSScoreResponse(**ats_score_result),
        )

    except Exception as e:
        logger.error("Job evaluation endpoint failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )
