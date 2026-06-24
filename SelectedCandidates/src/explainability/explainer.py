import logging

logger = logging.getLogger(__name__)

def generate_brief_reasoning(scored_cand: dict) -> str:
    """
    Generates a concise reasoning string matching the sample_submission.csv format:
    e.g., "ML Engineer with 6.4 yrs; 4 AI core skills; response rate 0.88."
    """
    title = scored_cand.get("career_details", {}).get("current_title", "Software Engineer")
    if not title:
        title = "Software Engineer"
        
    exp = scored_cand.get("career_details", {}).get("experience_years", 0.0)
    
    # Extract AI skills matched
    skill_det = scored_cand.get("skill_details", {})
    req_matched = skill_det.get("matched_required", [])
    pref_matched = skill_det.get("matched_preferred", [])
    ai_skills_count = len(req_matched) + len(pref_matched)
    
    # Recruiter response rate
    beh_det = scored_cand.get("behavior_details", {})
    rr = beh_det.get("recruiter_response_rate", 0.5)
    
    reasoning = f"{title} with {exp:.1f} yrs; {ai_skills_count} AI core skills; response rate {rr:.2f}."
    return reasoning

def generate_detailed_explanation(scored_cand: dict, rank: int) -> dict:
    """
    Generates a deep structured explanation for ranking transparency,
    breaking down all hybrid scoring components.
    """
    req_matched = scored_cand.get("skill_details", {}).get("matched_required", [])
    pref_matched = scored_cand.get("skill_details", {}).get("matched_preferred", [])
    
    return {
        "candidate_id": scored_cand["candidate_id"],
        "rank": rank,
        "final_score": scored_cand["final_score"],
        "raw_hybrid_score": scored_cand["raw_hybrid_score"],
        "category": scored_cand["category"],
        "multiplier": scored_cand["multiplier"],
        "scoring_breakdown": {
            "semantic_score_40pct": scored_cand["semantic_score"],
            "career_score_20pct": scored_cand["career_score"],
            "skill_score_15pct": scored_cand["skill_score"],
            "behavior_score_10pct": scored_cand["behavior_score"],
            "quality_score_10pct": scored_cand["quality_score"],
            "product_company_score_5pct": scored_cand["product_company_score"]
        },
        "strengths": {
            "experience_years": scored_cand["career_details"]["experience_years"],
            "matched_required_skills": req_matched,
            "matched_preferred_skills": pref_matched,
            "recruiter_response_rate": scored_cand["behavior_details"]["recruiter_response_rate"],
            "days_since_active": scored_cand["behavior_details"]["days_since_active"]
        },
        "weaknesses": {
            "consulting_history": scored_cand["career_details"]["company_score"] < 1.0,
            "missing_skills_count": max(0, 16 - len(req_matched)) # 16 is the total required skills in config
        }
    }
