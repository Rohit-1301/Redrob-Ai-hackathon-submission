from configs.config import (
    CONSULTING_COMPANIES, TARGET_LOCATIONS, AI_ML_KEYWORDS, 
    JD_REQUIRED_SKILLS, JD_PREFERRED_SKILLS, CV_SPEECH_KEYWORDS
)

def validate_jd_eligibility(candidate: dict) -> tuple:
    """
    Evaluates the candidate against the Senior AI Engineer Job Description (JD).
    Checks for mandatory requirements, positive indicators, and disqualifiers.
    Returns:
        - flags: list of string flags
        - disqualifiers: list of string reasons for disqualification
        - credibility_score: float (0-100)
    """
    flags = []
    disqualifiers = []
    
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    signals = candidate.get("redrob_signals", {})

    claimed_years = profile.get("years_of_experience", 0.0)
    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)

    # 1. Location Validation
    # Prefer Noida/Pune or target Indian hubs. Open to relocation.
    is_in_target_location = any(loc in location for loc in TARGET_LOCATIONS)
    is_in_india = "india" in country or any(loc in location for loc in ["pune", "noida", "chennai", "mumbai", "hyderabad", "bangalore", "bengaluru", "delhi", "gurgaon", "ncr"])
    
    if not is_in_india:
        if not willing_to_relocate:
            disqualifiers.append("LOCATION_OUTSIDE_INDIA")
            flags.append("LOCATION_DISQUALIFIED")
    elif not is_in_target_location:
        if not willing_to_relocate:
            # Not in target hub and not willing to relocate
            flags.append("LOCATION_OFF_TARGET")

    # 2. Experience Band Flag
    if claimed_years < 4.0 or claimed_years > 10.0:
        flags.append("OUTSIDE_EXPERIENCE_BAND")

    # 3. Consulting-Only Background Disqualifier
    # Check if all jobs in history are with consulting companies
    if career_history:
        all_consulting = True
        has_any_job = False
        for job in career_history:
            if isinstance(job, dict):
                has_any_job = True
                company = job.get("company", "").lower().strip()
                # Check if company name matches any consulting giant
                matches_consulting = any(c_co in company for c_co in CONSULTING_COMPANIES)
                if not matches_consulting:
                    all_consulting = False
                    break
        if has_any_job and all_consulting:
            disqualifiers.append("CONSULTING_ONLY_BACKGROUND")
            flags.append("CONSULTING_ONLY_DISQUALIFIER")

    # 4. Pure Research Background Disqualifier
    # If titles contain researcher/scientist and there is no product/engineering exposure in descriptions
    if career_history:
        has_prod_exp = False
        all_research_titles = True
        for job in career_history:
            if isinstance(job, dict):
                title = job.get("title", "").lower()
                desc = job.get("description", "").lower()
                
                # Check for research titles
                is_research_title = any(term in title for term in ["researcher", "research fellow", "scientist", "postdoc", "phd", "academic", "professor", "lecturer"])
                # If they have an engineer/developer title, then they are not pure research
                is_eng_title = any(term in title for term in ["engineer", "developer", "architect", "lead", "analyst", "manager", "programmer"])
                
                if is_eng_title and not is_research_title:
                    all_research_titles = False
                    
                # Look for production indicators
                if any(term in desc for term in ["production", "deploy", "scale", "served", "pipeline", "real users", "latency", "system", "infrastructure"]):
                    has_prod_exp = True
                    
        if all_research_titles and not has_prod_exp:
            disqualifiers.append("PURE_RESEARCH_BACKGROUND")
            flags.append("PURE_RESEARCH_DISQUALIFIER")

    # 5. LangChain-only Short Experience (Under 12 months with no pre-LLM experience)
    # Check if they have LangChain/OpenAI skills, but they are all very recent (short duration)
    # and they have no older core ML skills (like regression, random forest, xgboost, NLP, FAISS, search, etc.)
    has_llm_skills = False
    max_llm_duration = 0
    has_pre_llm_ml = False
    
    for s in skills:
        if isinstance(s, dict):
            name = s.get("name", "").lower()
            dur = s.get("duration_months", 0)
            
            # Identify LLM skills
            if any(term in name for term in ["langchain", "llamaindex", "openai", "gpt", "chatgpt", "large language model", "llm"]):
                has_llm_skills = True
                max_llm_duration = max(max_llm_duration, dur)
            # Identify Pre-LLM / Core ML skills
            elif any(term in name for term in ["nlp", "retrieval", "search", "ranking", "xgboost", "classification", "regression", "svm", "random forest", "pytorch", "tensorflow", "vector", "embeddings"]):
                if dur > 12: # Significant pre-LLM experience
                    has_pre_llm_ml = True

    if has_llm_skills and max_llm_duration < 12 and not has_pre_llm_ml:
        disqualifiers.append("LANGCHAIN_ONLY_SHORT_EXPERIENCE")
        flags.append("LANGCHAIN_ONLY_DISQUALIFIER")

    # 6. Pure Computer Vision / Speech Disqualifier
    # Has CV/Speech keywords but zero NLP/IR keywords
    has_cv_speech = False
    has_nlp_ir = False
    for s in skills:
        if isinstance(s, dict):
            name = s.get("name", "").lower()
            if any(kw in name for kw in CV_SPEECH_KEYWORDS):
                has_cv_speech = True
            if any(kw in name for kw in JD_REQUIRED_SKILLS) or any(kw in name for kw in JD_PREFERRED_SKILLS):
                has_nlp_ir = True

    if has_cv_speech and not has_nlp_ir:
        disqualifiers.append("PURE_CV_SPEECH_BACKGROUND")
        flags.append("PURE_CV_SPEECH_DISQUALIFIER")

    # 7. Title Chaser (switches company every <= 1.5 years on average, with >= 3 switches)
    if career_history and len(career_history) >= 3:
        total_dur = sum(job.get("duration_months", 0) for job in career_history if isinstance(job, dict))
        avg_job_duration = total_dur / len(career_history)
        if avg_job_duration <= 18:  # 1.5 years
            disqualifiers.append("TITLE_CHASER_JOB_HOPPER")
            flags.append("TITLE_CHASER_DISQUALIFIER")

    # 8. Check production AI experience (Not a disqualifier but key positive flag)
    desc_text = " ".join([job.get("description", "").lower() for job in career_history if isinstance(job, dict)])
    has_production_text = any(term in desc_text for term in ["production", "deploy", "scale", "real users", "latency", "system", "infrastructure"])
    
    if not has_production_text and any(s.get("name", "").lower() in JD_REQUIRED_SKILLS for s in skills if isinstance(s, dict)):
        flags.append("LACKS_PRODUCTION_AI")

    # 9. Compute Credibility Score (0-100)
    # Credibility depends on education tiers, verified markers, platform activity, and company pedigree.
    credibility_score = 30.0  # Base level

    # Education Pedigree
    edu_pedigree_points = 0
    for edu in education:
        if isinstance(edu, dict):
            tier = edu.get("tier", "unknown")
            if tier == "tier_1":
                edu_pedigree_points = max(edu_pedigree_points, 30)
            elif tier == "tier_2":
                edu_pedigree_points = max(edu_pedigree_points, 15)
            elif tier == "tier_3":
                edu_pedigree_points = max(edu_pedigree_points, 5)
    credibility_score += edu_pedigree_points

    # Verified email/phone
    if signals.get("verified_email", False):
        credibility_score += 10.0
    if signals.get("verified_phone", False):
        credibility_score += 10.0
        
    # Github activity
    gh_score = signals.get("github_activity_score", -1)
    if gh_score >= 50:
        credibility_score += 10.0
    elif gh_score >= 20:
        credibility_score += 5.0
        
    # Company Pedigree (if they have worked in a product company size 201-1000 or 1001-5000 and not consulting)
    has_product_co = False
    for job in career_history:
        if isinstance(job, dict):
            co_size = job.get("company_size", "")
            comp = job.get("company", "").lower()
            if co_size in ["51-200", "201-500", "501-1000", "1001-5000"] and not any(c_co in comp for c_co in CONSULTING_COMPANIES):
                has_product_co = True
                break
    if has_product_co:
        credibility_score += 10.0

    credibility_score = max(0.0, min(100.0, credibility_score))
    
    return flags, disqualifiers, float(credibility_score)
