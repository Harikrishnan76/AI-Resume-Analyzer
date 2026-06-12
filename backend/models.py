"""
AI Resume Analyzer — ORM Models

SQLAlchemy models for: User, Candidate, Resume, Job, Score, EmailLog.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    candidate = "candidate"
    admin = "admin"


class ParseStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    failed = "failed"


class JobStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class EmailStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    failed = "failed"


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.candidate, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="user", uselist=False)
    jobs_created = relationship("Job", back_populates="created_by_user")


# ──────────────────────────────────────────────
# Candidate
# ──────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    extracted_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, nullable=True)       # List of skill strings
    extracted_experience = Column(JSON, nullable=True)   # Structured experience data
    extracted_education = Column(JSON, nullable=True)    # Structured education data
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="candidate")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="candidate")


# ──────────────────────────────────────────────
# Resume
# ──────────────────────────────────────────────

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    file_size_bytes = Column(Integer, nullable=False)
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.pending, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")


# ──────────────────────────────────────────────
# Job
# ──────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)    # List of skill strings
    preferred_skills = Column(JSON, nullable=True)   # List of skill strings
    experience_level = Column(String(50), nullable=True)  # junior, mid, senior
    status = Column(Enum(JobStatus), default=JobStatus.active, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="jobs_created")
    scores = relationship("Score", back_populates="job", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="job")


# ──────────────────────────────────────────────
# Score
# ──────────────────────────────────────────────

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_match_detail = Column(JSON, nullable=True)  # Per-skill match info
    experience_match = Column(JSON, nullable=True)
    education_match = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    scoring_method = Column(String(50), default="hybrid")
    shortlisted = Column(Boolean, default=False)
    scored_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="scores")
    job = relationship("Job", back_populates="scores")


# ──────────────────────────────────────────────
# Email Log
# ──────────────────────────────────────────────

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    template_name = Column(String(100), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    status = Column(Enum(EmailStatus), default=EmailStatus.queued, nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="email_logs")
    job = relationship("Job", back_populates="email_logs")
