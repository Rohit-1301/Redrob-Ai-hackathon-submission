import os
import json
import logging
import datetime
import pandas as pd
import numpy as np

# Import validators and scoring
from validators.schema_validator import validate_schema
from validators.career_validator import validate_career
from validators.skill_validator import validate_skills
from validators.signal_validator import validate_signals
from validators.honeypot_detector import detect_honeypots
from validators.jd_validator import validate_jd_eligibility
from scoring.validation_score import compute_validation_score

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def run_pipeline(input_path: str, output_parquet_path: str, report_json_path: str):
    logger.info(f"Starting candidate preprocessing and validation pipeline on: {input_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_json_path), exist_ok=True)

    records = []
    
    # Stats trackers
    total_count = 0
    status_counts = {"VALID": 0, "REVIEW": 0, "WEAK": 0, "INVALID": 0}
    failure_reason_counts = {}
    
    # Signal stats aggregations
    sum_completeness = 0.0
    sum_resp_rate = 0.0
    sum_int_comp = 0.0
    sum_offer_acc = 0.0
    offer_acc_count = 0
    github_linked_count = 0
    sum_connections = 0
    
    # Recency stats
    recency_buckets = {"<= 7 days": 0, "<= 30 days": 0, "<= 90 days": 0, "> 90 days": 0}
    # Notice period stats
    notice_buckets = {"0-30 days": 0, "31-60 days": 0, "61-90 days": 0, "> 90 days": 0}

    def get_candidates(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info("Input recognized as JSON array.")
                    for item in data:
                        yield item
                    return
        except Exception:
            pass

        logger.info("Input recognized as JSONL (line-by-line).")
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    valid_profiles = []
    invalid_profiles = []
    
    for candidate in get_candidates(input_path):
        total_count += 1
        if total_count % 10000 == 0:
            logger.info(f"Processed {total_count} candidates...")

        candidate_id = candidate.get("candidate_id", f"UNKNOWN_{total_count}")
        
        # Step 1 & 2: Schema Validation
        schema_errs = validate_schema(candidate)
        
        # If critical schema errors exist, evaluate with defaults
        if any(e["severity"] == "HIGH" for e in schema_errs):
            career_errs, skill_errs, signal_errs, honeypot_errs = [], [], [], []
            honeypot_score = 100.0
            behavioral_score, availability_score = 0.0, 0.0
            jd_flags, jd_disqualifiers, credibility_score = [], ["CRITICAL_SCHEMA_FAILURE"], 0.0
        else:
            # Step 3 & 4: Career Consistency Validation
            career_errs = validate_career(candidate)
            
            # Step 5: Skill Credibility Validation
            skill_errs = validate_skills(candidate)
            
            # Step 6: Behavioral Signal Processing
            signal_errs, behavioral_score, availability_score = validate_signals(candidate)
            
            # Step 7: JD Eligibility Validation
            jd_flags, jd_disqualifiers, credibility_score = validate_jd_eligibility(candidate)
            
            # Step 8: Honeypot Detection
            honeypot_errs, honeypot_score = detect_honeypots(candidate)

        # Step 9 & 10: Scoring and Classification
        validation_score, validation_status, penalties = compute_validation_score(
            schema_errors=schema_errs,
            career_errors=career_errs,
            skill_errors=skill_errs,
            signal_errors=signal_errs,
            honeypot_errors=honeypot_errs,
            honeypot_score=honeypot_score,
            behavioral_score=behavioral_score,
            disqualifiers=jd_disqualifiers
        )

        # Update stats
        status_counts[validation_status] += 1
        
        # Log all errors/penalties to invalid_reasons
        invalid_reasons = []
        for e in schema_errs + career_errs + skill_errs + signal_errs + honeypot_errs:
            code = e["code"]
            invalid_reasons.append(e["message"])
            failure_reason_counts[code] = failure_reason_counts.get(code, 0) + 1

        for p in penalties:
            # Add human readable details of penalties
            if p not in invalid_reasons:
                invalid_reasons.append(p)
                
        # Extract combined flags
        combined_flags = list(set(jd_flags + [e["code"] for e in schema_errs + career_errs + skill_errs + signal_errs + honeypot_errs if e["severity"] == "HIGH"]))

        # Join reasons to form a single explainable text column
        invalidation_reason = "; ".join(invalid_reasons) if validation_status == "INVALID" else ""

        # Save stats for signals
        signals = candidate.get("redrob_signals", {})
        if isinstance(signals, dict):
            sum_completeness += float(signals.get("profile_completeness_score", 0.0))
            sum_resp_rate += float(signals.get("recruiter_response_rate", 0.0))
            sum_int_comp += float(signals.get("interview_completion_rate", 0.0))
            
            offer_acc = signals.get("offer_acceptance_rate", -1)
            if offer_acc != -1:
                sum_offer_acc += float(offer_acc)
                offer_acc_count += 1
                
            gh_act = signals.get("github_activity_score", -1)
            if gh_act != -1:
                github_linked_count += 1
                
            sum_connections += int(signals.get("connection_count", 0))
            
            # Active date distribution
            last_active_str = signals.get("last_active_date")
            last_active_date = parse_date(last_active_str)
            if last_active_date:
                days_active = (datetime.date(2026, 6, 20) - last_active_date).days
                if days_active <= 7:
                    recency_buckets["<= 7 days"] += 1
                elif days_active <= 30:
                    recency_buckets["<= 30 days"] += 1
                elif days_active <= 90:
                    recency_buckets["<= 90 days"] += 1
                else:
                    recency_buckets["> 90 days"] += 1
                    
            # Notice period distribution
            notice_days = signals.get("notice_period_days", 90)
            if notice_days <= 30:
                notice_buckets["0-30 days"] += 1
            elif notice_days <= 60:
                notice_buckets["31-60 days"] += 1
            elif notice_days <= 90:
                notice_buckets["61-90 days"] += 1
            else:
                notice_buckets["> 90 days"] += 1

        records.append({
            "candidate_id": candidate_id,
            "validation_status": validation_status,
            "validation_score": float(validation_score),
            "behavioral_score": float(behavioral_score),
            "credibility_score": float(credibility_score),
            "availability_score": float(availability_score),
            "honeypot_score": float(honeypot_score),
            "invalidation_reason": invalidation_reason,
            "invalid_reasons": invalid_reasons,
            "flags": combined_flags
        })

        # Append detailed profiles to splits
        candidate_extra = candidate.copy()
        candidate_extra["validation_status"] = validation_status
        candidate_extra["validation_score"] = float(validation_score)
        candidate_extra["behavioral_score"] = float(behavioral_score)
        candidate_extra["credibility_score"] = float(credibility_score)
        candidate_extra["availability_score"] = float(availability_score)
        candidate_extra["honeypot_score"] = float(honeypot_score)
        candidate_extra["invalidation_reason"] = invalidation_reason
        candidate_extra["invalid_reasons"] = invalid_reasons
        candidate_extra["flags"] = combined_flags
        
        if validation_status == "VALID":
            valid_profiles.append(candidate_extra)
        elif validation_status == "INVALID":
            invalid_profiles.append(candidate_extra)

    # Save to Parquet
    logger.info("Converting to Pandas DataFrame...")
    df = pd.DataFrame(records)
    
    logger.info(f"Writing to Parquet file: {output_parquet_path}")
    # Save parquet with support for lists of strings
    df.to_parquet(output_parquet_path, engine='pyarrow', index=False)

    # Write separate JSON files
    valid_json_path = os.path.join(os.path.dirname(output_parquet_path), "valid_candidates.json")
    invalid_json_path = os.path.join(os.path.dirname(output_parquet_path), "invalid_candidates.json")
    
    logger.info(f"Writing valid candidates to standard JSON: {valid_json_path}")
    with open(valid_json_path, 'w', encoding='utf-8') as f_v:
        json.dump(valid_profiles, f_v, indent=2, ensure_ascii=False)
        
    logger.info(f"Writing invalid candidates to standard JSON: {invalid_json_path}")
    with open(invalid_json_path, 'w', encoding='utf-8') as f_inv:
        json.dump(invalid_profiles, f_inv, indent=2, ensure_ascii=False)
    
    # Compute signal metrics averages
    avg_completeness = sum_completeness / total_count if total_count > 0 else 0.0
    avg_resp_rate = sum_resp_rate / total_count if total_count > 0 else 0.0
    avg_int_comp = sum_int_comp / total_count if total_count > 0 else 0.0
    avg_offer_acc = sum_offer_acc / offer_acc_count if offer_acc_count > 0 else 0.0
    github_link_rate = github_linked_count / total_count if total_count > 0 else 0.0
    avg_connections = sum_connections / total_count if total_count > 0 else 0.0

    # Save validation report summary
    report = {
        "total_candidates": total_count,
        "status_distribution": status_counts,
        "signal_distributions": {
            "average_profile_completeness_score": round(avg_completeness, 2),
            "average_recruiter_response_rate": round(avg_resp_rate, 3),
            "average_interview_completion_rate": round(avg_int_comp, 3),
            "average_offer_acceptance_rate": round(avg_offer_acc, 3),
            "github_connection_rate": round(github_link_rate, 3),
            "average_connection_count": round(avg_connections, 1),
            "last_active_recency_distribution": recency_buckets,
            "notice_period_distribution": notice_buckets
        },
        "common_failure_reasons": dict(sorted(failure_reason_counts.items(), key=lambda item: item[1], reverse=True)[:15])
    }

    logger.info(f"Writing validation summary report: {report_json_path}")
    with open(report_json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info("Pipeline executed successfully!")

if __name__ == "__main__":
    import sys
    
    # Define local workspace paths
    input_file = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\Redrobsdataset\candidates.jsonl"
    output_parquet = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\outputs\validated_candidates.parquet"
    report_json = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\outputs\validation_report.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_parquet = sys.argv[2]
    if len(sys.argv) > 3:
        report_json = sys.argv[3]
        
    # Fallback to sample if default input file doesn't exist and not overridden
    if len(sys.argv) <= 1 and not os.path.exists(input_file):
        logger.warning(f"Full dataset not found at {input_file}, checking sample...")
        input_file = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\Redrobsdataset\sample_candidates.json"
        
    run_pipeline(input_file, output_parquet, report_json)
