"""
AI Resume Analyzer — Scorer Tests

Tests for keyword matching, embedding similarity, rule-based scoring,
and the composite scoring pipeline.
"""

import pytest
from backend.services.scorer import (
    score_keyword_match,
    score_embedding_similarity,
    score_rules,
    score_candidate,
)


class TestKeywordMatch:
    """Test keyword-based skill matching."""

    def test_exact_match(self):
        result = score_keyword_match(
            candidate_skills=["Python", "FastAPI", "Docker"],
            required_skills=["Python", "FastAPI"],
            preferred_skills=["Docker"],
            resume_text="",
        )
        assert result["score"] > 0.9
        assert all(m["matched"] for m in result["matched_required"])

    def test_partial_match(self):
        result = score_keyword_match(
            candidate_skills=["Python"],
            required_skills=["Python", "Java", "Go"],
            preferred_skills=["Docker"],
            resume_text="",
        )
        assert 0 < result["score"] < 1
        matched_count = sum(1 for m in result["matched_required"] if m["matched"])
        assert matched_count == 1

    def test_no_match(self):
        result = score_keyword_match(
            candidate_skills=["Rust", "Haskell"],
            required_skills=["Python", "Java"],
            preferred_skills=["Docker"],
            resume_text="",
        )
        assert result["score"] == 0.0

    def test_resume_text_fallback(self):
        """Skills found in resume text but not in extracted skills list."""
        result = score_keyword_match(
            candidate_skills=[],
            required_skills=["Python"],
            preferred_skills=[],
            resume_text="I have extensive experience with Python development",
        )
        matched = [m for m in result["matched_required"] if m["matched"]]
        assert len(matched) == 1
        assert matched[0]["confidence"] == 0.75

    def test_empty_skills(self):
        result = score_keyword_match(
            candidate_skills=[],
            required_skills=[],
            preferred_skills=[],
            resume_text="",
        )
        assert result["score"] == 0.0

    def test_substring_match(self):
        """Partial substring matching (e.g., 'javascript' matches 'java')."""
        result = score_keyword_match(
            candidate_skills=["javascript"],
            required_skills=["java"],
            preferred_skills=[],
            resume_text="",
        )
        matched = [m for m in result["matched_required"] if m["matched"]]
        assert len(matched) == 1
        assert matched[0]["confidence"] == 0.85


class TestEmbeddingSimilarity:
    """Test embedding-based similarity scoring."""

    def test_similar_texts(self):
        result = score_embedding_similarity(
            resume_text="Experienced Python developer with expertise in FastAPI, REST APIs, and Docker",
            job_description="Looking for a Python developer skilled in FastAPI and containerization",
        )
        assert result["score"] > 0
        assert result["method"] in ("sentence_transformer", "tfidf")

    def test_dissimilar_texts(self):
        result = score_embedding_similarity(
            resume_text="Chef with 10 years experience in French cuisine and pastry making",
            job_description="Looking for a Python developer skilled in FastAPI and Docker",
        )
        # Dissimilar texts should score lower
        assert result["score"] < 0.8

    def test_empty_text(self):
        result = score_embedding_similarity(
            resume_text="",
            job_description="",
        )
        # Should handle gracefully
        assert "score" in result
        assert "method" in result


class TestRulesScoring:
    """Test rule-based scoring (experience + education)."""

    def test_senior_with_enough_experience(self):
        result = score_rules(
            experience_data={"total_years": 8},
            education_data=[{"level": "masters"}],
            job_experience_level="senior",
        )
        assert result["score"] > 0.5
        assert result["experience_match"]["match"] is True

    def test_junior_with_little_experience(self):
        result = score_rules(
            experience_data={"total_years": 1},
            education_data=[{"level": "bachelors"}],
            job_experience_level="junior",
        )
        assert result["score"] > 0
        assert result["experience_match"]["match"] is True

    def test_insufficient_experience(self):
        result = score_rules(
            experience_data={"total_years": 1},
            education_data=[],
            job_experience_level="senior",
        )
        assert result["experience_match"]["match"] is False

    def test_no_experience_level(self):
        result = score_rules(
            experience_data={"total_years": 3},
            education_data=[{"level": "bachelors"}],
            job_experience_level=None,
        )
        # Should still score positively
        assert result["score"] > 0

    def test_doctorate_education(self):
        result = score_rules(
            experience_data={},
            education_data=[{"level": "doctorate"}],
            job_experience_level=None,
        )
        assert result["education_match"]["highest_level"] == "doctorate"


class TestScoreCandidate:
    """Test the composite scoring pipeline."""

    def test_full_scoring_pipeline(self):
        result = score_candidate(
            resume_text="Senior Python developer with 8 years of experience in FastAPI, Docker, Kubernetes, and AWS.",
            candidate_skills=["Python", "FastAPI", "Docker", "Kubernetes", "AWS"],
            experience_data={"total_years": 8},
            education_data=[{"level": "masters"}],
            job_description="Looking for a senior Python developer with FastAPI and cloud experience.",
            required_skills=["Python", "FastAPI", "Docker"],
            preferred_skills=["AWS", "Kubernetes"],
            job_experience_level="senior",
        )

        assert "overall_score" in result
        assert "shortlisted" in result
        assert "component_scores" in result
        assert "skill_match_detail" in result
        assert 0 <= result["overall_score"] <= 1

    def test_weak_candidate(self):
        result = score_candidate(
            resume_text="Junior web developer familiar with HTML and CSS.",
            candidate_skills=["HTML", "CSS"],
            experience_data={"total_years": 0},
            education_data=[],
            job_description="Looking for a senior Python developer with machine learning expertise.",
            required_skills=["Python", "Machine Learning", "TensorFlow"],
            preferred_skills=["Docker", "AWS"],
            job_experience_level="senior",
        )

        assert result["overall_score"] < 0.5
        assert result["shortlisted"] is False

    def test_scoring_method_is_set(self):
        result = score_candidate(
            resume_text="Python developer",
            candidate_skills=["Python"],
            experience_data={},
            education_data=[],
            job_description="Need Python dev",
            required_skills=["Python"],
            preferred_skills=[],
        )
        assert "scoring_method" in result
