"""
AI Resume Analyzer — Parser Tests

Tests for resume text extraction, skill extraction, experience parsing,
and education parsing.
"""

import pytest
from backend.services.parser import (
    extract_skills,
    extract_experience,
    extract_education,
    extract_contact_info,
    extract_structured,
)


# ── Sample resume text for testing ──
SAMPLE_RESUME = """
John Doe
Email: john.doe@example.com
Phone: (555) 012-0199

PROFESSIONAL SUMMARY
Senior software engineer with 8+ years of experience in Python, Java, and cloud technologies.

SKILLS
Python, FastAPI, Django, Java, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, CI/CD, REST, Agile

EXPERIENCE
Senior Engineer — MegaCorp
Jan 2020 - Present
- Led backend team of 5 engineers
- Deployed microservices on Kubernetes

Software Engineer — TechStartup
Mar 2016 - Dec 2019
- Built REST APIs with Django
- Managed PostgreSQL databases

EDUCATION
Master of Science in Computer Science — MIT, 2016
Bachelor of Science in Computer Engineering — UCLA, 2014
"""


class TestExtractSkills:
    """Test skill extraction from resume text."""

    def test_finds_known_skills(self):
        skills = extract_skills(SAMPLE_RESUME)
        skills_lower = [s.lower() for s in skills]
        assert "python" in skills_lower
        assert "docker" in skills_lower
        assert "kubernetes" in skills_lower

    def test_finds_framework_skills(self):
        skills = extract_skills(SAMPLE_RESUME)
        skills_lower = [s.lower() for s in skills]
        assert "fastapi" in skills_lower
        assert "django" in skills_lower

    def test_finds_cloud_skills(self):
        skills = extract_skills(SAMPLE_RESUME)
        skills_lower = [s.lower() for s in skills]
        assert "aws" in skills_lower

    def test_empty_text_returns_empty(self):
        skills = extract_skills("")
        assert skills == []

    def test_no_skills_returns_empty(self):
        skills = extract_skills("This is a text with no technical skills mentioned.")
        assert len(skills) == 0

    def test_returns_sorted_unique(self):
        skills = extract_skills("Python python PYTHON FastAPI fastapi")
        # Should be deduplicated
        skills_lower = [s.lower() for s in skills]
        assert len(set(skills_lower)) == len(skills)


class TestExtractExperience:
    """Test experience extraction from resume text."""

    def test_finds_years_of_experience(self):
        result = extract_experience(SAMPLE_RESUME)
        assert isinstance(result, dict)
        assert result["total_years"] >= 8

    def test_finds_date_ranges(self):
        result = extract_experience(SAMPLE_RESUME)
        entries = result.get("entries", [])
        assert len(entries) >= 1

    def test_empty_text(self):
        result = extract_experience("")
        assert result["total_years"] == 0
        assert result["entries"] == []

    def test_no_experience_mentioned(self):
        result = extract_experience("Hello world, this has no experience info.")
        assert result["total_years"] == 0


class TestExtractEducation:
    """Test education extraction from resume text."""

    def test_finds_education(self):
        education = extract_education(SAMPLE_RESUME)
        assert len(education) >= 1

    def test_finds_degree_level(self):
        education = extract_education(SAMPLE_RESUME)
        levels = [e.get("level") for e in education if "level" in e]
        assert "masters" in levels or "bachelors" in levels

    def test_empty_text(self):
        education = extract_education("")
        assert education == []


class TestExtractContactInfo:
    """Test contact info extraction."""

    def test_finds_email(self):
        contact = extract_contact_info(SAMPLE_RESUME)
        assert contact["email"] == "john.doe@example.com"

    def test_finds_phone(self):
        contact = extract_contact_info(SAMPLE_RESUME)
        assert contact["phone"] is not None

    def test_no_contact_info(self):
        contact = extract_contact_info("No contact info here.")
        assert contact["email"] is None
        assert contact["phone"] is None


class TestExtractStructured:
    """Test the full structured extraction pipeline."""

    def test_returns_all_fields(self):
        result = extract_structured(SAMPLE_RESUME)
        assert "skills" in result
        assert "experience" in result
        assert "education" in result
        assert "contact" in result

    def test_skills_not_empty(self):
        result = extract_structured(SAMPLE_RESUME)
        assert len(result["skills"]) > 0

    def test_empty_text(self):
        result = extract_structured("")
        assert result["skills"] == []
        assert result["experience"]["total_years"] == 0
        assert result["education"] == []
        assert result["contact"]["email"] is None
