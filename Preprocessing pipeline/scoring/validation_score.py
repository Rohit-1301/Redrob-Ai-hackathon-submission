def compute_validation_score(
    schema_errors: list,
    career_errors: list,
    skill_errors: list,
    signal_errors: list,
    honeypot_errors: list,
    honeypot_score: float,
    behavioral_score: float,
    disqualifiers: list
) -> tuple:
    """
    Computes validation_score (0-100) and decides validation_status based on deductions.
    Returns:
        - score: float (0-100)
        - status: str (VALID, REVIEW, WEAK, INVALID)
        - penalties_reasons: list of strings describing the applied deductions
    """
    score = 100.0
    penalties_reasons = []

    # 1. Schema Quality deductions
    schema_penalty = 0.0
    for err in schema_errors:
        if err["severity"] == "HIGH":
            schema_penalty += 30.0
        elif err["severity"] == "MEDIUM":
            schema_penalty += 10.0
    if schema_penalty > 0:
        deduction = min(40.0, schema_penalty)
        score -= deduction
        penalties_reasons.append(f"Schema quality issues: {schema_errors[0]['message']} (-{deduction:.0f})")

    # 2. Career Consistency deductions
    career_penalty = 0.0
    career_desc = ""
    for err in career_errors:
        code = err["code"]
        if code in ["FUTURE_JOB_START", "FUTURE_JOB_END", "INVALID_JOB_CHRONOLOGY"]:
            career_penalty += 15.0
            if not career_desc: career_desc = err["message"]
        elif code == "NEGATIVE_JOB_DURATION":
            career_penalty += 20.0
            if not career_desc: career_desc = err["message"]
        elif code == "EXPERIENCE_MISMATCH":
            career_penalty += 10.0
            if not career_desc: career_desc = err["message"]
        elif code == "EMPLOYMENT_OVERLAP":
            career_penalty += 10.0
            if not career_desc: career_desc = err["message"]
        elif code in ["CAREER_REGRESSION_ANOMALY", "INSUFFICIENT_EXP_FOR_EXEC_ROLE"]:
            career_penalty += 15.0
            if not career_desc: career_desc = err["message"]
            
    if career_penalty > 0:
        deduction = min(35.0, career_penalty)
        score -= deduction
        penalties_reasons.append(f"Career consistency issue: {career_desc} (-{deduction:.0f})")

    # 3. Skill Credibility deductions
    skill_penalty = 0.0
    skill_desc = ""
    for err in skill_errors:
        code = err["code"]
        if code in ["SKILL_INFLATION", "SKILL_INFLATION_ABSOLUTE"]:
            skill_penalty += 15.0
            if not skill_desc: skill_desc = err["message"]
        elif code == "SKILL_DURATION_MISMATCH":
            skill_penalty += 15.0
            if not skill_desc: skill_desc = err["message"]
        elif code == "SKILL_EMPLOYMENT_INCONSISTENCY":
            skill_penalty += 10.0
            if not skill_desc: skill_desc = err["message"]
            
    if skill_penalty > 0:
        deduction = min(35.0, skill_penalty)
        score -= deduction
        penalties_reasons.append(f"Skill credibility issue: {skill_desc} (-{deduction:.0f})")

    # 4. Behavioral Quality deductions (does not invalidate alone)
    behavioral_penalty = 0.0
    if behavioral_score < 40.0:
        behavioral_penalty += 15.0
    elif behavioral_score < 60.0:
        behavioral_penalty += 7.0
        
    for err in signal_errors:
        if err["code"] == "INVALID_SIGNAL_VALUE":
            behavioral_penalty += 5.0
            
    if behavioral_penalty > 0:
        deduction = min(25.0, behavioral_penalty)
        score -= deduction
        penalties_reasons.append(f"Weak platform activity behavior score of {behavioral_score:.1f} (-{deduction:.0f})")

    # 5. Honeypot deductions
    if honeypot_score > 0:
        deduction = min(80.0, honeypot_score * 0.8)
        score -= deduction
        honeypot_desc = honeypot_errors[0]["message"] if honeypot_errors else "Fraud indicator risk"
        penalties_reasons.append(f"Honeypot risk: {honeypot_desc} (-{deduction:.0f})")

    # Ensure score bounds
    score = max(0.0, min(100.0, score))

    # 6. Critical Failure Overrides
    if disqualifiers:
        score = min(35.0, score)
        penalties_reasons.append(f"DISQUALIFIED: {', '.join(disqualifiers)}")
        
    if honeypot_score >= 40.0:
        score = min(35.0, score)
        penalties_reasons.append("Capped due to high honeypot probability")

    # Status classification
    if score >= 80.0:
        status = "VALID"
    elif score >= 60.0:
        status = "REVIEW"
    elif score >= 40.0:
        status = "WEAK"
    else:
        status = "INVALID"

    return float(score), status, penalties_reasons
