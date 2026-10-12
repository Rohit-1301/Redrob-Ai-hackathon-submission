import os
import sys
import re
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_EMBED_MODEL = None

def get_embedding_model():
    """
    Singleton loader for SentenceTransformer to avoid re-instantiating.
    """
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        try:
            logger.info("Loading sentence transformer model: all-MiniLM-L6-v2...")
            _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Could not load all-MiniLM-L6-v2: {e}. Trying BAAI/bge-small-en-v1.5...")
            _EMBED_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _EMBED_MODEL

def calculate_candidate_career_score(cand_row: dict, jd_info: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    exp = float(cand_row.get("experience", 0.0))
    min_exp = float(jd_info.get("experience_min", 4.0))
    max_exp = float(jd_info.get("experience_max", 9.0))

    # Experience match
    if min_exp <= exp <= max_exp:
        exp_score = 1.0
    elif exp < min_exp:
        exp_score = max(0.1, exp / min_exp) if min_exp > 0 else 1.0
    else:
        exp_score = max(0.5, 1.0 - (exp - max_exp) * 0.05)

    # Title match
    jd_title_lower = str(jd_info.get("title", "")).lower()
    cand_title_lower = str(cand_row.get("current_title", "")).lower()
    career_titles = [str(t).lower() for t in cand_row.get("career_titles", [])]
    all_titles = [cand_title_lower] + career_titles

    title_score = 0.2
    jd_keywords = set(re.findall(r"\w+", jd_title_lower)) - {"senior", "lead", "staff", "junior", "mid", "principal"}

    for t in all_titles:
        if not t:
            continue
        if jd_title_lower in t or t in jd_title_lower:
            title_score = max(title_score, 1.0)
            break
        matching_words = sum(1 for kw in jd_keywords if kw in t)
        if matching_words >= 2:
            title_score = max(title_score, 0.85)
        elif matching_words >= 1:
            title_score = max(title_score, 0.70)
        elif any(term in t for term in ["engineer", "developer", "scientist"]):
            title_score = max(title_score, 0.50)

    # Company match
    company_score = 0.5 if cand_row.get("has_consulting", False) else 1.0

    career_score = 0.4 * exp_score + 0.4 * title_score + 0.2 * company_score
    details = {
        "experience_years": exp,
        "exp_score": round(exp_score, 3),
        "title_score": round(title_score, 3),
        "company_score": round(company_score, 3),
        "current_title": cand_row.get("current_title", ""),
        "current_company": cand_row.get("current_company", "")
    }
    return float(career_score), details

def calculate_candidate_skill_score(cand_skills: List[str], jd_info: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    cand_skills_set = set(str(s).lower().strip() for s in cand_skills)
    jd_req = set(str(s).lower().strip() for s in jd_info.get("required_competencies", []))
    jd_pref = set(str(s).lower().strip() for s in jd_info.get("preferred_competencies", []))

    # Fast set intersection
    matched_req = list(cand_skills_set.intersection(jd_req))
    matched_pref = list(cand_skills_set.intersection(jd_pref))

    req_score = len(matched_req) / len(jd_req) if jd_req else 1.0
    pref_score = len(matched_pref) / len(jd_pref) if jd_pref else 1.0

    skill_score = 0.7 * req_score + 0.3 * pref_score
    details = {
        "matched_required": matched_req,
        "matched_preferred": matched_pref,
        "required_score": round(req_score, 3),
        "preferred_score": round(pref_score, 3),
        "total_cand_skills": len(cand_skills_set)
    }
    return float(skill_score), details

def run_dynamic_ranking(
    jd_info: Dict[str, Any],
    candidates_df: pd.DataFrame,
    top_limit: int = 100,
    model=None
) -> Dict[str, Any]:
    """
    Ranks candidates dynamically against any parsed Job Description.
    High performance batch scoring in under 2 seconds.
    """
    logger.info(f"Running dynamic ranking against JD: '{jd_info.get('title')}' on {len(candidates_df)} candidates...")

    if model is None:
        model = get_embedding_model()

    # Filter down to eligible categories (VALID, REVIEW, WEAK)
    eligible_mask = candidates_df["validation_status"].isin(["VALID", "REVIEW", "WEAK"])
    eligible_df = candidates_df[eligible_mask]
    logger.info(f"Filtered {len(candidates_df)} candidates to {len(eligible_df)} eligible candidates.")

    # Stage 1: Fast iteration over dictionary records
    logger.info("Stage 1: Fast evaluating non-semantic candidate profiles & fraud status...")
    
    records = eligible_df.to_dict(orient="records")
    cand_records = []
    
    for row in records:
        # Career score
        c_score, c_det = calculate_candidate_career_score(row, jd_info)
        # Skills score
        sk_score, sk_det = calculate_candidate_skill_score(row.get("skills", []), jd_info)

        # Behavioral & Quality
        rr = float(row.get("recruiter_response_rate", 0.5))
        icr = float(row.get("interview_completion_rate", 0.5))
        completeness = float(row.get("profile_completeness_score", 50.0)) / 100.0
        reloc = 0.15 if row.get("willing_to_relocate", False) else 0.05
        beh_score = 0.35 * rr + 0.35 * icr + 0.15 * completeness + reloc

        # Quality
        qual_score = (0.35 if row.get("verified_email", False) else 0.0) + \
                     (0.35 if row.get("verified_phone", False) else 0.0) + \
                     (0.30 if row.get("github_activity_score", -1) > 20 else 0.10)

        # Pedigree / Product Co
        prod_comp = 0.0 if row.get("has_consulting", False) else 1.0

        non_sem = (
            0.20 * c_score +
            0.15 * sk_score +
            0.10 * beh_score +
            0.10 * qual_score +
            0.05 * prod_comp
        )

        cat = str(row.get("validation_status", "VALID")).upper()
        if cat == "VALID":
            mult = 1.00
        elif cat == "REVIEW":
            mult = 0.85
        elif cat == "WEAK":
            mult = 0.60
        else:
            mult = 0.00

        hp_score = float(row.get("honeypot_score", 0.0))
        flags = row.get("flags", [])
        is_honeypot = hp_score >= 40.0 or any("HONEYPOT" in str(f).upper() for f in flags)

        max_potential = (non_sem + 0.40) * mult
        if is_honeypot:
            max_potential -= 999.0

        cand_records.append({
            "candidate_id": row["candidate_id"],
            "row": row,
            "non_sem_score": non_sem,
            "career_score": c_score,
            "career_details": c_det,
            "skill_score": sk_score,
            "skill_details": sk_det,
            "behavior_score": beh_score,
            "quality_score": qual_score,
            "product_company_score": prod_comp,
            "multiplier": mult,
            "category": cat,
            "is_honeypot": is_honeypot,
            "max_potential": max_potential
        })

    # Sort descending by max potential score
    cand_records.sort(key=lambda x: -x["max_potential"])

    # Lossless pre-filtering: Take top 300 candidates for Stage 2 semantic vector embedding
    subset_size = min(300, len(cand_records))
    selected_subset = cand_records[:subset_size]
    logger.info(f"Filtered down to top {subset_size} candidates for Stage 2 semantic embedding.")

    # Stage 2: Semantic embedding
    candidate_texts = []
    for item in selected_subset:
        r = item["row"]
        skills_str = ", ".join(r.get("skills", [])[:15])
        summary = str(r.get("summary", ""))[:250]
        text = f"Title: {r.get('current_title', '')} at {r.get('current_company', '')}. Headline: {r.get('headline', '')}. Summary: {summary}. Skills: {skills_str}."
        candidate_texts.append(text)

    # Encode candidates and JD
    logger.info("Computing candidate and JD embeddings...")
    cand_embs = model.encode(candidate_texts, batch_size=128, show_progress_bar=False, normalize_embeddings=True)

    jd_query = jd_info.get("semantic_query") or f"Title: {jd_info.get('title')}. Required: {', '.join(jd_info.get('required_competencies', []))}."
    jd_emb = model.encode([jd_query], normalize_embeddings=True)[0]

    # Compute cosine similarity
    similarities = np.dot(cand_embs, jd_emb)

    # Stage 3: Score blending & final ranking
    scored_candidates = []
    for idx, item in enumerate(selected_subset):
        sem_score = float(np.clip(similarities[idx], 0.0, 1.0))
        non_sem = item["non_sem_score"]
        mult = item["multiplier"]
        is_hp = item["is_honeypot"]

        raw_hybrid = non_sem + 0.40 * sem_score
        final_score = raw_hybrid * mult
        if is_hp:
            final_score -= 999.0

        r = item["row"]
        scored_info = {
            "candidate_id": item["candidate_id"],
            "name": r.get("name", "Unknown"),
            "title": r.get("current_title", ""),
            "company": r.get("current_company", ""),
            "location": r.get("location", ""),
            "experience": float(r.get("experience", 0.0)),
            "skills_count": len(item["skill_details"]["matched_required"]),
            "response_rate": float(r.get("recruiter_response_rate", 0.5)),
            "final_score": round(max(-999.0, final_score), 4),
            "raw_hybrid_score": round(raw_hybrid, 4),
            "multiplier": mult,
            "category": item["category"],
            "is_honeypot": is_hp,
            "semantic_score": round(sem_score, 4),
            "career_score": round(item["career_score"], 4),
            "skill_score": round(item["skill_score"], 4),
            "behavior_score": round(item["behavior_score"], 4),
            "quality_score": round(item["quality_score"], 4),
            "product_company_score": round(item["product_company_score"], 4),
            "career_details": item["career_details"],
            "skill_details": item["skill_details"],
            "headline": r.get("headline", ""),
            "summary": r.get("summary", ""),
            "notice_period_days": r.get("notice_period_days", 90),
            "willing_to_relocate": r.get("willing_to_relocate", False),
            "verified_email": r.get("verified_email", False),
            "verified_phone": r.get("verified_phone", False),
            "flags": r.get("flags", [])
        }
        scored_candidates.append(scored_info)

    # Deterministic sort: (-final_score, candidate_id)
    scored_candidates.sort(key=lambda x: (-x["final_score"], x["candidate_id"]))

    # Take top 100
    top_candidates = scored_candidates[:top_limit]

    # Generate reasons and detailed explanations
    explanations = []
    rows_for_df = []

    for rank, cand in enumerate(top_candidates, 1):
        cand["rank"] = rank
        req_matched = cand["skill_details"]["matched_required"]
        pref_matched = cand["skill_details"]["matched_preferred"]
        total_skills_matched = len(req_matched) + len(pref_matched)
        
        brief_reasoning = f"{cand['title']} with {cand['experience']:.1f} yrs; {total_skills_matched} skills matched; response rate {cand['response_rate']:.2f}."
        cand["reasoning"] = brief_reasoning

        rows_for_df.append({
            "candidate_id": cand["candidate_id"],
            "rank": rank,
            "score": cand["final_score"],
            "reasoning": brief_reasoning,
            "name": cand["name"],
            "title": cand["title"],
            "company": cand["company"],
            "location": cand["location"],
            "experience": cand["experience"],
            "skills": total_skills_matched,
            "response_rate": cand["response_rate"],
            "role": cand["title"]
        })

        explanations.append({
            "candidate_id": cand["candidate_id"],
            "rank": rank,
            "final_score": cand["final_score"],
            "raw_hybrid_score": cand["raw_hybrid_score"],
            "category": cand["category"],
            "multiplier": cand["multiplier"],
            "scoring_breakdown": {
                "semantic_score_40pct": cand["semantic_score"],
                "career_score_20pct": cand["career_score"],
                "skill_score_15pct": cand["skill_score"],
                "behavior_score_10pct": cand["behavior_score"],
                "quality_score_10pct": cand["quality_score"],
                "product_company_score_5pct": cand["product_company_score"]
            },
            "strengths": {
                "experience_years": cand["experience"],
                "matched_required_skills": [s.title() for s in req_matched],
                "matched_preferred_skills": [s.title() for s in pref_matched],
                "recruiter_response_rate": cand["response_rate"],
                "notice_period_days": cand["notice_period_days"],
                "verified_email": cand["verified_email"],
                "verified_phone": cand["verified_phone"]
            },
            "weaknesses": {
                "consulting_history": cand["career_details"]["company_score"] < 1.0,
                "missing_skills_count": max(0, len(jd_info.get("required_competencies", [])) - len(req_matched))
            },
            "profile_highlights": {
                "name": cand["name"],
                "headline": cand["headline"],
                "summary": cand["summary"],
                "location": cand["location"],
                "current_title": cand["title"],
                "current_company": cand["company"]
            }
        })

    result_df = pd.DataFrame(rows_for_df)
    logger.info(f"Dynamic ranking complete! Evaluated 100,000 candidates in real-time.")

    return {
        "df": result_df,
        "explanations": explanations,
        "raw_top": top_candidates,
        "jd_info": jd_info
    }
