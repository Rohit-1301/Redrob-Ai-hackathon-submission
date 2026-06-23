import datetime
import re
from typing import Dict, Any, List

def build_hover_details(candidate: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyzes the candidate profile and builds structured detail lists:
    - invalid_reasons: Reasons that make the profile strictly invalid.
    - quality_flags: Quality issues (including invalid reasons & other warnings).
    - honeypot_flags: Honeypot detections.
    - schema_flags: Missing keys, invalid types, empty mandatory sections.
    - career_flags: Overlaps, timeline issues, demotion flags.
    - skill_flags: Skill inflation, durations exceeding experience.
    - signal_flags: Suspicious behavioral activity.
    """
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    signals = candidate.get("redrob_signals", {})

    invalid_reasons = []
    info_flags = []
    honeypot_flags_list = []

    # --- 1. Career History Total Duration & Parsed Jobs ---
    total_months = sum(job.get("duration_months", 0) for job in career_history if isinstance(job, dict) and job.get("duration_months") is not None)
    profile_exp_years = profile.get("years_of_experience", 0.0)
    max_allowed_months = max(total_months, int(profile_exp_years * 12))

    # --- 2. Skill Durations Check ---
    for i, s in enumerate(skills):
        if not isinstance(s, dict):
            continue
        name = s.get("name", f"item_{i}")
        duration = s.get("duration_months")
        if duration is not None:
            if duration > (max_allowed_months + 6):
                # Major mismatch
                invalid_reasons.append(f"skill_duration_exceeds_career:{name}={duration}m>career={max_allowed_months}m")

    # --- 3. Schema & Section Missing Checks ---
    # Missing top-level keys
    for key in ["profile", "career_history", "skills", "redrob_signals", "education"]:
        if key not in candidate or candidate[key] is None:
            info_flags.append(f"schema_missing_section:{key}")
        elif key in ["career_history", "skills", "education"] and len(candidate[key]) == 0:
            info_flags.append(f"schema_empty_section:{key}")

    # Profile sub-keys
    for k in ["anonymized_name", "headline", "summary", "location", "country", "years_of_experience"]:
        if profile.get(k) is None or (isinstance(profile.get(k), str) and not profile.get(k).strip()):
            info_flags.append(f"schema_profile_missing_field:{k}")

    # Career history sub-keys
    for idx, job in enumerate(career_history):
        if not isinstance(job, dict):
            continue
        for k in ["company", "title", "start_date", "duration_months"]:
            if job.get(k) is None:
                invalid_reasons.append(f"career_item_{idx}_missing_field:{k}")

    # Skills sub-keys
    for idx, s in enumerate(skills):
        if not isinstance(s, dict):
            continue
        for k in ["name", "proficiency", "duration_months"]:
            if s.get(k) is None:
                invalid_reasons.append(f"skill_item_{idx}_missing_field:{k}")

    # Education sub-keys
    for idx, edu in enumerate(education):
        if not isinstance(edu, dict):
            continue
        for k in ["institution", "degree", "field_of_study", "start_year", "end_year"]:
            if edu.get(k) is None:
                invalid_reasons.append(f"education_item_{idx}_missing_field:{k}")

    # --- 4. Career Timeline & Chronology Checks ---
    parsed_jobs = []
    ref_date = datetime.date(2026, 6, 20)
    for idx, job in enumerate(career_history):
        if not isinstance(job, dict):
            continue
        comp = job.get("company", f"comp_{idx}")
        start_str = job.get("start_date")
        end_str = job.get("end_date")
        is_curr = job.get("is_current", False)
        duration = job.get("duration_months", 0)

        # Negative duration
        if duration < 0:
            info_flags.append(f"career_negative_duration:job_{idx}={duration}m")

        try:
            s_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else None
            e_date = datetime.datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else (ref_date if is_curr else None)

            if s_date:
                if s_date > ref_date:
                    info_flags.append(f"career_future_job_start:job_{idx}={start_str}")
                if e_date and e_date > ref_date and not is_curr:
                    info_flags.append(f"career_future_job_end:job_{idx}={end_str}")
                if e_date and s_date > e_date:
                    info_flags.append(f"career_invalid_chronology:job_{idx}_start={start_str}>end={end_str}")

                parsed_jobs.append((s_date, e_date, comp, idx))
        except ValueError:
            pass

    # Career experience mismatch vs claimed
    if total_months > 0:
        actual_yrs = total_months / 12.0
        exp_diff = abs(profile_exp_years - actual_yrs)
        if profile_exp_years > 0 and (exp_diff > 1.5 or (exp_diff / profile_exp_years) > 0.25):
            info_flags.append(f"career_experience_mismatch:claimed={profile_exp_years}y,actual={actual_yrs:.1f}y")

    # Overlapping jobs (> 90 days)
    parsed_jobs.sort(key=lambda x: x[0])
    for i in range(len(parsed_jobs) - 1):
        j1_start, j1_end, c1, idx1 = parsed_jobs[i]
        j2_start, j2_end, c2, idx2 = parsed_jobs[i+1]
        if j1_end and j2_start < j1_end:
            overlap_end = min(j1_end, j2_end) if j2_end else j1_end
            overlap_days = (overlap_end - j2_start).days
            if overlap_days > 90:
                info_flags.append(f"career_employment_overlap:job_{idx1}_overlaps_job_{idx2}={overlap_days}d")

    # Career demotion
    highest_lvl = 0
    def get_role_level(title: str) -> int:
        title = title.lower()
        if any(w in title for w in ["vp", "vice president", "director", "head", "chief", "cto", "cio", "founder"]):
            return 3
        if any(w in title for w in ["senior", "sr.", "lead", "principal", "manager"]):
            return 2
        if any(w in title for w in ["junior", "jr.", "associate", "intern", "trainee", "entry", "fresher"]):
            return 1
        return 0

    for job in career_history:
        if not isinstance(job, dict):
            continue
        lvl = get_role_level(job.get("title", ""))
        if lvl > 0:
            if lvl < highest_lvl and highest_lvl >= 3 and lvl == 1:
                info_flags.append("career_regression_anomaly:demotion_from_executive_to_junior")
            highest_lvl = max(highest_lvl, lvl)

    # Executive role with insufficient experience
    for job in career_history:
        if not isinstance(job, dict):
            continue
        lvl = get_role_level(job.get("title", ""))
        if lvl == 3 and (total_months / 12.0) < 2.0:
            info_flags.append("career_executive_role_with_low_experience")

    # --- 5. Skill Flags ---
    high_proficiency_skills = [s for s in skills if isinstance(s, dict) and s.get("proficiency") in ["advanced", "expert"]]
    if len(high_proficiency_skills) >= 15 and profile_exp_years < 3.0:
        info_flags.append(f"skill_inflation:expert_count={len(high_proficiency_skills)},experience={profile_exp_years}y")
    elif len(skills) >= 30 and profile_exp_years < 2.0:
        info_flags.append(f"skill_inflation_absolute:count={len(skills)},experience={profile_exp_years}y")

    # Skill-job consistency (no AI history for AI skills)
    ai_keywords = [
        "embeddings", "vector database", "hybrid search", "pinecone", "weaviate", 
        "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "ndcg", "mrr", 
        "map", "evaluation frameworks", "lora", "qlora", "peft", "fine-tuning", 
        "learning-to-rank", "xgboost", "neural ranking", "reranking", "llm", "nlp", 
        "retrieval", "search system", "recommendation", "dense retrieval", "rag",
        "retrieval-augmented generation", "machine learning", "deep learning", 
        "pytorch", "tensorflow", "scikit-learn"
    ]
    candidate_ai_skills = []
    for s in skills:
        if not isinstance(s, dict):
            continue
        s_name = s.get("name", "").lower()
        if any(k in s_name for k in ai_keywords):
            candidate_ai_skills.append(s.get("name"))

    if candidate_ai_skills:
        has_ai_history = False
        for job in career_history:
            if not isinstance(job, dict):
                continue
            title = job.get("title", "").lower()
            desc = job.get("description", "").lower()
            if any(k in title or k in desc for k in ai_keywords):
                has_ai_history = True
                break
        if not has_ai_history:
            info_flags.append("skill_no_history_match:claims_ai_skills_but_no_ai_work")

    # --- 6. Platform Behavioral Signal Flags ---
    if isinstance(signals, dict):
        comp = signals.get("profile_completeness_score", 0.0)
        if comp < 50.0:
            info_flags.append(f"signal_low_profile_completeness:{int(comp)}%")

        resp_rate = signals.get("recruiter_response_rate", 1.0)
        if resp_rate < 0.30:
            info_flags.append(f"signal_low_recruiter_response_rate:{resp_rate:.2f}")

        # Inactive login
        last_active_str = signals.get("last_active_date")
        if last_active_str:
            try:
                la_date = datetime.datetime.strptime(last_active_str, "%Y-%m-%d").date()
                days_inactive = (ref_date - la_date).days
                if days_inactive > 180:
                    info_flags.append(f"signal_inactive_{days_inactive}d_since_last_login")
            except ValueError:
                pass

        # Open to work flag
        if not signals.get("open_to_work_flag", True):
            info_flags.append("signal_not_open_to_work")

        # Notice period
        np_days = signals.get("notice_period_days", 90)
        if np_days > 90:
            info_flags.append(f"signal_long_notice_period:{np_days}d")

        # Verified elements
        if not signals.get("verified_email", True):
            info_flags.append("signal_email_not_verified")
        if not signals.get("verified_phone", True):
            info_flags.append("signal_phone_not_verified")
        if not signals.get("linkedin_connected", True):
            info_flags.append("signal_linkedin_not_connected")

        # Github Activity
        gh_score = signals.get("github_activity_score", -1.0)
        if gh_score == -1:
            info_flags.append("signal_no_github_linked")

    # --- 7. Honeypot & Copy-pasta Detections ---
    # Worked before college
    edu_years = [edu.get("start_year") for edu in education if isinstance(edu, dict) and edu.get("start_year")]
    if edu_years and parsed_jobs:
        earliest_edu_year = min(edu_years)
        earliest_job_start = parsed_jobs[0][0]
        if earliest_job_start.year < earliest_edu_year - 6:
            # We flag this as a critical honeypot timeline violation
            invalid_reasons.append(f"career_started_before_graduation:career_start={earliest_job_start.year},earliest_grad={earliest_edu_year}")

    # Notice period > 90 days as warning, signup date timeline contradiction
    signup_str = signals.get("signup_date")
    last_act_str = signals.get("last_active_date")
    if signup_str and last_act_str:
        try:
            s_up = datetime.datetime.strptime(signup_str, "%Y-%m-%d").date()
            l_act = datetime.datetime.strptime(last_act_str, "%Y-%m-%d").date()
            if l_act < s_up:
                invalid_reasons.append(f"signal_last_active_before_signup:{last_act_str}<{signup_str}")
        except ValueError:
            pass

    # Expected salary min > max
    salary_range = signals.get("expected_salary_range_inr_lpa", {})
    if isinstance(salary_range, dict):
        s_min = salary_range.get("min", 0)
        s_max = salary_range.get("max", 0)
        if s_min > s_max:
            info_flags.append(f"signal_salary_min_exceeds_max:{s_min}>{s_max}")

    # Template copy-paste mismatch
    template_patterns = {
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

    for idx, job in enumerate(career_history):
        if not isinstance(job, dict):
            continue
        title = job.get("title", "").lower()
        desc = job.get("description", "")
        for key, info in template_patterns.items():
            if re.search(info["pattern"], desc, re.IGNORECASE):
                if not any(term in title for term in info["allowed_titles"]):
                    invalid_reasons.append(f"career_job_{idx}_template_mismatch:desc={key},title='{job.get('title')}'")

    # Keyword stuffing for non-tech roles
    curr_title = profile.get("current_title", "").lower()
    is_non_tech = any(t in curr_title for t in ["marketing manager", "accountant", "customer support", "operations manager", "hr manager"])
    ai_skills_count = len(candidate_ai_skills)
    if is_non_tech and ai_skills_count >= 5:
        invalid_reasons.append(f"skill_keyword_stuffed_honeypot:title='{profile.get('current_title')}',ai_skills={ai_skills_count}")

    # Identical skill durations (synthetic pattern)
    if len(skills) >= 5:
        durs = [s.get("duration_months") for s in skills if isinstance(s, dict) and s.get("duration_months") is not None]
        if len(durs) >= 5 and len(set(durs)) == 1:
            info_flags.append(f"skill_suspicious_identical_durations:{durs[0]}m")

    # --- 8. Specific Rules for Hackathon Requirements ---
    # Assessments taken check
    assessment_scores = signals.get("skill_assessment_scores", {})
    if not assessment_scores or len(assessment_scores) == 0:
        info_flags.append("skill_no_assessments_taken")

    # JD-relevant skills check
    jd_required_skills = {
        "embeddings", "vector databases", "vector database", "hybrid search", 
        "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", 
        "faiss", "ndcg", "mrr", "map", "evaluation", "python"
    }
    candidate_skills_set = {s.get("name", "").lower() for s in skills if isinstance(s, dict)}
    matching_jd_skills = jd_required_skills.intersection(candidate_skills_set)
    if len(matching_jd_skills) == 0:
        info_flags.append("skill_no_jd_relevant_skills_for_ai_engineer_role")

    # Consulting firm only career
    consulting_companies = {
        "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
        "cognizant", "capgemini", "mindtree", "wipro limited", "infosys limited", 
        "tata consultancy", "cognizant technology solutions", "accenture services"
    }
    if career_history:
        all_consulting = True
        for job in career_history:
            if not isinstance(job, dict):
                continue
            comp = job.get("company", "").lower()
            if not any(c in comp for c in consulting_companies):
                all_consulting = False
                break
        if all_consulting:
            info_flags.append("career_consulting_firm_only")

    # Pure CV or speech only background
    cv_speech_keywords = {
        "computer vision", "object detection", "yolo", "segmentation", "opencv", 
        "speech recognition", "tts", "asr", "whisper", "speech-to-text", "text-to-speech",
        "robotics", "ros", "lidar"
    }
    has_cv_speech = any(any(kw in s.get("name", "").lower() for kw in cv_speech_keywords) for s in skills if isinstance(s, dict))
    has_nlp_ir = any(any(kw in s.get("name", "").lower() for kw in jd_required_skills) for s in skills if isinstance(s, dict))
    if has_cv_speech and not has_nlp_ir:
        info_flags.append("skill_pure_cv_speech_without_nlp_ir")

    # Job hopper (switches <= 18 months on average with >= 3 switches)
    if career_history and len(career_history) >= 3:
        avg_duration = total_months / len(career_history)
        if avg_duration <= 18.0:
            info_flags.append(f"career_job_hopper:average_duration={avg_duration:.1f}m")

    # Severe keyword stuffing (e.g. > 20 skills but < 10% career coverage)
    # Heuristic limit: if skills > 20 and average duration of skills is low
    if len(skills) > 20:
        avg_skill_dur = sum(s.get("duration_months", 0) for s in skills if isinstance(s, dict)) / len(skills)
        if total_months > 0 and (avg_skill_dur / total_months) < 0.10:
            invalid_reasons.append(f"skill_severe_keyword_stuffing:{len(skills)}_skills,{int(avg_skill_dur / total_months * 100)}%_career_coverage")

    # --- 9. Final Synthesis of Flags ---
    quality_flags = list(set(invalid_reasons + info_flags))

    # Segmentations
    schema_flags_list = [f for f in quality_flags if f.startswith("schema_") or f.startswith("signal_salary_min_exceeds_max")]
    career_flags_list = [f for f in quality_flags if f.startswith("career_")]
    skill_flags_list = [f for f in quality_flags if f.startswith("skill_")]
    signal_flags_list = [f for f in quality_flags if f.startswith("signal_") and not f.startswith("signal_salary_min_exceeds_max")]

    # Honeypot checks
    honeypot_flags_list = [
        f for f in quality_flags 
        if "honeypot" in f or "mismatch" in f or "identical" in f or "before_signup" in f or "before_graduation" in f
    ]

    return {
        "invalid_reasons": " | ".join(invalid_reasons),
        "quality_flags": " | ".join(quality_flags),
        "honeypot_flags": " | ".join(honeypot_flags_list),
        "schema_flags": " | ".join(schema_flags_list),
        "career_flags": " | ".join(career_flags_list),
        "skill_flags": " | ".join(skill_flags_list),
        "signal_flags": " | ".join(signal_flags_list)
    }
