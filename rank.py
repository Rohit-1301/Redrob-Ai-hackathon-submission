import os
import sys
import argparse
import shutil
import tempfile
import logging
import importlib.util

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

def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description="End-to-End Candidate Ranking Pipeline")
    parser.add_argument("--candidates", type=str, default="./candidates.jsonl", help="Path to raw candidates JSON/JSONL dataset")
    parser.add_argument("--out", type=str, default="./submission.csv", help="Path to output ranked candidates CSV file")
    args = parser.parse_args()

    # Resolve paths
    candidates_path = os.path.abspath(args.candidates)
    output_csv_path = os.path.abspath(args.out)
    
    # Check that candidates file exists
    if not os.path.exists(candidates_path):
        logger.error(f"Candidates file not found at: {candidates_path}")
        sys.exit(1)

    jd_path = os.path.join(project_root, "Redrobsdataset", "job_description.docx")
    if not os.path.exists(jd_path):
        # Try SelectedCandidates/Redrobsdataset/job_description.docx
        jd_path = os.path.join(project_root, "SelectedCandidates", "Redrobsdataset", "job_description.docx")
        
    if not os.path.exists(jd_path):
        logger.error(f"Job description docx not found. Checked: {jd_path}")
        sys.exit(1)

    # Create a temporary directory for preprocessed splits
    temp_dir = tempfile.mkdtemp(prefix="redrobs_preprocess_", dir=project_root)
    logger.info(f"Created temporary directory for preprocessing splits: {temp_dir}")
    
    try:
        # Step 1: Preprocess candidate profiles
        logger.info("Step 1: Running Candidate Preprocessing and Validation Engine...")
        
        # Load preprocessing module dynamically to prevent namespace/collision issues
        prep_script_path = os.path.join(project_root, "Preprocessing pipeline", "preprocess.py")
        preprocess_module = import_from_path("preprocess_pipeline_runner", prep_script_path)
        
        # Run the validation and preprocessing pipeline
        preprocess_module.run_pipeline(candidates_path, temp_dir)
        
        # Construct expected paths
        valid_path = os.path.join(temp_dir, "valid.json")
        review_path = os.path.join(temp_dir, "review.json")
        weak_path = os.path.join(temp_dir, "weak.json")
        
        # Verify splits exist
        for p in [valid_path, review_path, weak_path]:
            if not os.path.exists(p):
                logger.error(f"Preprocessing did not generate expected split file: {p}")
                sys.exit(1)

        # Step 2: Rank candidates
        logger.info("Step 2: Running Semantic Vector Ranking Engine...")
        
        # Import ranker from SelectedCandidates package
        from SelectedCandidates.src.ranking.ranker import run_ranking_pipeline
        
        # Define output directory and cache directory for ranker
        ranker_output_dir = os.path.join(temp_dir, "ranker_output")
        cache_dir = os.path.join(project_root, "SelectedCandidates", "models")
        os.makedirs(ranker_output_dir, exist_ok=True)
        
        results = run_ranking_pipeline(
            docx_path=jd_path,
            valid_path=valid_path,
            review_path=review_path,
            weak_path=weak_path,
            output_dir=ranker_output_dir,
            cache_dir=cache_dir
        )
        
        generated_csv = results["csv_path"]
        
        # Copy output to the requested destination
        logger.info(f"Copying generated CSV from {generated_csv} to {output_csv_path}...")
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        shutil.copy2(generated_csv, output_csv_path)
        
        logger.info("Pipeline execution completed successfully!")
        
    finally:
        # Cleanup temporary files
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
