import re

CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")

def validate_schema(candidate: dict) -> list:
    """
    Validates the high-level schema of a candidate profile.
    Returns a list of error dictionaries containing:
        - code: error category code
        - severity: HIGH, MEDIUM, LOW
        - message: human-readable explanation
    """
    errors = []

    # 1. Check top-level required fields
    required_top_level = ["candidate_id", "profile", "career_history", "education", "skills", "redrob_signals"]
    for field in required_top_level:
        if field not in candidate or candidate[field] is None:
            errors.append({
                "code": f"MISSING_{field.upper()}",
                "severity": "HIGH",
                "message": f"Candidate is missing the required top-level field: '{field}'"
            })
            continue

    # If top-level fields are missing, return early to prevent nested errors
    if any(e["severity"] == "HIGH" for e in errors):
        return errors

    # 2. Validate Candidate ID
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str):
        errors.append({
            "code": "INVALID_ID_TYPE",
            "severity": "HIGH",
            "message": f"candidate_id must be a string, got {type(candidate_id).__name__}"
        })
    elif not CANDIDATE_ID_PATTERN.match(candidate_id):
        errors.append({
            "code": "MALFORMED_ID",
            "severity": "HIGH",
            "message": f"candidate_id '{candidate_id}' does not match pattern CAND_XXXXXXX"
        })

    # 3. Validate Profile Structure
    profile = candidate.get("profile")
    if not isinstance(profile, dict):
        errors.append({
            "code": "INVALID_PROFILE_TYPE",
            "severity": "HIGH",
            "message": "profile must be an object"
        })
    else:
        profile_required = ["anonymized_name", "headline", "summary", "location", "country", "years_of_experience", "current_title"]
        for p_field in profile_required:
            val = profile.get(p_field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append({
                    "code": f"MISSING_PROFILE_{p_field.upper()}",
                    "severity": "MEDIUM",
                    "message": f"Candidate profile is missing or empty for: '{p_field}'"
                })

    # 4. Validate Career History
    career_history = candidate.get("career_history")
    if not isinstance(career_history, list):
        errors.append({
            "code": "INVALID_CAREER_HISTORY_TYPE",
            "severity": "HIGH",
            "message": "career_history must be a list/array"
        })
    else:
        if len(career_history) == 0:
            errors.append({
                "code": "EMPTY_CAREER_HISTORY",
                "severity": "HIGH",
                "message": "Candidate has no employment history listed"
            })
        for i, job in enumerate(career_history):
            if not isinstance(job, dict):
                errors.append({
                    "code": "INVALID_JOB_RECORD_TYPE",
                    "severity": "HIGH",
                    "message": f"Job entry at index {i} is not a valid object"
                })
                continue
            job_required = ["company", "title", "start_date", "duration_months", "is_current"]
            for j_field in job_required:
                if job.get(j_field) is None:
                    errors.append({
                        "code": f"MISSING_JOB_{j_field.upper()}",
                        "severity": "MEDIUM",
                        "message": f"Job entry at index {i} is missing field: '{j_field}'"
                    })

    # 5. Validate Skills
    skills = candidate.get("skills")
    if not isinstance(skills, list):
        errors.append({
            "code": "INVALID_SKILLS_TYPE",
            "severity": "HIGH",
            "message": "skills must be a list/array"
        })
    else:
        if len(skills) == 0:
            errors.append({
                "code": "MISSING_SKILLS",
                "severity": "HIGH",
                "message": "Candidate has no listed skills"
            })
        for i, skill in enumerate(skills):
            if not isinstance(skill, dict):
                errors.append({
                    "code": "INVALID_SKILL_RECORD_TYPE",
                    "severity": "MEDIUM",
                    "message": f"Skill entry at index {i} is not a valid object"
                })
                continue
            skill_required = ["name", "proficiency", "endorsements"]
            for s_field in skill_required:
                if skill.get(s_field) is None:
                    errors.append({
                        "code": f"MISSING_SKILL_{s_field.upper()}",
                        "severity": "MEDIUM",
                        "message": f"Skill entry at index {i} is missing field: '{s_field}'"
                    })

    # 6. Validate Signals
    signals = candidate.get("redrob_signals")
    if not isinstance(signals, dict):
        errors.append({
            "code": "INVALID_SIGNALS_TYPE",
            "severity": "HIGH",
            "message": "redrob_signals must be an object"
        })

    return errors
