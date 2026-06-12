"""
AI Resume Analyzer — Emails Router

Trigger templated emails to candidates, view email logs.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import require_admin
from backend.database import get_db
from backend.models import Candidate, EmailLog, EmailStatus, Job, Score, User
from backend.schemas import EmailLogResponse, EmailSendRequest, EmailSendResponse
from backend.services.email_service import send_candidate_email

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/emails/send", response_model=EmailSendResponse)
async def send_emails(
    data: EmailSendRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Send templated emails to selected candidates for a job.
    Supports 'shortlist' and 'rejection' templates. Admin only.
    """
    # Validate job exists
    result = await db.execute(select(Job).where(Job.id == data.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch candidates
    result = await db.execute(
        select(Candidate).where(Candidate.id.in_(data.candidate_ids))
    )
    candidates = {c.id: c for c in result.scalars().all()}

    if not candidates:
        raise HTTPException(status_code=400, detail="No valid candidates found")

    sent_count = 0
    failed_count = 0
    email_logs = []

    for cid in data.candidate_ids:
        candidate = candidates.get(cid)
        if not candidate:
            logger.warning("Candidate %d not found, skipping email", cid)
            continue

        # Get candidate's score for this job (if available)
        score_result = await db.execute(
            select(Score).where(
                Score.candidate_id == cid,
                Score.job_id == data.job_id,
            )
        )
        score_record = score_result.scalar_one_or_none()
        candidate_score = score_record.overall_score if score_record else None

        # Send email
        result = send_candidate_email(
            template_name=data.template,
            candidate_name=candidate.full_name,
            candidate_email=candidate.email,
            job_title=job.title,
            custom_message=data.custom_message,
            score=candidate_score,
        )

        # Log the email
        email_log = EmailLog(
            candidate_id=candidate.id,
            job_id=job.id,
            template_name=data.template,
            recipient_email=candidate.email,
            subject=result.get("subject", ""),
            status=EmailStatus.sent if result["success"] else EmailStatus.failed,
            error_message=result.get("error"),
            sent_at=result.get("sent_at"),
        )
        db.add(email_log)
        await db.flush()
        await db.refresh(email_log)

        if result["success"]:
            sent_count += 1
        else:
            failed_count += 1

        email_logs.append(email_log)
        logger.info(
            "Email %s to %s: %s",
            "sent" if result["success"] else "FAILED",
            candidate.email,
            result.get("error", "OK"),
        )

    return EmailSendResponse(
        total=len(email_logs),
        sent=sent_count,
        failed=failed_count,
        details=[
            EmailLogResponse(
                id=log.id,
                candidate_id=log.candidate_id,
                job_id=log.job_id,
                template_name=log.template_name,
                recipient_email=log.recipient_email,
                subject=log.subject,
                status=log.status.value,
                error_message=log.error_message,
                sent_at=log.sent_at,
            )
            for log in email_logs
        ],
    )


@router.get("/emails/logs", response_model=list[EmailLogResponse])
async def get_email_logs(
    job_id: int = Query(None, description="Filter by job ID"),
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """View email send history (admin only)."""
    query = select(EmailLog).order_by(EmailLog.id.desc()).offset(skip).limit(limit)

    if job_id:
        query = query.where(EmailLog.job_id == job_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        EmailLogResponse(
            id=log.id,
            candidate_id=log.candidate_id,
            job_id=log.job_id,
            template_name=log.template_name,
            recipient_email=log.recipient_email,
            subject=log.subject,
            status=log.status.value,
            error_message=log.error_message,
            sent_at=log.sent_at,
        )
        for log in logs
    ]
