import os
import json
import time
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_cache")

def build_candidates_cache(
    jsonl_path="data/candidates.jsonl",
    val_parquet_path="outputs/validated_candidates.parquet",
    output_cache_path="data/candidates_cache.parquet"
):
    t0 = time.time()
    logger.info(f"Loading validated parquet from {val_parquet_path}...")
    if os.path.exists(val_parquet_path):
        val_df = pd.read_parquet(val_parquet_path)
        val_dict = val_df.set_index("candidate_id").to_dict(orient="index")
    else:
        val_dict = {}
        logger.warning("Validated parquet not found; proceeding without precomputed validation.")

    logger.info(f"Parsing 100k candidates from {jsonl_path}...")
    records = []
    
    # Consulting firms set for quick boolean flag
    consulting_set = {
        "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
        "cognizant", "capgemini", "mindtree", "wipro limited", "infosys limited", 
        "tata consultancy", "cognizant technology solutions", "accenture services"
    }

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id", f"CAND_{idx:07d}")
            prof = c.get("profile", {})
            sigs = c.get("redrob_signals", {})
            skills_raw = c.get("skills", [])
            career_raw = c.get("career_history", [])
            edu_raw = c.get("education", [])

            skills = [s.get("name", "").lower().strip() for s in skills_raw if isinstance(s, dict) and s.get("name")]
            career_titles = [str(j.get("title", "")).lower().strip() for j in career_raw if isinstance(j, dict) and j.get("title")]
            career_companies = [str(j.get("company", "")).lower().strip() for j in career_raw if isinstance(j, dict) and j.get("company")]
            edu_tiers = [str(e.get("tier", "unknown")).lower() for e in edu_raw if isinstance(e, dict) and e.get("tier")]

            cur_comp = str(prof.get("current_company", "")).lower().strip()
            cur_title = str(prof.get("current_title", "")).strip()

            has_consulting = any(c_co in cur_comp for c_co in consulting_set) or any(
                any(c_co in co for c_co in consulting_set) for co in career_companies
            )

            # Check research vs engineering
            all_research = False
            if career_titles:
                all_research = all(
                    any(term in t for term in ["researcher", "scientist", "fellow", "postdoc", "phd", "academic", "professor"])
                    and not any(term in t for term in ["engineer", "developer", "lead", "architect", "programmer"])
                    for t in career_titles
                )

            val_info = val_dict.get(cid, {})

            records.append({
                "candidate_id": cid,
                "name": prof.get("anonymized_name", "Unknown"),
                "current_title": cur_title,
                "current_company": prof.get("current_company", "Unknown"),
                "experience": float(prof.get("years_of_experience", 0.0) or 0.0),
                "location": prof.get("location", "Unknown"),
                "country": prof.get("country", "India"),
                "skills": skills,
                "headline": prof.get("headline", ""),
                "summary": prof.get("summary", ""),
                "career_titles": career_titles,
                "career_companies": career_companies,
                "edu_tiers": edu_tiers,
                "has_consulting": has_consulting,
                "is_pure_research": all_research,
                "recruiter_response_rate": float(sigs.get("recruiter_response_rate", 0.5) if sigs.get("recruiter_response_rate", 0.5) != -1 else 0.5),
                "interview_completion_rate": float(sigs.get("interview_completion_rate", 0.5) if sigs.get("interview_completion_rate", 0.5) != -1 else 0.5),
                "profile_completeness_score": float(sigs.get("profile_completeness_score", 50.0) or 50.0),
                "notice_period_days": int(sigs.get("notice_period_days", 90) or 90),
                "last_active_date": str(sigs.get("last_active_date", "")),
                "willing_to_relocate": bool(sigs.get("willing_to_relocate", False)),
                "verified_email": bool(sigs.get("verified_email", False)),
                "verified_phone": bool(sigs.get("verified_phone", False)),
                "github_activity_score": float(sigs.get("github_activity_score", -1) or -1),
                "connection_count": int(sigs.get("connection_count", 0) or 0),
                "validation_status": val_info.get("validation_status", "VALID"),
                "validation_score": float(val_info.get("validation_score", 100.0)),
                "behavioral_score": float(val_info.get("behavioral_score", 50.0)),
                "credibility_score": float(val_info.get("credibility_score", 50.0)),
                "availability_score": float(val_info.get("availability_score", 50.0)),
                "honeypot_score": float(val_info.get("honeypot_score", 0.0)),
                "invalidation_reason": val_info.get("invalidation_reason", ""),
                "flags": list(val_info.get("flags", [])) if isinstance(val_info.get("flags", []), (list, tuple)) else []
            })

            if (idx + 1) % 25000 == 0:
                logger.info(f"Processed {idx + 1} candidates...")

    logger.info("Converting to DataFrame...")
    df = pd.DataFrame(records)
    logger.info(f"DataFrame created: {df.shape}. Writing Parquet to {output_cache_path}...")
    df.to_parquet(output_cache_path, engine="pyarrow", index=False)
    logger.info(f"Candidate cache successfully saved in {time.time() - t0:.2f}s! File size: {os.path.getsize(output_cache_path)/(1024*1024):.2f} MB")

if __name__ == "__main__":
    build_candidates_cache()
