"""
AI Resume Analyzer — LLM-Assisted Extraction Service

Uses Google Gemini API for enhanced structured extraction
from resume text. Falls back to traditional parsing when unavailable.
"""

import json
import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# ── LLM Prompt Template ──
EXTRACTION_PROMPT = """You are an expert HR resume parser. Extract structured information from the following resume text.

Return a JSON object with these exact keys:
{
  "full_name": "string — candidate's full name",
  "email": "string or null",
  "phone": "string or null",
  "skills": ["list of technical and soft skills mentioned"],
  "experience": {
    "total_years": number,
    "entries": [
      {
        "title": "Job Title",
        "company": "Company Name",
        "period": "Start - End",
        "highlights": ["key achievements or responsibilities"]
      }
    ]
  },
  "education": [
    {
      "degree": "Degree name",
      "institution": "School/University",
      "year": "Graduation year or period",
      "level": "doctorate|masters|bachelors|associate|certification"
    }
  ],
  "summary": "A 2-3 sentence professional summary of the candidate"
}

IMPORTANT:
- Extract ALL skills mentioned, including programming languages, frameworks, tools, and soft skills
- For experience years, calculate from the earliest to latest date if not explicitly stated
- If information is missing or unclear, use null or empty arrays
- Return ONLY valid JSON, no markdown formatting

Resume text:
---
{resume_text}
---"""


async def extract_with_llm(raw_text: str) -> Optional[dict]:
    """
    Use Google Gemini API to extract structured data from resume text.

    Returns structured dict on success, None on failure.
    Caller should fall back to traditional extraction on None.
    """
    if not settings.llm_enabled:
        logger.debug("LLM extraction skipped: no API key configured")
        return None

    if not raw_text or len(raw_text) < 50:
        logger.warning("Resume text too short for LLM extraction (%d chars)", len(raw_text))
        return None

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

        # Truncate very long resumes to stay within token limits
        truncated_text = raw_text[:8000] if len(raw_text) > 8000 else raw_text

        prompt = ("You are a precise resume parser. Always respond with valid JSON only.\n\n"
                  + EXTRACTION_PROMPT.format(resume_text=truncated_text))

        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text
        result = json.loads(result_text)

        logger.info(
            "LLM extraction successful: found %d skills, %d experience entries",
            len(result.get("skills", [])),
            len(result.get("experience", {}).get("entries", [])),
        )
        return _normalize_llm_result(result)

    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON: %s", e)
        return None
    except ImportError:
        logger.error("google-genai package not installed")
        return None
    except Exception as e:
        logger.error("LLM extraction failed: %s", e)
        return None


def _normalize_llm_result(raw: dict) -> dict:
    """
    Normalize the LLM output to match our internal schema.
    Ensures consistent structure regardless of LLM output variations.
    """
    skills = raw.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    experience = raw.get("experience", {})
    if isinstance(experience, list):
        experience = {"total_years": 0, "entries": experience}
    elif not isinstance(experience, dict):
        experience = {"total_years": 0, "entries": []}

    # Ensure entries have required fields
    entries = experience.get("entries", [])
    normalized_entries = []
    for entry in entries:
        if isinstance(entry, dict):
            normalized_entries.append({
                "title": entry.get("title", ""),
                "company": entry.get("company", ""),
                "period": entry.get("period", ""),
                "highlights": entry.get("highlights", []),
            })

    education = raw.get("education", [])
    if isinstance(education, str):
        education = [{"description": education, "level": "unknown"}]
    normalized_education = []
    for edu in education:
        if isinstance(edu, dict):
            normalized_education.append({
                "degree": edu.get("degree", ""),
                "institution": edu.get("institution", ""),
                "year": edu.get("year", ""),
                "level": edu.get("level", "unknown"),
                "description": f"{edu.get('degree', '')} - {edu.get('institution', '')}",
            })

    return {
        "full_name": raw.get("full_name"),
        "email": raw.get("email"),
        "phone": raw.get("phone"),
        "skills": [s for s in skills if isinstance(s, str) and s.strip()],
        "experience": {
            "total_years": int(experience.get("total_years", 0) or 0),
            "entries": normalized_entries,
        },
        "education": normalized_education,
        "summary": raw.get("summary", ""),
        "contact": {
            "email": raw.get("email"),
            "phone": raw.get("phone"),
        },
    }
