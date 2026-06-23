import datetime
from configs.config import REFERENCE_DATE

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def validate_career(candidate: dict) -> list:
    """
    Validates candidate's career history chronology, overlaps, duration anomalies,
    and progression sequence.
    """
    errors = []
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    
    if not isinstance(career_history, list) or len(career_history) == 0:
        return errors

    claimed_years = profile.get("years_of_experience", 0.0)
    total_months = 0
    parsed_jobs = []

    # 1. Individual Job Date Chronology and Future Checks
    for i, job in enumerate(career_history):
        if not isinstance(job, dict):
            continue
        
        comp = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        start_str = job.get("start_date")
        end_str = job.get("end_date")
        is_current = job.get("is_current", False)
        duration = job.get("duration_months", 0)

        start_date = parse_date(start_str)
        end_date = parse_date(end_str) if not is_current else REFERENCE_DATE

        # Check negative duration in schema but double check here
        if duration < 0:
            errors.append({
                "code": "NEGATIVE_JOB_DURATION",
                "severity": "HIGH",
                "message": f"Job at '{comp}' has a negative duration of {duration} months"
            })

        # Check future dates
        if start_date and start_date > REFERENCE_DATE:
            errors.append({
                "code": "FUTURE_JOB_START",
                "severity": "HIGH",
                "message": f"Job at '{comp}' starts in the future: {start_str}"
            })
        if end_date and end_date > REFERENCE_DATE and not is_current:
            errors.append({
                "code": "FUTURE_JOB_END",
                "severity": "HIGH",
                "message": f"Job at '{comp}' ends in the future: {end_str}"
            })

        # Chronology
        if start_date and end_date and start_date > end_date:
            errors.append({
                "code": "INVALID_JOB_CHRONOLOGY",
                "severity": "HIGH",
                "message": f"Job at '{comp}' has start_date '{start_str}' after end_date '{end_str}'"
            })

        # Accumulate total experience months
        if duration > 0:
            total_months += duration

        if start_date and end_date:
            parsed_jobs.append({
                "company": comp,
                "title": title.lower(),
                "start": start_date,
                "end": end_date,
                "duration": duration
            })

    # 2. Experience Mismatch
    actual_years = total_months / 12.0
    experience_diff = abs(claimed_years - actual_years)
    # Flag large mismatch (e.g. difference is greater than 1.5 years or 25% of claimed experience)
    if claimed_years > 0 and (experience_diff > 1.5 or (experience_diff / claimed_years) > 0.25):
        errors.append({
            "code": "EXPERIENCE_MISMATCH",
            "severity": "MEDIUM",
            "message": f"Claimed experience ({claimed_years} yrs) differs significantly from career history sum ({actual_years:.1f} yrs)"
        })

    # 3. Employment Overlap
    # Sort parsed jobs chronologically by start date
    parsed_jobs.sort(key=lambda x: x["start"])
    for i in range(len(parsed_jobs)):
        for j in range(i + 1, len(parsed_jobs)):
            job1 = parsed_jobs[i]
            job2 = parsed_jobs[j]
            # Check overlap between job1 and job2
            # Overlap exists if job2 start is before job1 end
            if job2["start"] < job1["end"]:
                # Calculate overlap duration in days
                overlap_end = min(job1["end"], job2["end"])
                overlap_days = (overlap_end - job2["start"]).days
                # If overlap is more than 90 days (3 months), flag as suspicious
                if overlap_days > 90:
                    errors.append({
                        "code": "EMPLOYMENT_OVERLAP",
                        "severity": "MEDIUM",
                        "message": f"Suspicious employment overlap ({overlap_days} days) between '{job1['company']}' ({job1['title']}) and '{job2['company']}' ({job2['title']})"
                    })

    # 4. Career Progression Anomalies
    # Chronological title check: check if Junior role starts after holding a Senior/VP/Director role
    highest_level = 0  # 0: None, 1: Junior, 2: Senior, 3: VP/Director/Executive
    
    def get_title_level(title_str):
        # High titles
        if any(term in title_str for term in ["vp", "vice president", "director", "head of", "chief", "cto", "cio", "founder"]):
            return 3
        # Senior titles
        elif any(term in title_str for term in ["senior", "sr.", "lead", "principal", "manager"]):
            return 2
        # Junior titles
        elif any(term in title_str for term in ["junior", "jr.", "associate", "intern", "trainee", "entry", "fresher"]):
            return 1
        return 0

    for job in parsed_jobs:
        lvl = get_title_level(job["title"])
        if lvl > 0:
            if lvl < highest_level:
                # If current job level is lower than a previously held job level, flag it (excluding transitions from Senior to VP, etc.)
                # E.g. we had a VP/Director role (lvl 3) or Senior role (lvl 2) and then transitioned to a Junior/Intern role (lvl 1)
                if highest_level >= 3 and lvl == 1:
                    errors.append({
                        "code": "CAREER_REGRESSION_ANOMALY",
                        "severity": "HIGH",
                        "message": f"Demotion anomaly: Candidate held an executive/VP role before a junior/intern role"
                    })
                elif highest_level == 3 and lvl == 2:
                    # VP to Senior is common in startups, but let's log a lower severity flag if needed
                    pass
            highest_level = max(highest_level, lvl)

    # Check for Director or VP with extremely low experience
    for job in parsed_jobs:
        lvl = get_title_level(job["title"])
        if lvl == 3: # VP / Director
            # If total actual experience is less than 2.0 years, this is highly suspicious
            if actual_years < 2.0:
                errors.append({
                    "code": "INSUFFICIENT_EXP_FOR_EXEC_ROLE",
                    "severity": "HIGH",
                    "message": f"Candidate holds an executive/VP/Director title ('{job['title']}') with only {actual_years:.1f} years of total experience"
                })

    return errors
