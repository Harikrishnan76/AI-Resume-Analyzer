"""
AI Resume Analyzer — Scoring Router

Run scoring for candidates against jobs, view ranked results.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import require_admin, get_current_user
from backend.database import get_db
from backend.models import Candidate, Job, Score, User
from backend.schemas import (
    ScoreDetailResponse,
    ScoreResultItem,
    ScoringResultsResponse,
    ScoringRunRequest,
)
from backend.services.scorer import score_candidate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scoring/run", response_model=ScoringResultsResponse)
async def run_scoring(
    data: ScoringRunRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Run scoring for ALL candidates against a specific job.
    Scores each candidate's extracted resume data against the job requirements.
    Returns ranked shortlist. Admin only.
    """
    # Fetch job
    result = await db.execute(select(Job).where(Job.id == data.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch all candidates with parsed resumes
    result = await db.execute(
        select(Candidate).where(Candidate.extracted_text.isnot(None))
    )
    candidates = result.scalars().all()

    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="No candidates with parsed resumes found. Upload resumes first.",
        )

    # Delete existing scores for this job (re-scoring)
    existing = await db.execute(
        select(Score).where(Score.job_id == data.job_id)
    )
    for old_score in existing.scalars().all():
        await db.delete(old_score)
    await db.flush()

    # Score each candidate
    scored_results = []
    for candidate in candidates:
        try:
            result_data = score_candidate(
                resume_text=candidate.extracted_text or "",
                candidate_skills=candidate.extracted_skills or [],
                experience_data=candidate.extracted_experience or {},
                education_data=candidate.extracted_education or [],
                job_description=job.description,
                required_skills=job.required_skills or [],
                preferred_skills=job.preferred_skills or [],
                job_experience_level=job.experience_level,
            )

            # Build explanation text
            explanation_parts = []
            comp = result_data.get("component_scores", {})
            explanation_parts.append(
                f"Keyword match: {comp.get('keyword', 0):.0%}"
            )
            explanation_parts.append(
                f"Semantic similarity ({comp.get('embedding_method', 'n/a')}): {comp.get('embedding', 0):.0%}"
            )
            explanation_parts.append(
                f"Rules check: {comp.get('rules', 0):.0%}"
            )

            matched_skills = [
                s["skill"] for s in result_data.get("skill_match_detail", []) if s.get("matched")
            ]
            if matched_skills:
                explanation_parts.append(f"Matched skills: {', '.join(matched_skills[:10])}")

            exp_match = result_data.get("experience_match", {})
            if exp_match.get("match"):
                explanation_parts.append(
                    f"Experience: {exp_match.get('candidate_years', 0)} years (meets {exp_match.get('required', 'any')} requirement)"
                )

            explanation = " | ".join(explanation_parts)

            # Create score record
            score = Score(
                candidate_id=candidate.id,
                job_id=job.id,
                overall_score=result_data["overall_score"],
                skill_match_detail=result_data.get("skill_match_detail"),
                experience_match=result_data.get("experience_match"),
                education_match=result_data.get("education_match"),
                explanation=explanation,
                scoring_method=result_data.get("scoring_method", "hybrid"),
                shortlisted=result_data["shortlisted"],
            )
            db.add(score)
            await db.flush()

            scored_results.append((score, candidate))
            logger.info(
                "Scored candidate %d for job %d: %.4f (%s)",
                candidate.id, job.id, result_data["overall_score"],
                "shortlisted" if result_data["shortlisted"] else "not shortlisted",
            )

        except Exception as e:
            logger.error("Scoring failed for candidate %d: %s", candidate.id, e)
            continue

    # Sort by score descending
    scored_results.sort(key=lambda x: x[0].overall_score, reverse=True)

    # Build response
    result_items = []
    for rank, (score, candidate) in enumerate(scored_results, 1):
        result_items.append(
            ScoreResultItem(
                rank=rank,
                score_id=score.id,
                candidate_id=candidate.id,
                candidate_name=candidate.full_name,
                candidate_email=candidate.email,
                overall_score=score.overall_score,
                skill_match_detail=score.skill_match_detail,
                experience_match=score.experience_match,
                education_match=score.education_match,
                explanation=score.explanation or "",
                shortlisted=score.shortlisted,
                scored_at=score.scored_at,
            )
        )

    shortlisted_count = sum(1 for s, _ in scored_results if s.shortlisted)

    return ScoringResultsResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates=len(scored_results),
        shortlisted_count=shortlisted_count,
        results=result_items,
        scored_at=datetime.now(timezone.utc),
    )


@router.get("/scoring/results/{job_id}", response_model=ScoringResultsResponse)
async def get_scoring_results(
    job_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get existing scoring results for a job (admin only)."""
    # Fetch job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch scores with candidate data
    result = await db.execute(
        select(Score, Candidate)
        .join(Candidate, Score.candidate_id == Candidate.id)
        .where(Score.job_id == job_id)
        .order_by(Score.overall_score.desc())
    )
    rows = result.all()

    if not rows:
        return ScoringResultsResponse(
            job_id=job.id,
            job_title=job.title,
            total_candidates=0,
            shortlisted_count=0,
            results=[],
        )

    result_items = []
    for rank, (score, candidate) in enumerate(rows, 1):
        result_items.append(
            ScoreResultItem(
                rank=rank,
                score_id=score.id,
                candidate_id=candidate.id,
                candidate_name=candidate.full_name,
                candidate_email=candidate.email,
                overall_score=score.overall_score,
                skill_match_detail=score.skill_match_detail,
                experience_match=score.experience_match,
                education_match=score.education_match,
                explanation=score.explanation or "",
                shortlisted=score.shortlisted,
                scored_at=score.scored_at,
            )
        )

    shortlisted_count = sum(1 for s, _ in rows if s.shortlisted)

    return ScoringResultsResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates=len(rows),
        shortlisted_count=shortlisted_count,
        results=result_items,
        scored_at=rows[0][0].scored_at if rows else None,
    )


@router.get("/scoring/detail/{score_id}", response_model=ScoreDetailResponse)
async def get_score_detail(
    score_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed score breakdown for a single score record."""
    result = await db.execute(select(Score).where(Score.id == score_id))
    score = result.scalar_one_or_none()

    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")

    return score
