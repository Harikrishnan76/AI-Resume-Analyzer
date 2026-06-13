"""
AI Resume Analyzer — Analyzer Tests

Tests for resume improvement analysis, skill gap matching, and ATS score calculations.
"""

import pytest
from backend.services.analyzer import (
    analyze_skill_gap,
    calculate_ats_score,
    _get_fallback_improvement_suggestions,
)


class TestSkillGapAnalysis:
    """Test skill gap analysis comparison logic."""

    def test_all_matched(self):
        result = analyze_skill_gap(
            candidate_skills=["Python", "FastAPI", "Docker"],
            required_skills=["Python", "FastAPI"],
            preferred_skills=["Docker"],
        )
        assert len(result["missing_required"]) == 0
        assert len(result["missing_preferred"]) == 0
        assert len(result["matched_required"]) == 2
        assert "Python" in result["matched_required"]
        assert "FastAPI" in result["matched_required"]

    def test_partial_and_missing(self):
        result = analyze_skill_gap(
            candidate_skills=["Python", "SQL"],
            required_skills=["Python", "FastAPI", "Docker"],
            preferred_skills=["Kubernetes"],
        )
        assert "Python" in result["matched_required"]
        assert "FastAPI" in result["missing_required"]
        assert "Docker" in result["missing_required"]
        assert "Kubernetes" in result["missing_preferred"]


class TestATSScoreCalculation:
    """Test ATS scoring math and ranges."""

    def test_ideal_candidate(self):
        scores = calculate_ats_score(
            candidate_skills=["Python", "FastAPI", "Docker", "SQL"],
            experience_data={"total_years": 6},
            education_data=[{"level": "masters"}],
            resume_text="Senior Python Developer. Email: test@candidate.com, Phone: 123-456-7890. Experience with FastAPI and SQL. Summary: experienced software engineer. Skills: Python, FastAPI, Docker, SQL. Education: Masters in CS.",
            job_description="Senior Python Developer experienced in FastAPI and Docker.",
            required_skills=["Python", "FastAPI"],
            preferred_skills=["Docker"],
            job_experience_level="senior",
        )

        assert scores["overall_score"] > 80.0
        assert scores["formatting_score"] == 100.0  # has email, phone, sections, no weak verbs
        assert scores["experience_score"] == 100.0  # meets senior experience + master education

    def test_poor_candidate(self):
        scores = calculate_ats_score(
            candidate_skills=["HTML"],
            experience_data={"total_years": 0},
            education_data=[],
            resume_text="Just HTML.",
            job_description="Senior Python Developer experienced in FastAPI and Docker.",
            required_skills=["Python", "FastAPI"],
            preferred_skills=["Docker"],
            job_experience_level="senior",
        )

        assert scores["overall_score"] < 50.0
        assert scores["formatting_score"] < 60.0  # missing contact details and sections


class TestFallbackImprovementSuggestions:
    """Test the rule-based suggestions generator."""

    def test_empty_resume(self):
        res = _get_fallback_improvement_suggestions("")
        assert len(res["weak_sections"]) > 0
        assert len(res["formatting_suggestions"]) > 0

    def test_resume_missing_summary(self):
        res = _get_fallback_improvement_suggestions("Experience: Worked at Google. Education: BS. Skills: coding.")
        # Summary should be identified as weak/missing
        summary_issues = [w for w in res["weak_sections"] if "summary" in w["section"].lower()]
        assert len(summary_issues) == 1
