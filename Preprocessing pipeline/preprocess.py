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

def run_pipeline(input_path: str, output_dir: str):
    logger.info(f"Starting candidate preprocessing and validation pipeline on: {input_path}")
    logger.info(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Use container-local temp dir to bypass slow host mount (e.g., OneDrive)
    use_temp = False
    temp_dir = output_dir
    if output_dir == "/app/output" or output_dir.startswith("/app/output/"):
        use_temp = True
        temp_dir = "/app/temp_output"
        logger.info(f"Using container-local temp directory for fast I/O: {temp_dir}")
        os.makedirs(temp_dir, exist_ok=True)

    valid_json_path = os.path.join(temp_dir, "valid.json")
    review_json_path = os.path.join(temp_dir, "review.json")
    weak_json_path = os.path.join(temp_dir, "weak.json")
    invalid_json_path = os.path.join(temp_dir, "invalid.json")
    output_parquet_path = os.path.join(temp_dir, "validated_candidates.parquet")
    report_json_path = os.path.join(temp_dir, "validation_report.json")

    # Open output JSON files for streaming to prevent OOM
    f_valid = open(valid_json_path, 'w', encoding='utf-8')
    f_review = open(review_json_path, 'w', encoding='utf-8')
    f_weak = open(weak_json_path, 'w', encoding='utf-8')
    f_invalid = open(invalid_json_path, 'w', encoding='utf-8')

    f_valid.write("[\n")
    f_review.write("[\n")
    f_weak.write("[\n")
    f_invalid.write("[\n")

    first_valid = True
    first_review = True
    first_weak = True
    first_invalid = True

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
    
    # Recency & notice period buckets
    recency_buckets = {"<= 7 days": 0, "<= 30 days": 0, "<= 90 days": 0, "> 90 days": 0}
    notice_buckets = {"0-30 days": 0, "31-60 days": 0, "61-90 days": 0, "> 90 days": 0}

    ref_date = datetime.date(2026, 6, 20)
    records = []

    def get_candidates(path):
        is_array = False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        if stripped.startswith('['):
                            is_array = True
                        break
        except Exception:
            pass

        if is_array:
            logger.info("Input recognized as JSON array.")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    yield item
        else:
            logger.info("Input recognized as JSONL (line-by-line).")
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)

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
            if p not in invalid_reasons:
                invalid_reasons.append(p)
                
        combined_flags = list(set(jd_flags + [e["code"] for e in schema_errs + career_errs + skill_errs + signal_errs + honeypot_errs if e["severity"] == "HIGH"]))
        invalidation_reason = "; ".join(invalid_reasons) if validation_status == "INVALID" else ""

        # Build Parquet metadata record
        record = {
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
        }
        records.append(record)
        
        # Build candidate extra dictionary (original data + validation metadata fields)
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

        # Stream write to matching JSON output file
        if validation_status == "VALID":
            if not first_valid:
                f_valid.write(",\n")
            else:
                first_valid = False
            json.dump(candidate_extra, f_valid, indent=2, ensure_ascii=False)
        elif validation_status == "REVIEW":
            if not first_review:
                f_review.write(",\n")
            else:
                first_review = False
            json.dump(candidate_extra, f_review, indent=2, ensure_ascii=False)
        elif validation_status == "WEAK":
            if not first_weak:
                f_weak.write(",\n")
            else:
                first_weak = False
            json.dump(candidate_extra, f_weak, indent=2, ensure_ascii=False)
        elif validation_status == "INVALID":
            if not first_invalid:
                f_invalid.write(",\n")
            else:
                first_invalid = False
            json.dump(candidate_extra, f_invalid, indent=2, ensure_ascii=False)

        # Track signal distributions
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
                days_active = (ref_date - last_active_date).days
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

    # Close JSON files
    f_valid.write("\n]")
    f_review.write("\n]")
    f_weak.write("\n]")
    f_invalid.write("\n]")

    f_valid.close()
    f_review.close()
    f_weak.close()
    f_invalid.close()

    # Save to Parquet
    logger.info("Converting metadata to Pandas DataFrame...")
    df = pd.DataFrame(records)
    logger.info(f"Writing to Parquet file: {output_parquet_path}")
    df.to_parquet(output_parquet_path, engine='pyarrow', index=False)

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

    if use_temp:
        import shutil
        logger.info(f"Copying final outputs from temp directory {temp_dir} to mount {output_dir}...")
        for filename in os.listdir(temp_dir):
            src = os.path.join(temp_dir, filename)
            dst = os.path.join(output_dir, filename)
            logger.info(f"Copying {filename}...")
            shutil.copy2(src, dst)
        logger.info("All outputs copied successfully to mount!")

    logger.info("Pipeline executed successfully!")

if __name__ == "__main__":
    import sys
    
    # Defaults
    input_file = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\Redrobsdataset\candidates.jsonl"
    output_dir = r"c:\Users\rg975\OneDrive - Vidyalankar Institute of Technology\23101A0019 Rohit Gupta INFT-A\redrobs\Preprocessing pipeline\output"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
        
    run_pipeline(input_file, output_dir)
