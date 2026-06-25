import sys
import os
import argparse
import json
import gzip
import csv

# Add src to the Python search path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.score_candidates import score_candidate
from utils.rank_candidates import rank_candidates
from jd.senion_ai_engineer import senior_ai_enginerr_jd

def load_candidates(file_path):
    print(f"Loading candidates from {file_path}...")
    candidates = []
    
    # Support both gzipped and raw json/jsonl files
    is_gzip = file_path.endswith('.gz')
    open_func = gzip.open if is_gzip else open
    mode = 'rt' if is_gzip else 'r'
    
    with open_func(file_path, mode, encoding='utf-8') as f:
        content = f.read()
        
    stripped = content.strip()
    if stripped.startswith("["):
        try:
            candidates = json.loads(stripped)
        except Exception as e:
            print(f"Error parsing JSON array: {e}")
    else:
        for idx, line in enumerate(stripped.splitlines()):
            if not line.strip():
                continue
            try:
                candidates.append(json.loads(line))
            except Exception as e:
                print(f"Warning: Failed to parse line {idx}: {e}")
                continue
                
    print(f"Successfully loaded {len(candidates)} candidates.")
    return candidates

def main():
    parser = argparse.ArgumentParser(description="Rank candidates against a Job Description.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Path to write the output CSV")
    
    args = parser.parse_args()
    
    # 1. Load candidates
    candidates = load_candidates(args.candidates)
    
    # 2. Get JD profile
    jd = senior_ai_enginerr_jd()
    
    # 3. Score candidates
    print("Scoring candidates (scoring + honeypot filtering)...")
    scores = score_candidate(candidates, jd)
    
    # 4. Rank candidates
    print("Ranking candidates...")
    ranked = rank_candidates(scores)
    
    # 5. Extract top 100
    top_100 = ranked[:100]
    
    # Check if we have at least 100 rows
    if len(top_100) < 100:
        print(f"Warning: Only found {len(top_100)} candidates. Padded entries will be created.")
        
    print(f"Writing top 100 candidates to {args.out}...")
    
    # Ensure directory exists
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    with open(args.out, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for idx, item in enumerate(top_100):
            writer.writerow([
                item["candidate_id"],
                idx + 1,
                item["score"],
                item["reasoning"]
            ])
            
    print("Finished successfully.")

if __name__ == "__main__":
    main()
