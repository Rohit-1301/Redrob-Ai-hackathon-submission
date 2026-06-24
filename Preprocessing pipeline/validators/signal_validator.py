import datetime
from configs.config import REFERENCE_DATE

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def validate_signals(candidate: dict) -> tuple:
    """
    Validates all 23 redrob platform signals.
    Computes weighted behavioral_score and availability_score.
    Returns:
        - errors: list of warning/error dicts
        - behavioral_score: float (0-100)
        - availability_score: float (0-100)
    """
    errors = []
    signals = candidate.get("redrob_signals", {})
    if not isinstance(signals, dict):
        return errors, 0.0, 0.0

    # 1. Bounds Validation & Clean up
    completeness = signals.get("profile_completeness_score", 0.0)
    if not isinstance(completeness, (int, float)) or completeness < 0.0 or completeness > 100.0:
        errors.append({
            "code": "INVALID_SIGNAL_VALUE",
            "severity": "LOW",
            "message": f"profile_completeness_score ({completeness}) is out of bounds (0-100)"
        })
        completeness = max(0.0, min(100.0, float(completeness))) if isinstance(completeness, (int, float)) else 0.0

    resp_rate = signals.get("recruiter_response_rate", 0.0)
    if not isinstance(resp_rate, (int, float)) or resp_rate < 0.0 or resp_rate > 1.0:
        errors.append({
            "code": "INVALID_SIGNAL_VALUE",
            "severity": "LOW",
            "message": f"recruiter_response_rate ({resp_rate}) is out of bounds (0-1)"
        })
        resp_rate = max(0.0, min(1.0, float(resp_rate))) if isinstance(resp_rate, (int, float)) else 0.0

    int_comp_rate = signals.get("interview_completion_rate", 0.0)
    if not isinstance(int_comp_rate, (int, float)) or int_comp_rate < 0.0 or int_comp_rate > 1.0:
        errors.append({
            "code": "INVALID_SIGNAL_VALUE",
            "severity": "LOW",
            "message": f"interview_completion_rate ({int_comp_rate}) is out of bounds (0-1)"
        })
        int_comp_rate = max(0.0, min(1.0, float(int_comp_rate))) if isinstance(int_comp_rate, (int, float)) else 0.0

    offer_acc_rate = signals.get("offer_acceptance_rate", -1.0)
    if not isinstance(offer_acc_rate, (int, float)) or ((offer_acc_rate < 0.0 or offer_acc_rate > 1.0) and offer_acc_rate != -1.0):
        errors.append({
            "code": "INVALID_SIGNAL_VALUE",
            "severity": "LOW",
            "message": f"offer_acceptance_rate ({offer_acc_rate}) is out of bounds (0-1 or -1)"
        })
        offer_acc_rate = max(-1.0, min(1.0, float(offer_acc_rate))) if isinstance(offer_acc_rate, (int, float)) else -1.0

    gh_score = signals.get("github_activity_score", -1.0)
    if not isinstance(gh_score, (int, float)) or ((gh_score < 0.0 or gh_score > 100.0) and gh_score != -1.0):
        errors.append({
            "code": "INVALID_SIGNAL_VALUE",
            "severity": "LOW",
            "message": f"github_activity_score ({gh_score}) is out of bounds (0-100 or -1)"
        })
        gh_score = max(-1.0, min(100.0, float(gh_score))) if isinstance(gh_score, (int, float)) else -1.0

    # 2. Availability Score Calculation (max 100)
    availability_score = 0.0
    
    # Open to work flag (base weight: 40)
    if signals.get("open_to_work_flag", False):
        availability_score += 40.0
    
    # Last active recency (base weight: 30)
    last_active_str = signals.get("last_active_date")
    last_active_date = parse_date(last_active_str)
    if last_active_date:
        days_since_active = (REFERENCE_DATE - last_active_date).days
        if days_since_active <= 7:
            availability_score += 30.0
        elif days_since_active <= 30:
            availability_score += 20.0
        elif days_since_active <= 90:
            availability_score += 10.0
        elif days_since_active > 180:
            availability_score -= 10.0  # inactive penalty
    
    # Recruiter response rate (base weight: 20)
    availability_score += resp_rate * 20.0
    
    # Notice period days (base weight: 10)
    notice_days = signals.get("notice_period_days", 90)
    if notice_days <= 30:
        availability_score += 10.0
    elif notice_days <= 60:
        availability_score += 5.0
    elif notice_days > 90:
        availability_score -= 5.0

    availability_score = max(0.0, min(100.0, availability_score))

    # 3. Behavioral Score Calculation (max 100)
    behavioral_score = 0.0
    
    # Profile completeness contribution (max 30)
    behavioral_score += completeness * 0.3
    
    # Github activity contribution (max 15)
    if gh_score != -1.0:
        behavioral_score += gh_score * 0.15
    else:
        behavioral_score += 5.0  # baseline if no github
        
    # Endorsements contribution (max 10)
    endorsements = signals.get("endorsements_received", 0)
    behavioral_score += min(10.0, endorsements / 5.0)
    
    # Connections contribution (max 10)
    connections = signals.get("connection_count", 0)
    behavioral_score += min(10.0, connections / 50.0)
    
    # Verified elements (max 15)
    if signals.get("verified_email", False):
        behavioral_score += 5.0
    if signals.get("verified_phone", False):
        behavioral_score += 5.0
    if signals.get("linkedin_connected", False):
        behavioral_score += 5.0
        
    # Interview completion rate contribution (max 10)
    behavioral_score += int_comp_rate * 10.0
    
    # Offer acceptance rate contribution (max 10)
    if offer_acc_rate != -1.0:
        behavioral_score += offer_acc_rate * 10.0
    else:
        behavioral_score += 7.0  # baseline
        
    # Response time (max 10, min -10)
    resp_time = signals.get("avg_response_time_hours", 48.0)
    if resp_time <= 24.0:
        behavioral_score += 10.0
    elif resp_time <= 72.0:
        behavioral_score += 5.0
    elif resp_time > 168.0:
        behavioral_score -= 10.0

    behavioral_score = max(0.0, min(100.0, behavioral_score))
    
    return errors, float(behavioral_score), float(availability_score)
