import os
import sys
import logging

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Configure logging to console and file
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, "pipeline.log"), encoding='utf-8')
    ]
)
logger = logging.getLogger("run_pipeline")

from src.ranking.ranker import run_ranking_pipeline
from src.reporting.generator import generate_reports_and_charts
from Redrobsdataset.validate_submission import validate_submission

def main():
    logger.info("Starting candidate ranking pipeline...")
    
    # Resolve absolute paths to work correctly regardless of CWD
    jd_path = os.path.abspath(os.path.join(project_root, os.getenv("JD_PATH", "Redrobsdataset/job_description.docx")))
    valid_path = os.path.abspath(os.path.join(project_root, os.getenv("VALID_PATH", "Preprocessing pipeline/output/valid.json")))
    review_path = os.path.abspath(os.path.join(project_root, os.getenv("REVIEW_PATH", "Preprocessing pipeline/output/review.json")))
    weak_path = os.path.abspath(os.path.join(project_root, os.getenv("WEAK_PATH", "Preprocessing pipeline/output/weak.json")))
    
    output_dir = os.path.abspath(os.path.join(current_dir, "outputs"))
    cache_dir = os.path.abspath(os.path.join(current_dir, "models"))
    reports_dir = os.path.abspath(os.path.join(current_dir, "reports"))
    
    logger.info(f"Using Job Description: {jd_path}")
    logger.info(f"Using VALID Candidates: {valid_path}")
    logger.info(f"Using REVIEW Candidates: {review_path}")
    logger.info(f"Using WEAK Candidates: {weak_path}")
    
    # Check that input files exist
    for p in [jd_path, valid_path, review_path, weak_path]:
        if not os.path.exists(p):
            logger.error(f"Required input file does not exist: {p}")
            sys.exit(1)
            
    # Run scoring and ranking
    try:
        results = run_ranking_pipeline(
            docx_path=jd_path,
            valid_path=valid_path,
            review_path=review_path,
            weak_path=weak_path,
            output_dir=output_dir,
            cache_dir=cache_dir
        )
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        sys.exit(1)
        
    # Generate charts and markdown report
    try:
        logger.info("Generating charts and final markdown report...")
        generate_reports_and_charts(results, reports_dir)
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        sys.exit(1)
        
    # Validate the generated CSV
    logger.info("Running compliance validation check on top_100_candidates.csv...")
    csv_path = results["csv_path"]
    errors = validate_submission(csv_path)
    
    if errors:
        logger.error(f"CSV compliance validation FAILED with {len(errors)} issues:")
        for err in errors:
            logger.error(f"- {err}")
        sys.exit(1)
    else:
        logger.info("CSV compliance validation SUCCESS. Output file is fully compliant with challenge rules!")
        
    logger.info("All pipeline processes completed successfully. Output files saved in outputs/ and reports/.")

if __name__ == "__main__":
    main()
