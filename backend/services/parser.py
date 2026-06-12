"""
AI Resume Analyzer — Resume Parser Service

Handles PDF and DOCX text extraction with structured data extraction
using spaCy NER and regex patterns.
"""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Common skill keywords for matching ──
COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    # Web Frameworks
    "react", "angular", "vue", "vue.js", "next.js", "nextjs", "django",
    "flask", "fastapi", "express", "spring", "rails", "laravel", "svelte",
    # Data / ML
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "spark", "hadoop", "airflow", "dbt", "mlflow", "huggingface",
    "machine learning", "deep learning", "nlp", "computer vision",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "sqlite", "oracle",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "ci/cd", "github actions", "gitlab ci",
    # Tools & Practices
    "git", "linux", "agile", "scrum", "rest", "graphql", "microservices",
    "api", "html", "css", "node.js", "nodejs",
}

# ── Regex patterns for structured extraction ──
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)
EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "ph.d", "doctorate", "mba", "b.s.", "m.s.",
    "b.sc", "m.sc", "b.tech", "m.tech", "b.e.", "m.e.", "bca", "mca",
    "associate", "diploma", "certification", "certificate",
    "computer science", "engineering", "information technology",
    "data science", "mathematics", "statistics", "physics",
]
EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?",
    re.IGNORECASE,
)


def parse_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    Primary: PyMuPDF (fitz). Fallback: pdfplumber.
    """
    text = ""

    # Try PyMuPDF first
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        if text.strip():
            logger.info("PDF parsed with PyMuPDF: %s (%d chars)", file_path, len(text))
            return text.strip()
    except Exception as e:
        logger.warning("PyMuPDF failed for %s: %s", file_path, e)

    # Fallback to pdfplumber
    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            logger.info("PDF parsed with pdfplumber: %s (%d chars)", file_path, len(text))
            return text.strip()
    except Exception as e:
        logger.warning("pdfplumber failed for %s: %s", file_path, e)

    logger.error("All PDF parsers failed for %s", file_path)
    return text.strip()


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        logger.info("DOCX parsed: %s (%d chars)", file_path, len(text))
        return text.strip()
    except Exception as e:
        logger.error("DOCX parsing failed for %s: %s", file_path, e)
        return ""


def parse_resume(file_path: str) -> str:
    """
    Parse a resume file (PDF or DOCX) and return raw text.
    Dispatches to the appropriate parser based on file extension.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Only PDF and DOCX are supported.")


def extract_contact_info(text: str) -> dict:
    """Extract email and phone from resume text."""
    emails = EMAIL_PATTERN.findall(text)
    phones = PHONE_PATTERN.findall(text)
    return {
        "email": emails[0] if emails else None,
        "phone": phones[0].strip() if phones else None,
    }


def extract_skills(text: str) -> list[str]:
    """
    Extract skills from resume text using keyword matching.
    Returns a list of matched skills, case-preserved.
    """
    text_lower = text.lower()
    found_skills = []

    for skill in COMMON_SKILLS:
        # Use word boundary matching for short skills to avoid false positives
        if len(skill) <= 2:
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_lower):
                found_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
        elif skill in text_lower:
            # Capitalize properly
            found_skills.append(skill.title() if " " in skill else skill)

    return sorted(set(found_skills))


def extract_experience(text: str) -> list[dict]:
    """
    Extract experience information from resume text.
    Returns a list of experience entries with years and context.
    """
    experiences = []

    # Find years of experience mentions
    matches = EXPERIENCE_PATTERN.findall(text)
    total_years = max((int(m) for m in matches), default=0)

    # Try to find job titles and companies (simplified)
    lines = text.split("\n")
    current_entry = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for date ranges (e.g., "2020 - 2023", "Jan 2020 - Present")
        date_match = re.search(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}|Present|Current)",
            line,
            re.IGNORECASE,
        )
        if date_match:
            if current_entry:
                experiences.append(current_entry)
            current_entry = {
                "period": f"{date_match.group(1)} - {date_match.group(2)}",
                "description": line,
            }
        elif current_entry and len(line) > 10:
            # Add context to current entry
            current_entry["description"] += f" | {line}"

    if current_entry:
        experiences.append(current_entry)

    return {
        "total_years": total_years,
        "entries": experiences[:10],  # Limit to 10 entries
    }


def extract_education(text: str) -> list[dict]:
    """
    Extract education information from resume text.
    Returns a list of education entries.
    """
    education = []
    text_lower = text.lower()
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for keyword in EDUCATION_KEYWORDS:
            if keyword in line_lower:
                # Found an education-related line
                entry = {"description": line.strip()}

                # Try to find the degree level
                if any(k in line_lower for k in ["phd", "ph.d", "doctorate"]):
                    entry["level"] = "doctorate"
                elif any(k in line_lower for k in ["master", "m.s.", "m.sc", "m.tech", "mba", "mca", "m.e."]):
                    entry["level"] = "masters"
                elif any(k in line_lower for k in ["bachelor", "b.s.", "b.sc", "b.tech", "b.e.", "bca"]):
                    entry["level"] = "bachelors"
                elif any(k in line_lower for k in ["associate", "diploma"]):
                    entry["level"] = "associate"
                elif any(k in line_lower for k in ["certification", "certificate"]):
                    entry["level"] = "certification"

                education.append(entry)
                break  # Avoid duplicates from same line

    # Deduplicate
    seen = set()
    unique_education = []
    for e in education:
        desc = e["description"][:50]
        if desc not in seen:
            seen.add(desc)
            unique_education.append(e)

    return unique_education[:5]  # Limit to 5


def extract_structured(raw_text: str) -> dict:
    """
    Extract structured information from raw resume text.
    Returns a dict with skills, experience, education, and contact info.
    """
    if not raw_text:
        return {
            "skills": [],
            "experience": {"total_years": 0, "entries": []},
            "education": [],
            "contact": {"email": None, "phone": None},
        }

    return {
        "skills": extract_skills(raw_text),
        "experience": extract_experience(raw_text),
        "education": extract_education(raw_text),
        "contact": extract_contact_info(raw_text),
    }
