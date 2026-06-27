import os
import sys
import shutil
import subprocess

def run_cmd(cmd):
    print(f"\nRunning command: {' '.join(cmd)}")
    res = subprocess.run(cmd, check=True)
    return res

def main():
    print("=" * 70)
    print("   STARTING REDROB PIPELINE: PREPROCESSING, SELECTION & WEB APP  ")
    print("=" * 70)
    
    # 1. Determine input candidates file (prioritize mounted volume /app/data)
    candidates_file = "/app/data/candidates.jsonl"
    if not os.path.exists(candidates_file):
        print(f"No mounted dataset found at {candidates_file}, checking internal cache...")
        candidates_file = "/app/Redrobsdataset/candidates.jsonl"
        
    if not os.path.exists(candidates_file):
        print(f"No internal dataset found at {candidates_file}, checking sample candidates...")
        fallback = "/app/Redrobsdataset/sample_candidates.json"
        if os.path.exists(fallback):
            print(f"Using sample_candidates.json for demonstration/testing.")
            candidates_file = fallback
        else:
            print("ERROR: No candidates dataset found in the container!")
            sys.exit(1)
            
    print(f"Using candidates data file: {candidates_file}")
            
    # 2. Run Preprocessing Pipeline
    # Inside the container, output goes to "Preprocessing pipeline/output"
    print("\n--- [1/4] Running Candidate Preprocessing & Classification ---")
    run_cmd([
        sys.executable, 
        "Preprocessing pipeline/preprocess.py", 
        candidates_file, 
        "Preprocessing pipeline/output"
    ])
    
    # 3. Run Ranking Pipeline
    # This reads from "Preprocessing pipeline/output" and writes to "SelectedCandidates/outputs"
    print("\n--- [2/4] Running Candidate Scoring & Ranking (Top 100 Selection) ---")
    run_cmd([
        sys.executable,
        "SelectedCandidates/run_pipeline.py"
    ])
    
    # 4. Generate Stats for All Candidates
    # Reads candidates.jsonl and validated_candidates.parquet, writes all_candidates_stats.json
    print("\n--- [3/4] Generating General Talent Pool Analytics (Skills, Location, YoE) ---")
    run_cmd([
        sys.executable,
        "SelectedCandidates/generate_all_stats.py"
    ])
    
    # 5. Persist outputs to mounted /app/outputs if it exists
    mount_outputs_dir = "/app/outputs"
    if os.path.exists(mount_outputs_dir):
        print(f"\n--- Saving final results to mounted host outputs directory: {mount_outputs_dir} ---")
        
        # Files to copy from SelectedCandidates/outputs
        local_outputs = os.path.abspath("SelectedCandidates/outputs")
        if os.path.exists(local_outputs):
            for file_name in os.listdir(local_outputs):
                src = os.path.join(local_outputs, file_name)
                dst = os.path.join(mount_outputs_dir, file_name)
                if os.path.isfile(src):
                    print(f"Copying {file_name} to outputs...")
                    shutil.copy2(src, dst)
                    
        # Files to copy from SelectedCandidates/reports (e.g. final_report.md, png images)
        local_reports = os.path.abspath("SelectedCandidates/reports")
        if os.path.exists(local_reports):
            for file_name in os.listdir(local_reports):
                src = os.path.join(local_reports, file_name)
                dst = os.path.join(mount_outputs_dir, file_name)
                if os.path.isfile(src):
                    print(f"Copying report {file_name} to outputs...")
                    shutil.copy2(src, dst)
                    
        # Also copy preprocessed report from Preprocessing pipeline/output
        preprocess_report = os.path.abspath("Preprocessing pipeline/output/validation_report.json")
        if os.path.exists(preprocess_report):
            print("Copying preprocessing validation_report.json to outputs...")
            shutil.copy2(preprocess_report, os.path.join(mount_outputs_dir, "validation_report.json"))
            
        print("Outputs persisted successfully on host!")
    
    # 6. Start Streamlit App
    print("\n--- [4/4] Starting Interactive Sandbox Streamlit Application ---")
    print("Application will be available on http://localhost:8501")
    
    streamlit_path = "streamlit"
    cmd = [
        streamlit_path, 
        "run", 
        "SelectedCandidates/app/streamlit_app.py", 
        "--server.port=8501", 
        "--server.address=0.0.0.0"
    ]
    
    try:
        os.execvp(cmd[0], cmd)
    except Exception as e:
        # Fallback if execvp fails
        subprocess.run(cmd)

if __name__ == "__main__":
    main()
