import re
from configs.config import AI_ML_KEYWORDS

# Standard copypasta description templates to match
TEMPLATE_PATTERNS = {
    "mechanical_design": {
        "pattern": r"mechanical\s+engineering\s+design\s+role",
        "allowed_titles": ["mechanical", "hardware", "design", "engineer", "cad", "creo", "ansys"]
    },
    "customer_support": {
        "pattern": r"customer\s+support\s+team\s+lead",
        "allowed_titles": ["support", "customer", "service", "helpdesk", "help desk"]
    },
    "content_writing": {
        "pattern": r"content\s+writing\s+and\s+seo",
        "allowed_titles": ["content", "writer", "seo", "editor", "marketing", "copywriter", "editorial"]
    },
    "business_analyst": {
        "pattern": r"business\s+analyst\s+at\s+a\s+consulting",
        "allowed_titles": ["analyst", "consultant", "business", "consulting", "strategy"]
    },
    "brand_design": {
        "pattern": r"brand\s+design\s+and\s+creative",
        "allowed_titles": ["design", "brand", "creative", "art", "marketing", "graphic", "designer"]
    },
    "accounting": {
        "pattern": r"senior\s+accounting\s+role",
        "allowed_titles": ["accounting", "accountant", "finance", "financial", "auditor", "gl"]
    },
    "operations": {
        "pattern": r"operations\s+management\s+role",
        "allowed_titles": ["operations", "operator", "ops", "logistics", "warehouse", "fulfillment"]
    }
}

def detect_honeypots(candidate: dict) -> tuple:
    """
    Detects impossible timelines, copypasta descriptions, title-description mismatches,
    and keyword stuffing.
    Returns:
        - errors: list of warning/error dicts
        - honeypot_score: float (0-100)
    """
    errors = []
    honeypot_score = 0.0
    
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])
    
    claimed_years = profile.get("years_of_experience", 0.0)

    # 1. Impossible timelines & age/graduation anomalies
    grad_years = []
    for edu in education:
        if isinstance(edu, dict):
            ey = edu.get("end_year")
            if isinstance(ey, int) and ey > 1970:
                grad_years.append(ey)
                
    min_grad_year = min(grad_years) if grad_years else None
    
    first_job_year = None
    for job in career_history:
        if isinstance(job, dict):
            start_str = job.get("start_date")
            if isinstance(start_str, str) and len(start_str) >= 4:
                try:
                    yr = int(start_str[:4])
                    if first_job_year is None or yr < first_job_year:
                        first_job_year = yr
                except ValueError:
                    pass

    # Heuristic: First job starts way before graduation (e.g. > 6 years before)
    if min_grad_year and first_job_year:
        if min_grad_year - first_job_year > 6:
            errors.append({
                "code": "IMPOSSIBLE_WORK_GRADUATION_TIMELINE",
                "severity": "HIGH",
                "message": f"Candidate started first job in {first_job_year} but didn't graduate until {min_grad_year}"
            })
            honeypot_score += 40.0

    # Heuristic: Total experience claimed is impossible for graduation date
    if min_grad_year:
        current_year = 2026 # Reference year
        max_possible_exp = current_year - min_grad_year + 1
        if claimed_years > max_possible_exp + 2: # Allow small 2-year padding
            errors.append({
                "code": "IMPOSSIBLE_EXPERIENCE_DURATION",
                "severity": "HIGH",
                "message": f"Candidate claims {claimed_years} years of experience but graduated in {min_grad_year} (max realistic: {max_possible_exp} years)"
            })
            honeypot_score += 40.0

    # 2. Heuristics on copypasta description mismatches
    mismatches_found = 0
    for i, job in enumerate(career_history):
        if not isinstance(job, dict):
            continue
        title = job.get("title", "").lower()
        desc = job.get("description", "")
        
        # Check against templated patterns
        for key, info in TEMPLATE_PATTERNS.items():
            if re.search(info["pattern"], desc, re.IGNORECASE):
                # Check if title does not contain any allowed terms
                if not any(term in title for term in info["allowed_titles"]):
                    mismatches_found += 1
                    errors.append({
                        "code": "TITLE_DESCRIPTION_MISMATCH",
                        "severity": "HIGH",
                        "message": f"Job index {i} at '{job.get('company')}' has description text matching '{key}' but title is '{job.get('title')}'"
                    })
                    honeypot_score += 30.0

    # 3. Identical skill duration artifacts (common in raw synthetics)
    if len(skills) >= 5:
        durations = [s.get("duration_months") for s in skills if isinstance(s, dict) and s.get("duration_months") is not None]
        if len(durations) >= 5:
            # Check if all durations are identical or endorsements are identical
            unique_durs = set(durations)
            if len(unique_durs) == 1:
                errors.append({
                    "code": "SUSPICIOUS_SKILL_DISTRIBUTION",
                    "severity": "MEDIUM",
                    "message": "Candidate has multiple skills with identical duration months (synthetic pattern)"
                })
                honeypot_score += 25.0

    # 4. Keyword stuffing mismatch check (from JD: Marketing Manager with AI keywords)
    current_title = profile.get("current_title", "").lower()
    is_non_tech_title = any(t in current_title for t in ["marketing manager", "accountant", "customer support", "operations manager", "hr manager"])
    
    # Count AI skills
    ai_skills_count = 0
    for s in skills:
        if isinstance(s, dict):
            name = s.get("name", "").lower()
            if any(kw in name for kw in AI_ML_KEYWORDS):
                ai_skills_count += 1
                
    if is_non_tech_title and ai_skills_count >= 5:
        errors.append({
            "code": "KEYWORD_STUFFED_HONEYPOT",
            "severity": "HIGH",
            "message": f"Candidate title is '{profile.get('current_title')}' but lists {ai_skills_count} AI/ML keywords (clear honeypot indicators)"
        })
        honeypot_score += 50.0

    honeypot_score = max(0.0, min(100.0, honeypot_score))
    return errors, float(honeypot_score)
