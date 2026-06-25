import json
from datetime import datetime
import math
import os

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    np = None
    SentenceTransformer = None

# Real-world founding years for the startups in the company list
FOUNDING_YEARS = {
    "sarvam ai": 2023,
    "krutrim": 2023,
    "rephrase.ai": 2019,
    "observe.ai": 2017,
    "yellow.ai": 2016,
    "saarthi.ai": 2017,
    "verloop.io": 2015,
    "wysa": 2015,
    "niramai": 2016,
    "aganitha": 2017,
    "cred": 2018,
    "phonepe": 2015,
    "dream11": 2008,
    "swiggy": 2014,
    "razorpay": 2014,
    "meesho": 2015,
    "unacademy": 2015,
    "upgrad": 2015,
    "freshworks": 2010,
    "flipkart": 2007,
    "inmobi": 2007,
    "zomato": 2008,
    "ola": 2010,
    "paytm": 2010,
    "vedantu": 2011,
    "locobuzz": 2015,
    "mad street den": 2013,
    "glance": 2019,
}


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None


def check_honeypot(candidate):
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    
    # Rule A: Expert skill with 0 duration
    expert_0 = sum(
        1
        for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    )
    
    if expert_0 > 0:
        return True, f"Expert skill with 0 duration: {expert_0} count"

    # Rule B: Stated duration exceeds calendar delta + 3 months
    # Rule C: Company founding year violations
    for job in career:
        comp = job.get("company", "").strip().lower()
        start = parse_date(job.get("start_date"))
        stated_dur = job.get("duration_months", 0)

        if start:
            end = parse_date(job.get("end_date"))
            if end:
                delta = (end.year - start.year) * 12 + (end.month - start.month)
            else:
                delta = (2026 - start.year) * 12 + (
                    6 - start.month
                )  # June 2026 current date

            if stated_dur > delta + 3:
                return True, f"Job duration mismatch at {comp}: stated {stated_dur} months, calendar {delta} months"

        if comp in FOUNDING_YEARS:
            founding = FOUNDING_YEARS[comp]
            if start and start.year < founding:
                return True, f"Started at {comp} in {start.year}, but company was founded in {founding}"
            max_possible = (2026 - founding) * 12 + 6
            if stated_dur > max_possible:
                return True, f"Job duration {stated_dur} months at {comp} exceeds company age since founding in {founding}"

    return False, ""


def score_candidate(candidates, jd):
    res = []

    # ----------------------------------------------------
    # Load Precomputed Embeddings (if available)
    # ----------------------------------------------------
    embeddings_dict = {}
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    embeddings_path = os.path.join(project_root, "data", "embeddings.npz")
    if not os.path.exists(embeddings_path):
        embeddings_path = "embeddings.npz"
    jd_vector = None

    if (
        np is not None
        and SentenceTransformer is not None
        and os.path.exists(embeddings_path)
    ):
        try:
            print(f"Loading precomputed candidate embeddings from {embeddings_path}...")
            data = np.load(embeddings_path)
            ids = data["ids"]
            vectors = data["vectors"]
            embeddings_dict = {cid: vec for cid, vec in zip(ids, vectors)}

            print("Encoding job description using local SentenceTransformer model...")
            # We enforce cpu usage to ensure compliance with compute constraints
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

            jd_text = " | ".join(
                [
                    " ".join(jd.get("target_titles", [])),
                    " ".join(jd.get("required_skills", [])),
                    " ".join(jd.get("preferred_skills", [])),
                    " ".join(jd.get("positive_signals", [])),
                ]
            )
            jd_vector = model.encode(jd_text, convert_to_numpy=True)
            jd_norm = np.linalg.norm(jd_vector)
            if jd_norm > 0:
                jd_vector = jd_vector / jd_norm
            print("Job description embedded successfully.")
        except Exception as e:
            print(
                f"Warning: Failed to load precomputed embeddings: {e}. Using keyword fallback for semantic matching."
            )
            jd_vector = None

    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        profile = candidate.get("profile", {})
        skills = candidate.get("skills", [])
        career = candidate.get("career_history", [])
        signals = candidate.get("redrob_signals", {})

        name = profile.get("anonymized_name", "Unknown")

        # ----------------------------------------------------
        # 1. HONEYPOT HARD FILTER
        # ----------------------------------------------------
        is_honeypot, honeypot_reason = check_honeypot(candidate)

        if is_honeypot:
            # Assign -999.0 score to filter it completely out of the top 100
            res.append(
                {
                    "candidate_id": candidate_id,
                    "name": name,
                    "score": -999.0,
                    "reasoning": f"Disqualified: {honeypot_reason}",
                }
            )
            continue

        # ----------------------------------------------------
        # 2. INDIVIDUAL COMPONENT SCORING
        # ----------------------------------------------------

        # A. Career Score (0.35)
        career_score = 0.0

        # Title matching (weight: 0.15)
        headline = profile.get("headline", "").lower()
        curr_title = profile.get("current_title", "").lower()
        title_match_points = 0.0

        for target in jd.get("target_titles", []):
            t_low = target.lower()
            if t_low == curr_title or t_low == headline:
                title_match_points = max(title_match_points, 1.0)
            elif t_low in curr_title or t_low in headline:
                title_match_points = max(title_match_points, 0.8)

        # Company context (weight: 0.10)
        # Avoid pure consulting background unless they have product/startup experience
        has_product = False
        has_consulting = False
        consulting_list = jd.get("consulting_companies", [])

        for job in career:
            comp = job.get("company", "").strip().lower()
            if comp in consulting_list:
                has_consulting = True
            else:
                has_product = True

        company_score = 1.0
        if has_consulting and not has_product:
            company_score = 0.0
        elif has_consulting and has_product:
            company_score = 0.6

        # Description keywords / positive signals (weight: 0.10)
        desc_matches = 0
        desc_penalty = 0
        desc_text = " ".join(job.get("description", "").lower() for job in career)

        for sig in jd.get("positive_signals", []):
            if sig.lower() in desc_text:
                desc_matches += 1

        for pat in jd.get("negative_patterns", []):
            if pat.lower() in desc_text or pat.lower() in headline:
                desc_penalty += 1

        desc_score = min(desc_matches * 0.2, 1.0) - (desc_penalty * 0.3)
        desc_score = max(0.0, min(1.0, desc_score))

        career_score = (
            0.15 * title_match_points + 0.10 * company_score + 0.10 * desc_score
        )
        # Scale career_score so its maximum contribution is 1.0 (then multiplied by 0.35 in final sum)
        career_score = career_score / 0.35

        # B. Semantic Score (0.20)
        semantic_score = 0.0
        if jd_vector is not None and candidate_id in embeddings_dict:
            cand_vector = embeddings_dict[candidate_id]
            cand_norm = np.linalg.norm(cand_vector)
            if cand_norm > 0:
                # Cosine similarity
                sim = np.dot(cand_vector, jd_vector) / cand_norm
                # Scale sim (typically in [-1, 1], map to [0, 1])
                semantic_score = max(0.0, min(1.0, (sim + 1.0) / 2.0))
                # Boost if similarity is strong
                if sim > 0.4:
                    semantic_score = min(1.0, semantic_score + 0.1)
        else:
            # Fallback to keyword summary match
            summary = profile.get("summary", "").lower()
            matched_keywords = 0
            all_keywords = jd.get("required_skills", []) + jd.get(
                "preferred_skills", []
            )
            for kw in all_keywords:
                if kw.lower() in summary:
                    matched_keywords += 1
            semantic_score = min(matched_keywords / 10.0, 1.0)

        # C. Skill Score (0.15)
        required = jd.get("required_skills", [])
        preferred = jd.get("preferred_skills", [])

        skill_points = 0.0
        max_possible_points = len(required) * 2.0 + len(preferred) * 1.0

        for sk in skills:
            sk_name = sk.get("name", "").strip().lower()
            prof = sk.get("proficiency", "beginner").strip().lower()
            endorsements = sk.get("endorsements", 0)

            # Proficiency multiplier
            prof_mult = 0.2
            if prof == "expert":
                prof_mult = 1.0
            elif prof == "advanced":
                prof_mult = 0.8
            elif prof == "intermediate":
                prof_mult = 0.5

            endorsement_bonus = 1.0 + math.log1p(endorsements)

            if sk_name in required:
                skill_points += 2.0 * prof_mult * endorsement_bonus
            elif sk_name in preferred:
                skill_points += 1.0 * prof_mult * endorsement_bonus

        skill_score = min(skill_points / (max_possible_points + 1e-6), 1.0)

        # D. Behavior Score (0.15)
        # 1. Recruiter Response Rate
        response_rate = signals.get("recruiter_response_rate", 0.0)

        # 2. Last Active Recency
        last_active = parse_date(signals.get("last_active_date", ""))
        recency_score = 0.1
        if last_active:
            # Months since June 2026
            months_ago = (2026 - last_active.year) * 12 + (6 - last_active.month)
            if months_ago <= 3:
                recency_score = 1.0
            elif months_ago <= 6:
                recency_score = 0.6
            elif months_ago <= 12:
                recency_score = 0.3

        # 3. Notice Period
        notice_days = signals.get("notice_period_days", 180)
        notice_score = 0.2
        if notice_days <= 30:
            notice_score = 1.0
        elif notice_days <= 60:
            notice_score = 0.7

        # 4. Location & Relocation
        location = profile.get("location", "").lower()
        country = profile.get("country", "").lower()
        relocate = signals.get("willing_to_relocate", False)

        in_pref_location = (
            any(loc in location for loc in jd.get("locations", []))
            or country != "india"
        )
        location_score = 1.0 if (in_pref_location or relocate) else 0.3

        # Weighted behavior score (scale to max 1.0)
        behavior_score = (
            0.4 * response_rate
            + 0.2 * recency_score
            + 0.2 * notice_score
            + 0.2 * location_score
        )

        # E. Experience Score (0.10)
        years_exp = profile.get("years_of_experience", 0.0)
        min_exp, max_exp = jd.get("experience_range", (5, 9))

        if min_exp <= years_exp <= max_exp:
            experience_score = 1.0
        elif (min_exp - 1) <= years_exp <= (max_exp + 3):
            experience_score = 0.7
        else:
            experience_score = 0.2

        # F. Stability Score (0.05)
        avg_tenure = 0.0
        if len(career) > 0:
            total_months = sum(job.get("duration_months", 0) for job in career)
            avg_tenure = total_months / len(career)

        if avg_tenure >= 36:  # 3+ years average
            stability_score = 1.0
        elif avg_tenure >= 24:  # 2+ years average
            stability_score = 0.8
        elif avg_tenure >= 18:  # 1.5+ years average
            stability_score = 0.5
        else:
            stability_score = 0.2

        # ----------------------------------------------------
        # 3. COMBINE SCORES & APPLY IRRELEVANT TITLE PENALTY
        # ----------------------------------------------------
        final_score = (
            0.35 * career_score
            + 0.20 * semantic_score
            + 0.15 * skill_score
            + 0.15 * behavior_score
            + 0.10 * experience_score
            + 0.05 * stability_score
        )

        # Irrelevant Title Check (Keyword Stuffers Trap)
        irrelevant_keywords = [
            "marketing",
            "sales",
            "hr manager",
            "human resources",
            "operations manager",
            "accountant",
            "accounting",
            "civil engineer",
            "mechanical engineer",
            "graphic designer",
            "customer support",
            "support agent",
            "content writer",
            "brand designer",
            "operations specialist",
            "sales executive",
            "recruiter",
            "operations manager",
            "office manager",
        ]

        is_irrelevant_title = False
        curr_title_lower = curr_title.lower()
        headline_lower = headline.lower()

        if title_match_points == 0.0:
            for kw in irrelevant_keywords:
                if kw in curr_title_lower or kw in headline_lower:
                    is_irrelevant_title = True
                    break

        if is_irrelevant_title:
            # Penalize heavily (subtract 0.35 to push keyword stuffers down)
            final_score = max(0.0, final_score - 0.35)

        # ----------------------------------------------------
        # 4. GENERATE CUSTOM REASONING
        # ----------------------------------------------------
        # Extract concrete facts from the profile
        exp_text = f"{years_exp:.1f} years of experience"
        title_text = curr_title or headline or "Engineer"
        company_text = f"at {career[0].get('company')}" if len(career) > 0 else ""

        reasons_list = []
        if title_match_points >= 0.8:
            reasons_list.append("fits the target title profile")
        elif is_irrelevant_title:
            reasons_list.append("non-AI/engineering background")

        # Top skills matches
        matched_skills = [
            sk.get("name")
            for sk in skills
            if sk.get("name", "").strip().lower() in required
        ]
        if matched_skills:
            reasons_list.append(f"has strong skills in {', '.join(matched_skills[:3])}")

        if company_score == 1.0:
            reasons_list.append("has solid product-company background")
        elif company_score == 0.0:
            reasons_list.append("has a consulting-heavy history")

        if response_rate >= 0.7:
            reasons_list.append("shows excellent response rate")

        if notice_days <= 30:
            reasons_list.append("has a quick notice period")

        reasoning = f"{title_text.capitalize()} with {exp_text} {company_text}; "
        if reasons_list:
            reasoning += "candidate " + ", ".join(reasons_list[:3]) + "."
        else:
            reasoning += "matches basic skills and criteria."

        res.append(
            {
                "candidate_id": candidate_id,
                "name": name,
                "score": round(final_score, 4),
                "reasoning": reasoning,
            }
        )

    return res
