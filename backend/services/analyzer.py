"""
AI Resume Analyzer — Resume Analyzer Service

Handles:
1) AI Resume Improvement Suggestions (weak sections, action verbs, formatting, ATS compatibility, transformations).
2) Skill Gap Analysis (required, candidate, missing skills).
3) ATS Scoring (Keyword match, Formatting, Skills, Experience, overall score).
Supports Google Gemini LLM analysis with a robust rule-based fallback.
"""

import logging
import re
import json
from typing import Optional, List, Dict, Any

from backend.config import settings

logger = logging.getLogger(__name__)

# List of weak verbs and their stronger action verb alternatives
ACTION_VERB_MAP = {
    "assisted": ["orchestrated", "facilitated", "collaborated on", "supported"],
    "helped": ["expedited", "championed", "supported", "boosted"],
    "managed": ["spearheaded", "directed", "steered", "administered"],
    "worked on": ["engineered", "implemented", "devised", "crafted"],
    "responsible for": ["executed", "managed", "supervised", "spearheaded"],
    "made": ["authored", "engineered", "formulated", "established"],
    "did": ["executed", "performed", "discharged", "conducted"],
    "used": ["leveraged", "utilized", "deployed", "implemented"],
    "got": ["acquired", "attained", "secured", "procured"],
    "handled": ["resolved", "managed", "navigated", "negotiated"],
    "led": ["spearheaded", "guided", "piloted", "championed"],
    "changed": ["transformed", "streamlined", "revitalized", "modernized"],
}

# Heuristics for formatting/ATS checks
COMMON_WEAK_PHRASES = [
    "responsible for",
    "duties included",
    "assisted with",
    "helped to",
    "worked on",
]

ANALYSIS_PROMPT_TEMPLATE = """You are an expert ATS (Applicant Tracking System) consultant and professional resume writer.
Analyze the following candidate's resume text, optionally compared against the target job description.

Target Job Description:
---
{job_description}
---

Candidate's Resume Text:
---
{resume_text}
---

Perform a comprehensive analysis and return a JSON object with the following structure:
{{
  "weak_sections": [
    {{
      "section": "Section Name (e.g., Summary, Experience, Education, Skills)",
      "issue": "Specific issue identified in this section",
      "suggestion": "Detailed, actionable suggestion to fix the issue"
    }}
  ],
  "proposed_verbs": [
    {{
      "original": "The weak verb found in the resume",
      "replacement": "Recommended stronger action verb",
      "context": "Context or example of how to change the bullet point"
    }}
  ],
  "formatting_suggestions": [
    "List of actionable suggestions to improve the visual layout and readability of the resume"
  ],
  "ats_compatibility": [
    "List of suggestions to improve compatibility with automated ATS parsers (e.g., headings, headers, structure)"
  ],
  "example_transformations": [
    {{
      "input": "An existing weak bullet point or sentence from the resume",
      "improved": "The rewritten, high-impact version of that bullet point incorporating action verbs and metrics"
    }}
  ],
  "improved_resume": "A fully polished, professionally formatted Markdown version of the resume incorporating all suggestions. Maintain all real candidate details but rewrite accomplishments for maximum impact, starting bullet points with strong action verbs and including placeholder metrics where appropriate (e.g., '[X]%')."
}}

IMPORTANT:
- Focus on finding weak action verbs, lack of quantifiable achievements (metrics), and generic descriptions.
- Ensure formatting suggestions are actionable and specific to the input text.
- If no Job Description is provided, perform a general resume critique.
- Return ONLY valid JSON, no markdown wrapper around the JSON object.
"""

async def analyze_resume_improvement(
    resume_text: str,
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate AI Resume Improvement Suggestions.
    Uses Gemini LLM if available; falls back to rule-based heuristics.
    """
    if not resume_text or len(resume_text.strip()) < 50:
        return _get_fallback_improvement_suggestions(resume_text, job_description)

    if settings.llm_enabled:
        try:
            from google import genai
            client = genai.Client(api_key=settings.gemini_api_key)

            job_desc_str = job_description or "None provided (General critique)"
            # Truncate inputs to stay safe on tokens
            trunc_resume = resume_text[:8000]
            trunc_job = job_desc_str[:4000]

            prompt = ("You are a professional ATS resume optimizer. Respond with valid JSON only.\n\n"
                      + ANALYSIS_PROMPT_TEMPLATE.format(
                          resume_text=trunc_resume,
                          job_description=trunc_job
                      ))

            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=2500,
                    response_mime_type="application/json",
                ),
            )

            result_text = response.text
            result = json.loads(result_text)
            logger.info("Successfully analyzed resume using LLM")
            return result

        except Exception as e:
            logger.error("LLM resume analysis failed, using fallback: %s", e)
            return _get_fallback_improvement_suggestions(resume_text, job_description)
    else:
        logger.info("LLM disabled, using fallback resume analyzer")
        return _get_fallback_improvement_suggestions(resume_text, job_description)


def _get_fallback_improvement_suggestions(
    resume_text: str,
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates rule-based resume suggestions when LLM is unavailable.
    """
    weak_sections = []
    proposed_verbs = []
    formatting_suggestions = [
        "Keep resume to 1 page if under 5 years of experience, or 2 pages maximum.",
        "Use a clean, single-column layout. Multi-column templates often parse incorrectly in older ATS systems.",
        "Ensure margins are set to 0.75 or 1.0 inch on all sides.",
        "Use professional sans-serif fonts such as Arial, Calibri, or Helvetica, sized 10-12pt for body text."
    ]
    ats_compatibility = [
        "Avoid placing important information like contact details inside headers, footers, or text boxes.",
        "Use standard section headings: 'Professional Experience', 'Education', 'Skills', and 'Summary'.",
        "Save and upload your resume as a PDF or DOCX; avoid image files or portfolio websites that ATS cannot read.",
        "Ensure all tables, charts, and graphics are removed. ATS scanners read text line-by-line and will scramble table layouts."
    ]
    example_transformations = []

    text_lower = resume_text.lower()

    # Check for weak sections
    if "summary" not in text_lower and "profile" not in text_lower:
        weak_sections.append({
            "section": "Summary / Profile",
            "issue": "No professional summary detected.",
            "suggestion": "Add a brief 3-4 sentence professional summary at the top of your resume. Introduce yourself, state your core technical expertise, and mention the value you bring to the role."
        })
    
    if "experience" not in text_lower and "history" not in text_lower and "work" not in text_lower:
        weak_sections.append({
            "section": "Professional Experience",
            "issue": "Experience section header is missing or non-standard.",
            "suggestion": "Create a clear 'Professional Experience' section. List your jobs in reverse chronological order with standard subheadings for Title, Company, and Dates."
        })
    
    if "education" not in text_lower and "academic" not in text_lower:
        weak_sections.append({
            "section": "Education",
            "issue": "Education section is missing or hard to locate.",
            "suggestion": "Add an 'Education' section listing your degree title, institution name, and graduation year."
        })

    if "skills" not in text_lower:
        weak_sections.append({
            "section": "Skills",
            "issue": "No dedicated Skills section found.",
            "suggestion": "Create a structured 'Skills' section grouped by category (e.g., Languages, Frameworks, Developer Tools) to make it easy for ATS and recruiters to scan."
        })

    # Propose stronger verbs by scanning text for weak verbs
    found_weak_verbs = set()
    for weak_verb, replacements in ACTION_VERB_MAP.items():
        pattern = r'\b' + re.escape(weak_verb) + r'\b'
        if re.search(pattern, text_lower):
            found_weak_verbs.add(weak_verb)
            proposed_verbs.append({
                "original": weak_verb,
                "replacement": replacements[0],
                "context": f"Instead of saying '{weak_verb} in project development', try: '{replacements[0].capitalize()} development for high-priority projects...'"
            })
            if len(proposed_verbs) >= 4:
                break

    # If no weak verbs found, suggest standard replacements
    if not proposed_verbs:
        proposed_verbs.append({
            "original": "assisted",
            "replacement": "orchestrated",
            "context": "Change 'assisted in team collaboration' to 'Orchestrated cross-functional collaboration...'"
        })
        proposed_verbs.append({
            "original": "helped",
            "replacement": "expedited",
            "context": "Change 'helped resolve client issues' to 'Expedited resolution of critical client tickets...'"
        })

    # Find weak phrases and add example transformations
    for phrase in COMMON_WEAK_PHRASES:
        if phrase in text_lower:
            example_transformations.append({
                "input": f"Responsible for {phrase} database migration.",
                "improved": f"Spearheaded database migration, optimizing query response time by 30% and reducing down-time."
            })
            break

    if not example_transformations:
        example_transformations.append({
            "input": "Responsible for writing clean code and fixing bugs.",
            "improved": "Engineered highly scalable REST APIs and resolved 40+ legacy system issues, improving service stability by 15%."
        })

    # Mock an improved markdown version of the resume
    improved_markdown = f"""# [Full Name]
[City, State] | [Phone Number] | [Email Address] | [LinkedIn/GitHub]

## Professional Summary
Detail-oriented and results-driven professional with a proven track record of delivering high-quality software solutions. Adept at leveraging modern frameworks, optimizing backend services, and collaborating in cross-functional teams to build responsive web applications.

## Skills
* **Languages:** Python, SQL, JavaScript, HTML/CSS
* **Frameworks/Libraries:** FastAPI, Flask, Streamlit, React
* **Tools & Databases:** Git, Docker, PostgreSQL, SQLite, AWS
* **Concepts:** RESTful APIs, OOP, CI/CD, Agile Methodologies

## Professional Experience
### [Job Title] | [Company Name]
*Location* | *Period*
* **Spearheaded** design and deployment of microservices, boosting throughput by 25%.
* **Orchestrated** migrations of legacy systems to PostgreSQL, reducing query latency by 18%.
* **Leveraged** automated CI/CD pipelines to streamline deployment cycles, reducing release times by 2 days.
* **Engineered** unit tests and integration tests, increasing code coverage to 92%.

### [Job Title] | [Company Name]
*Location* | *Period*
* **Optimized** client-facing dashboard using React, enhancing user retention rate by 12%.
* **Collaborated** with product managers to scope out new REST API endpoints.
* **Resolved** high-priority bugs under tight deadlines to maintain 99.9% uptime.

## Education
### Bachelor of Science in Computer Science
*[University Name]* | *[Graduation Year]*
"""

    return {
        "weak_sections": weak_sections,
        "proposed_verbs": proposed_verbs,
        "formatting_suggestions": formatting_suggestions,
        "ats_compatibility": ats_compatibility,
        "example_transformations": example_transformations,
        "improved_resume": improved_markdown
    }


def analyze_skill_gap(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str]
) -> Dict[str, Any]:
    """
    Compares candidate skills against job requirements.
    Output: Required Skills, Candidate Skills, Missing Skills.
    """
    c_skills_set = {s.strip().lower() for s in candidate_skills if s and s.strip()}
    req_skills_set = {s.strip().lower() for s in required_skills if s and s.strip()}
    pref_skills_set = {s.strip().lower() for s in preferred_skills if s and s.strip()}

    # Match skills case-insensitively, but keep original casing for response
    matched_req = []
    missing_req = []
    for skill in required_skills:
        sl = skill.lower()
        # Direct match
        if sl in c_skills_set:
            matched_req.append(skill)
        # Substring/Superstring matching
        elif any(sl in cs or cs in sl for cs in c_skills_set):
            matched_req.append(skill)
        else:
            missing_req.append(skill)

    matched_pref = []
    missing_pref = []
    for skill in preferred_skills:
        sl = skill.lower()
        if sl in c_skills_set:
            matched_pref.append(skill)
        elif any(sl in cs or cs in sl for cs in c_skills_set):
            matched_pref.append(skill)
        else:
            missing_pref.append(skill)

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "candidate_skills": candidate_skills,
        "matched_required": matched_req,
        "missing_required": missing_req,
        "matched_preferred": matched_pref,
        "missing_preferred": missing_pref,
        "missing_skills": missing_req,  # Backward compatibility / simple output
    }


def calculate_ats_score(
    candidate_skills: List[str],
    experience_data: Dict[str, Any],
    education_data: List[Dict[str, Any]],
    resume_text: str,
    job_description: str,
    required_skills: List[str],
    preferred_skills: List[str],
    job_experience_level: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes candidate ATS scores across: Keyword match, Formatting, Skills, and Experience.
    Returns scores out of 100, and an overall ATS score out of 100.
    """
    # 1. Keyword Match Score (0 - 100)
    # Checks presence of required and preferred skills in the full resume text
    resume_lower = resume_text.lower() if resume_text else ""
    c_skills_lower = {s.lower() for s in candidate_skills}

    def is_skill_in_resume(skill):
        sl = skill.lower()
        if sl in c_skills_lower:
            return True
        if sl in resume_lower:
            return True
        # Partial match
        if any(sl in cs or cs in sl for cs in c_skills_lower):
            return True
        return False

    req_matches = sum(1 for s in required_skills if is_skill_in_resume(s))
    pref_matches = sum(1 for s in preferred_skills if is_skill_in_resume(s))

    req_factor = req_matches / max(len(required_skills), 1)
    pref_factor = pref_matches / max(len(preferred_skills), 1)

    # Keyword match score: 80% required skills, 20% preferred skills
    keyword_score = (0.8 * req_factor + 0.2 * pref_factor) * 100
    keyword_score = round(max(0.0, min(100.0, keyword_score)), 1)

    # 2. Formatting Score (0 - 100)
    # Heuristic checks: email present, phone present, clean structure, lack of weak phrases, etc.
    formatting_score = 0.0
    
    # Check contact details
    has_email = "@" in resume_text
    has_phone = re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\+?\d{1,3}[ -]?\d{1,14}\b', resume_text) is not None
    if has_email:
        formatting_score += 20
    if has_phone:
        formatting_score += 20

    # Check sections presence
    text_lower = resume_text.lower()
    sections = ["summary", "experience", "education", "skills"]
    sections_found = sum(1 for s in sections if s in text_lower)
    formatting_score += (sections_found / len(sections)) * 40  # up to 40 points

    # Check action verb usage density
    weak_phrase_count = sum(text_lower.count(phrase) for phrase in COMMON_WEAK_PHRASES)
    if weak_phrase_count == 0:
        formatting_score += 20
    elif weak_phrase_count <= 2:
        formatting_score += 10
    else:
        formatting_score += 5

    formatting_score = round(max(10.0, min(100.0, formatting_score)), 1)

    # 3. Skills Score (0 - 100)
    # A deeper skills matching, combining candidate's extracted skills vs job required skills
    skills_gap = analyze_skill_gap(candidate_skills, required_skills, preferred_skills)
    total_req = len(required_skills)
    total_pref = len(preferred_skills)
    
    matched_req_cnt = len(skills_gap["matched_required"])
    matched_pref_cnt = len(skills_gap["matched_preferred"])
    
    req_ratio = matched_req_cnt / max(total_req, 1)
    pref_ratio = matched_pref_cnt / max(total_pref, 1)
    
    skills_score = (0.7 * req_ratio + 0.3 * pref_ratio) * 100
    # Add a tiny bump if they have extra skills
    extra_skills_count = max(0, len(candidate_skills) - matched_req_cnt - matched_pref_cnt)
    skills_score += min(10.0, extra_skills_count * 0.5)
    skills_score = round(max(0.0, min(100.0, skills_score)), 1)

    # 4. Experience Score (0 - 100)
    # Check years of experience vs required job experience level
    experience_score = 50.0
    candidate_years = experience_data.get("total_years", 0) if isinstance(experience_data, dict) else 0
    
    levels = {"junior": (0, 2), "mid": (2, 5), "senior": (5, 99)}
    if job_experience_level and job_experience_level in levels:
        min_y, max_y = levels[job_experience_level]
        if candidate_years >= min_y:
            # Meets min requirement
            experience_score = 100.0
            # If candidate years is way too high for a junior role, give slight penalty to match fit
            if job_experience_level == "junior" and candidate_years > 5:
                experience_score = 80.0
        else:
            # Under-experienced
            diff = min_y - candidate_years
            if diff <= 1:
                experience_score = 75.0
            elif diff <= 2:
                experience_score = 60.0
            else:
                experience_score = 40.0
    else:
        # No experience level required for the job
        if candidate_years > 0:
            experience_score = 90.0
        else:
            experience_score = 70.0

    # Also evaluate education level match (optional bonus)
    edu_levels = {"certification": 1, "associate": 2, "bachelors": 3, "masters": 4, "doctorate": 5}
    highest_rank = 0
    for edu in (education_data or []):
        if isinstance(edu, dict):
            rank = edu_levels.get(edu.get("level", ""), 0)
            if rank > highest_rank:
                highest_rank = rank

    # Add education bonus (up to 10 points)
    if highest_rank >= 3:  # Bachelors or higher
        experience_score = min(100.0, experience_score + 10)
    
    experience_score = round(max(20.0, min(100.0, experience_score)), 1)

    # 5. Overall Score (0 - 100)
    # Weighting: Keywords (30%), Formatting (15%), Skills Match (35%), Experience (20%)
    overall_score = (
        0.30 * keyword_score +
        0.15 * formatting_score +
        0.35 * skills_score +
        0.20 * experience_score
    )
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)

    return {
        "overall_score": overall_score,
        "keyword_score": keyword_score,
        "formatting_score": formatting_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "experience_years": candidate_years,
        "required_experience_level": job_experience_level,
        "formatting_issues_count": max(0, 5 - (int(formatting_score) // 20)),
    }
