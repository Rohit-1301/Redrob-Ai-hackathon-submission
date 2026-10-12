import os
import sys
import argparse
import json
import logging
import pandas as pd

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("rank_entry")

from SelectedCandidates.src.utils.dynamic_jd_parser import parse_jd
from SelectedCandidates.src.ranking.dynamic_ranker import run_dynamic_ranking, get_embedding_model

def load_candidates_dataset(candidates_arg_path: str):
    """
    Loads candidates dataframe, automatically utilizing candidates_cache.parquet if available.
    """
    cache_path = os.path.join(project_root, "data/candidates_cache.parquet")
    
    # If the user specifically supplied an existing parquet file
    if candidates_arg_path.endswith(".parquet") and os.path.exists(candidates_arg_path):
        logger.info(f"Loading candidates from user supplied Parquet: {candidates_arg_path}")
        return pd.read_parquet(candidates_arg_path)

    # If the cache parquet exists in data/candidates_cache.parquet
    if os.path.exists(cache_path):
        logger.info(f"Loading candidates from fast parquet cache: {cache_path}")
        return pd.read_parquet(cache_path)

    # Otherwise build the cache from candidates_arg_path or data/candidates.jsonl
    raw_path = candidates_arg_path
    if not os.path.exists(raw_path):
        raw_path = os.path.join(project_root, "data/candidates.jsonl")
    if not os.path.exists(raw_path):
        raw_path = os.path.join(project_root, "Redrobsdataset/candidates.jsonl")

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Candidates file not found at {candidates_arg_path} or default locations.")

    logger.info(f"Building fast candidate cache from {raw_path}...")
    from build_cache import build_candidates_cache
    build_candidates_cache(
        jsonl_path=raw_path,
        val_parquet_path=os.path.join(project_root, "outputs/validated_candidates.parquet"),
        output_cache_path=cache_path
    )
    return pd.read_parquet(cache_path)

def main():
    parser = argparse.ArgumentParser(description="End-to-End Dynamic Candidate Ranking Pipeline")
    parser.add_argument("--jd", type=str, default="Redrobsdataset/job_description.docx", help="Path to Job Description (PDF, DOCX, or TXT)")
    parser.add_argument("--candidates", type=str, default="data/candidates.jsonl", help="Path to raw candidates JSON/JSONL dataset or parquet cache")
    parser.add_argument("--top", type=int, default=100, choices=[10, 50, 100], help="Number of top candidates to output (10, 50, or 100)")
    parser.add_argument("--out", type=str, default="./submission.csv", help="Path to output ranked candidates CSV file")
    args = parser.parse_args()

    # 1. Resolve JD Path
    jd_path = os.path.abspath(args.jd)
    if not os.path.exists(jd_path):
        fallback_jd = os.path.join(project_root, "Redrobsdataset/job_description.docx")
        if os.path.exists(fallback_jd):
            jd_path = fallback_jd
        else:
            logger.error(f"Job Description file not found at: {jd_path}")
            sys.exit(1)

    logger.info(f"Ingesting Job Description from: {jd_path}")
    parsed_jd = parse_jd(jd_path)
    logger.info(f"Parsed Job Title: {parsed_jd.get('title')}")
    logger.info(f"Target Experience: {parsed_jd.get('experience_preferred')}")
    logger.info(f"Required Skills ({len(parsed_jd.get('required_competencies', []))}): {', '.join(parsed_jd.get('required_competencies', [])[:8])}...")

    # 2. Ingest Candidates
    df_cands = load_candidates_dataset(args.candidates)
    logger.info(f"Loaded {len(df_cands)} candidate profiles.")

    # 3. Dynamic Ranking with Honeypot Detector & Vector Semantic Model
    logger.info(f"Executing dynamic candidate ranking for Top {args.top} candidates...")
    results = run_dynamic_ranking(
        jd_info=parsed_jd,
        candidates_df=df_cands,
        top_limit=args.top
    )

    df_top = results["df"].head(args.top)
    explanations = results["explanations"][:args.top]

    # 4. Save Output CSV
    out_csv = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_top[["candidate_id", "rank", "score", "reasoning"]].to_csv(out_csv, index=False)
    logger.info(f"Top {args.top} candidates saved to CSV: {out_csv}")

    # 5. Save Output Explanations JSON alongside CSV
    out_json = os.path.splitext(out_csv)[0] + "_explanations.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(explanations, f, indent=2)
    logger.info(f"Detailed candidate explanations saved to JSON: {out_json}")

    # 6. Validate CSV compliance if top 100
    if args.top == 100:
        val_script = os.path.join(project_root, "Redrobsdataset/validate_submission.py")
        if os.path.exists(val_script):
            from Redrobsdataset.validate_submission import validate_submission
            errors = validate_submission(out_csv)
            if errors:
                logger.warning(f"Compliance validation had notices: {errors}")
            else:
                logger.info("Compliance validation SUCCESS: Submission file is 100% compliant!")

    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
