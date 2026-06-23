import os
import sys
import logging
import datetime

# Setup path to import configs
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from configs.config import (
    REFERENCE_DATE,
    CONSULTING_COMPANIES,
    JD_REQUIRED_SKILLS,
    JD_PREFERRED_SKILLS
)

logger = logging.getLogger(__name__)

def calculate_career_score(candidate: dict) -> dict:
    """
    Computes Career Score (20% weight in hybrid score):
    - Experience match (preferred 5-9 years): 40% weight
    - Title alignment: 40% weight
    - Product company vs consulting company check: 20% weight
    """
    profile = candidate.get("profile", {})
    exp = float(profile.get("years_of_experience", 0) or 0)
    
    # 1. Experience score
    if 5 <= exp <= 9:
        exp_score = 1.0
    elif exp < 5:
        exp_score = exp / 5.0
    else:
        # exp > 9: mild penalty for being overqualified for a senior engineer role
        exp_score = max(0.5, 1.0 - (exp - 9) * 0.05)
        
    # 2. Title score
    current_title = str(profile.get("current_title", "")).lower().strip()
    career_titles = [
        str(job.get("title", "")).lower().strip() 
        for job in candidate.get("career_history", []) 
        if isinstance(job, dict)
    ]
    all_titles = [current_title] + career_titles
    
    strong_keywords = ["ai", "machine learning", "ml", "retrieval", "search", "nlp", "ranking", "recommendation"]
    medium_keywords = ["data scientist", "research engineer", "applied scientist", "science", "analytics"]
    
    max_title_score = 0.2  # default baseline
    for title in all_titles:
        if not title:
            continue
        # Exact/strong title match
        if any(kw in title for kw in ["ai engineer", "machine learning engineer", "ml engineer", "search engineer", "retrieval engineer", "ranking engineer", "recommendation engineer"]):
            max_title_score = max(max_title_score, 1.0)
        elif any(kw in title for kw in strong_keywords):
            max_title_score = max(max_title_score, 0.85)
        elif any(kw in title for kw in medium_keywords):
            max_title_score = max(max_title_score, 0.70)
        elif any(kw in title for kw in ["software", "developer", "engineer"]):
            max_title_score = max(max_title_score, 0.50)
            
    # 3. Company score (product vs consulting)
    current_company = str(profile.get("current_company", "")).lower().strip()
    career_companies = [
        str(job.get("company", "")).lower().strip() 
        for job in candidate.get("career_history", []) 
        if isinstance(job, dict)
    ]
    
    is_current_consulting = any(c_co in current_company for c_co in CONSULTING_COMPANIES)
    is_any_consulting = is_current_consulting or any(
        any(c_co in company for c_co in CONSULTING_COMPANIES) 
        for company in career_companies
    )
    
    if is_current_consulting:
        company_score = 0.0
    elif is_any_consulting:
        company_score = 0.5
    else:
        company_score = 1.0
        
    career_score = 0.4 * exp_score + 0.4 * max_title_score + 0.2 * company_score
    
    return {
        "score": career_score,
        "details": {
            "experience_years": exp,
            "exp_score": exp_score,
            "title_score": max_title_score,
            "company_score": company_score,
            "current_title": profile.get("current_title", ""),
            "current_company": profile.get("current_company", "")
        }
    }

def calculate_skill_score(candidate: dict) -> dict:
    """
    Computes Skill Score (15% weight in hybrid score):
    - Matches candidate skills against JD_REQUIRED_SKILLS and JD_PREFERRED_SKILLS
    """
    cand_skills = set()
    for s in candidate.get("skills", []):
        if isinstance(s, dict) and s.get("name"):
            cand_skills.add(str(s["name"]).lower().strip())
            
    req_matches = cand_skills.intersection(JD_REQUIRED_SKILLS)
    pref_matches = cand_skills.intersection(JD_PREFERRED_SKILLS)
    
    req_score = len(req_matches) / len(JD_REQUIRED_SKILLS) if JD_REQUIRED_SKILLS else 1.0
    pref_score = len(pref_matches) / len(JD_PREFERRED_SKILLS) if JD_PREFERRED_SKILLS else 1.0
    
    skill_score = 0.7 * req_score + 0.3 * pref_score
    
    return {
        "score": skill_score,
        "details": {
            "total_skills": len(cand_skills),
            "matched_required": list(req_matches),
            "matched_preferred": list(pref_matches),
            "required_score": req_score,
            "preferred_score": pref_score
        }
    }

def calculate_behavior_score(candidate: dict) -> dict:
    """
    Computes Behavior Score (10% weight in hybrid score):
    - Recruiter response rate (30% weight)
    - Interview completion rate (30% weight)
    - Open to work flag (15% weight)
    - Profile completeness (10% weight)
    - Login recency based on last active date vs REFERENCE_DATE (15% weight)
    Incorporates the precomputed behavioral score from the dataset (50% blend weight)
    """
    signals = candidate.get("redrob_signals", {})
    
    # 1. Recruiter response rate
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr == -1 or rr is None:
        rr = 0.5
        
    # 2. Interview completion rate
    icr = signals.get("interview_completion_rate", 0.5)
    if icr == -1 or icr is None:
        icr = 0.5
        
    # 3. Open to work flag
    otw = 1.0 if signals.get("open_to_work_flag") else 0.5
    
    # 4. Profile completeness
    pc = float(signals.get("profile_completeness_score", 50)) / 100.0
    
    # 5. Login recency
    recency_score = 0.5
    last_active_str = signals.get("last_active_date")
    days_diff = 365
    if last_active_str:
        try:
            parts = last_active_str.split("-")
            last_active_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            days_diff = (REFERENCE_DATE - last_active_date).days
            if days_diff <= 30:
                recency_score = 1.0
            elif days_diff <= 90:
                recency_score = 0.8
            elif days_diff <= 180:
                recency_score = 0.6
            else:
                recency_score = 0.3
        except Exception:
            recency_score = 0.5
            
    computed_beh = 0.3 * rr + 0.3 * icr + 0.15 * otw + 0.1 * pc + 0.15 * recency_score
    
    # Blend with precomputed behavioral score
    raw_beh = float(candidate.get("behavioral_score", 50.0)) / 100.0
    final_behavior_score = 0.5 * computed_beh + 0.5 * raw_beh
    
    return {
        "score": final_behavior_score,
        "details": {
            "recruiter_response_rate": rr,
            "interview_completion_rate": icr,
            "open_to_work": otw == 1.0,
            "profile_completeness": pc,
            "days_since_active": days_diff,
            "recency_score": recency_score,
            "raw_behavioral_score": raw_beh,
            "computed_behavioral_score": computed_beh
        }
    }

def calculate_quality_score(candidate: dict) -> dict:
    """
    Computes Quality Score (10% weight in hybrid score):
    - Blend of validation score (80% weight) and credibility score (20% weight) from candidate record
    """
    val_score = float(candidate.get("validation_score", 80.0)) / 100.0
    cred_score = float(candidate.get("credibility_score", 80.0)) / 100.0
    
    quality_score = 0.8 * val_score + 0.2 * cred_score
    
    return {
        "score": quality_score,
        "details": {
            "validation_score": val_score,
            "credibility_score": cred_score
        }
    }

def calculate_product_company_score(candidate: dict) -> float:
    """
    Computes Product Company Score (5% weight in hybrid score):
    - 1.0 if no consulting companies found in current or past companies, 0.0 otherwise.
    """
    profile = candidate.get("profile", {})
    current_company = str(profile.get("current_company", "")).lower().strip()
    career_companies = [
        str(job.get("company", "")).lower().strip() 
        for job in candidate.get("career_history", []) 
        if isinstance(job, dict)
    ]
    
    is_any_consulting = any(c_co in current_company for c_co in CONSULTING_COMPANIES) or any(
        any(c_co in company for c_co in CONSULTING_COMPANIES) 
        for company in career_companies
    )
    
    return 0.0 if is_any_consulting else 1.0

def score_candidate(candidate: dict, semantic_score: float, category: str) -> dict:
    """
    Scores a single candidate.
    Applies the weights:
    - Semantic similarity (40%)
    - Career alignment (20%)
    - Skills match (15%)
    - Behavioral profile (10%)
    - Validation quality (10%)
    - Product company status (5%)
    
    Applies category multipliers:
    - VALID: 1.0
    - REVIEW: 0.85
    - WEAK: 0.60
    - INVALID: 0.00
    
    Applies honeypot penalty:
    - Subtracts 999.0 if honeypot score > 80 or honeypot flag detected.
    """
    career = calculate_career_score(candidate)
    skill = calculate_skill_score(candidate)
    behavior = calculate_behavior_score(candidate)
    quality = calculate_quality_score(candidate)
    prod_comp = calculate_product_company_score(candidate)
    
    raw_hybrid_score = (
        0.40 * semantic_score +
        0.20 * career["score"] +
        0.15 * skill["score"] +
        0.10 * behavior["score"] +
        0.10 * quality["score"] +
        0.05 * prod_comp
    )
    
    # Determine multiplier
    cat_upper = category.upper()
    if cat_upper == "VALID":
        multiplier = 1.00
    elif cat_upper == "REVIEW":
        multiplier = 0.85
    elif cat_upper == "WEAK":
        multiplier = 0.60
    else:
        multiplier = 0.00
        
    final_score = raw_hybrid_score * multiplier
    
    # Honeypot penalty check
    honeypot_score = candidate.get("honeypot_score", 0)
    is_honeypot = honeypot_score > 80 or "honeypot" in str(candidate.get("flags", [])).lower()
    
    if is_honeypot:
        final_score -= 999.0
        
    return {
        "candidate_id": candidate.get("candidate_id"),
        "final_score": round(max(-999.0, final_score), 4),
        "raw_hybrid_score": round(raw_hybrid_score, 4),
        "multiplier": multiplier,
        "category": cat_upper,
        "is_honeypot": is_honeypot,
        "semantic_score": round(semantic_score, 4),
        "career_score": round(career["score"], 4),
        "skill_score": round(skill["score"], 4),
        "behavior_score": round(behavior["score"], 4),
        "quality_score": round(quality["score"], 4),
        "product_company_score": prod_comp,
        "career_details": career["details"],
        "skill_details": skill["details"],
        "behavior_details": behavior["details"],
        "quality_details": quality["details"]
    }
