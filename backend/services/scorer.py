"""
AI Resume Analyzer — Scoring Engine

Hybrid scoring: keyword matching + embedding similarity + rule-based checks.
"""

import logging
import re
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", settings.embedding_model)
            _embedding_model = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            _embedding_model = False
    return _embedding_model if _embedding_model is not False else None


def score_keyword_match(candidate_skills, required_skills, preferred_skills, resume_text=""):
    candidate_lower = {s.lower() for s in candidate_skills}
    resume_lower = resume_text.lower()

    def match_skill(skill):
        sl = skill.lower()
        if sl in candidate_lower:
            return True, 1.0
        for cs in candidate_lower:
            if sl in cs or cs in sl:
                return True, 0.85
        if sl in resume_lower:
            return True, 0.75
        return False, 0.0

    matched_req = [{"skill": s, "matched": (m := match_skill(s))[0], "confidence": round(m[1], 2), "source": "keyword"} for s in required_skills]
    matched_pref = [{"skill": s, "matched": (m := match_skill(s))[0], "confidence": round(m[1], 2), "source": "keyword"} for s in preferred_skills]

    req_score = sum(1 for m in matched_req if m["matched"]) / max(len(required_skills), 1)
    pref_score = sum(1 for m in matched_pref if m["matched"]) / max(len(preferred_skills), 1)

    return {"score": round(0.7 * req_score + 0.3 * pref_score, 4), "matched_required": matched_req, "matched_preferred": matched_pref}


def score_embedding_similarity(resume_text, job_description):
    model = _get_embedding_model()
    if model is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            tfidf = TfidfVectorizer(max_features=5000, stop_words="english")
            matrix = tfidf.fit_transform([resume_text, job_description])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return {"score": round(float(sim), 4), "method": "tfidf"}
        except Exception:
            return {"score": 0.0, "method": "failed"}
    try:
        import numpy as np
        r_emb = model.encode(resume_text[:2000], normalize_embeddings=True)
        j_emb = model.encode(job_description[:2000], normalize_embeddings=True)
        sim = max(0.0, min(1.0, float(np.dot(r_emb, j_emb))))
        return {"score": round(sim, 4), "method": "sentence_transformer"}
    except Exception as e:
        logger.error("Embedding scoring failed: %s", e)
        return {"score": 0.0, "method": "failed"}


def score_rules(experience_data, education_data, job_experience_level):
    score = 0.0
    candidate_years = experience_data.get("total_years", 0) if isinstance(experience_data, dict) else 0
    exp_match = {"required": job_experience_level, "candidate_years": candidate_years, "match": False}

    levels = {"junior": (0, 3), "mid": (2, 7), "senior": (5, 99)}
    if job_experience_level and job_experience_level in levels:
        min_y, _ = levels[job_experience_level]
        if candidate_years >= min_y:
            exp_match["match"] = True
            score += 0.5
        elif candidate_years >= min_y - 1:
            exp_match["match"] = True
            score += 0.3
    else:
        exp_match["match"] = True
        score += 0.5

    edu_levels = {"certification": 1, "associate": 2, "bachelors": 3, "masters": 4, "doctorate": 5}
    highest_level, highest_rank = "unknown", 0
    for edu in (education_data or []):
        if isinstance(edu, dict):
            rank = edu_levels.get(edu.get("level", ""), 0)
            if rank > highest_rank:
                highest_rank = rank
                highest_level = edu.get("level", "unknown")

    edu_match = {"highest_level": highest_level, "match": highest_rank >= 1}
    score += min(0.5, highest_rank * 0.15) if highest_rank > 0 else 0

    return {"score": round(min(score, 1.0), 4), "experience_match": exp_match, "education_match": edu_match}


def score_candidate(resume_text, candidate_skills, experience_data, education_data,
                     job_description, required_skills, preferred_skills, job_experience_level=None):
    kw = score_keyword_match(candidate_skills, required_skills, preferred_skills, resume_text)
    emb = score_embedding_similarity(resume_text, job_description)
    rules = score_rules(experience_data, education_data, job_experience_level)

    w_kw, w_em, w_ru = settings.score_weight_keyword, settings.score_weight_embedding, settings.score_weight_rules
    overall = w_kw * kw["score"] + w_em * emb["score"] + w_ru * rules["score"]

    return {
        "overall_score": round(overall, 4),
        "shortlisted": overall >= settings.shortlist_threshold,
        "scoring_method": f"hybrid(kw={w_kw},emb={w_em},rules={w_ru})",
        "skill_match_detail": kw["matched_required"] + kw["matched_preferred"],
        "experience_match": rules["experience_match"],
        "education_match": rules["education_match"],
        "component_scores": {"keyword": kw["score"], "embedding": emb["score"], "embedding_method": emb["method"], "rules": rules["score"]},
    }
