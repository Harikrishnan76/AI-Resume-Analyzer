"""
AI Resume Analyzer — Pydantic Schemas

Request/response models for all API endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ──────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)
    role: str = Field(default="candidate", pattern="^(candidate|admin)$")
    full_name: str = Field(default="", max_length=255)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Candidate / Resume Schemas
# ──────────────────────────────────────────────

class CandidateResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    extracted_skills: Optional[list] = None
    extracted_experience: Optional[dict | list] = None
    extracted_education: Optional[list] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateListItem(BaseModel):
    id: int
    full_name: str
    email: str
    skills_count: int = 0
    resume_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    parse_status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Job Schemas
# ──────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_level: Optional[str] = Field(
        default=None, pattern="^(junior|mid|senior)$"
    )


class JobUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    experience_level: Optional[str] = Field(
        default=None, pattern="^(junior|mid|senior)$"
    )
    status: Optional[str] = Field(default=None, pattern="^(active|closed)$")


class JobResponse(BaseModel):
    id: int
    created_by: int
    title: str
    description: str
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    experience_level: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Scoring Schemas
# ──────────────────────────────────────────────

class ScoringRunRequest(BaseModel):
    job_id: int


class SkillMatchDetail(BaseModel):
    skill: str
    matched: bool
    confidence: float = 0.0
    source: str = ""  # "keyword" | "embedding" | "both"


class ScoreResultItem(BaseModel):
    rank: int
    score_id: int
    candidate_id: int
    candidate_name: str
    candidate_email: str
    overall_score: float
    skill_match_detail: Optional[list[dict]] = None
    experience_match: Optional[dict] = None
    education_match: Optional[dict] = None
    explanation: str = ""
    shortlisted: bool = False
    scored_at: datetime

    class Config:
        from_attributes = True


class ScoringResultsResponse(BaseModel):
    job_id: int
    job_title: str
    total_candidates: int
    shortlisted_count: int
    results: list[ScoreResultItem]
    scored_at: Optional[datetime] = None


class ScoreDetailResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    overall_score: float
    skill_match_detail: Optional[list[dict]] = None
    experience_match: Optional[dict] = None
    education_match: Optional[dict] = None
    explanation: str = ""
    scoring_method: str
    shortlisted: bool
    scored_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Email Schemas
# ──────────────────────────────────────────────

class EmailSendRequest(BaseModel):
    candidate_ids: list[int]
    job_id: int
    template: str = Field(..., pattern="^(shortlist|rejection)$")
    custom_message: str = ""


class EmailLogResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: Optional[int] = None
    template_name: str
    recipient_email: str
    subject: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailSendResponse(BaseModel):
    total: int
    sent: int
    failed: int
    details: list[EmailLogResponse]
