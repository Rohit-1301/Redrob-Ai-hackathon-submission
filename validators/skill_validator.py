from configs.config import AI_ML_KEYWORDS

def validate_skills(candidate: dict) -> list:
    """
    Validates skill credibility, duration consistency, and consistency with employment history.
    """
    errors = []
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    if not isinstance(skills, list) or len(skills) == 0:
        return errors

    claimed_years = profile.get("years_of_experience", 0.0)
    
    # Calculate actual experience in months from career history
    total_history_months = sum(job.get("duration_months", 0) for job in career_history if isinstance(job, dict))
    max_allowed_months = max(total_history_months, int(claimed_years * 12))

    # 1. Skill Inflation
    high_proficiency_skills = [s for s in skills if isinstance(s, dict) and s.get("proficiency") in ["advanced", "expert"]]
    if len(high_proficiency_skills) >= 15 and claimed_years < 3.0:
        errors.append({
            "code": "SKILL_INFLATION",
            "severity": "HIGH",
            "message": f"Candidate claims {len(high_proficiency_skills)} advanced/expert skills with only {claimed_years} years of experience"
        })
    elif len(skills) >= 30 and claimed_years < 2.0:
        errors.append({
            "code": "SKILL_INFLATION_ABSOLUTE",
            "severity": "HIGH",
            "message": f"Candidate claims a total of {len(skills)} skills with only {claimed_years} years of experience"
        })

    # 2. Skill Duration Mismatch
    for i, skill in enumerate(skills):
        if not isinstance(skill, dict):
            continue
        name = skill.get("name", "Unknown")
        duration = skill.get("duration_months", 0)
        
        # If a single skill duration exceeds maximum allowed history + 6 months padding
        if duration > (max_allowed_months + 6):
            errors.append({
                "code": "SKILL_DURATION_MISMATCH",
                "severity": "HIGH",
                "message": f"Skill '{name}' duration ({duration} months) exceeds candidate's total career history duration ({max_allowed_months} months)"
            })

    # 3. Skill-Job Consistency (e.g. claims AI skills but no AI history)
    candidate_ai_skills = []
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        s_name = skill.get("name", "").lower()
        if any(kw in s_name for kw in AI_ML_KEYWORDS):
            candidate_ai_skills.append(skill.get("name"))

    if candidate_ai_skills:
        has_ai_history = False
        for job in career_history:
            if not isinstance(job, dict):
                continue
            title = job.get("title", "").lower()
            desc = job.get("description", "").lower()
            
            # Check if any of our AI_ML_KEYWORDS are found in the title or description
            if any(kw in title or kw in desc for kw in AI_ML_KEYWORDS):
                has_ai_history = True
                break
                
        if not has_ai_history:
            errors.append({
                "code": "SKILL_EMPLOYMENT_INCONSISTENCY",
                "severity": "MEDIUM",
                "message": f"Candidate claims AI/ML skills ({', '.join(candidate_ai_skills[:4])}...) but career history has no mention of AI/ML engineering, search, or retrieval work"
            })

    return errors
