import os
import json
import pandas as pd
from collections import Counter

def main():
    print("Generating comprehensive statistics of the 100K candidate pool...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../"))
    
    candidates_path = os.path.join(project_root, "Redrobsdataset/candidates.jsonl")
    parquet_path = os.path.join(project_root, "Preprocessing pipeline/output/validated_candidates.parquet")
    output_stats_path = os.path.join(project_root, "SelectedCandidates/outputs/all_candidates_stats.json")
    
    print(f"Candidates path: {candidates_path}")
    print(f"Parquet path: {parquet_path}")
    print(f"Output stats path: {output_stats_path}")
    
    # 1. Classification Status Breakdown (from Parquet)
    status_counts = {"VALID": 0, "REVIEW": 0, "WEAK": 0, "INVALID": 0}
    if os.path.exists(parquet_path):
        try:
            df_p = pd.read_parquet(parquet_path)
            status_dist = df_p["validation_status"].value_counts().to_dict()
            for k, v in status_dist.items():
                status_counts[k] = int(v)
            print("Successfully loaded status distribution from parquet.")
        except Exception as e:
            print(f"Error reading parquet: {e}")
    else:
        print("Parquet file not found. Preprocessing might not have run yet.")
        
    skills_counter = Counter()
    locations_counter = Counter()
    experience_counter = Counter()
    companies_counter = Counter()
    total_candidates = 0

    if os.path.exists(candidates_path):
        with open(candidates_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    c = json.loads(line)
                    total_candidates += 1
                    
                    # Skills
                    for s in c.get("skills", []):
                        sname = s.get("name")
                        if sname:
                            skills_counter[sname] += 1
                            
                    # Location
                    profile = c.get("profile", {})
                    loc = profile.get("location")
                    if loc:
                        locations_counter[loc] += 1
                        
                    # Experience
                    yoe = profile.get("years_of_experience")
                    if yoe is not None:
                        # Bin to integer
                        experience_counter[int(round(yoe))] += 1
                        
                    # Companies
                    for job in c.get("career_history", []):
                        comp = job.get("company")
                        if comp:
                            companies_counter[comp] += 1
                except Exception as e:
                    pass
                if total_candidates % 25000 == 0:
                    print(f"Processed {total_candidates} candidates for stats...")
    else:
        print(f"Candidates file not found at {candidates_path}")
        return

    # Get top 20
    top_skills = [{"skill": k, "count": v} for k, v in skills_counter.most_common(20)]
    top_locations = [{"location": k, "count": v} for k, v in locations_counter.most_common(20)]
    top_companies = [{"company": k, "count": v} for k, v in companies_counter.most_common(20)]
    
    # Sort experience by key
    exp_dist = [{"experience_years": k, "count": v} for k, v in sorted(experience_counter.items())]

    stats = {
        "total_candidates": total_candidates,
        "status_distribution": status_counts,
        "top_skills": top_skills,
        "top_locations": top_locations,
        "top_companies": top_companies,
        "experience_distribution": exp_dist
    }

    os.makedirs(os.path.dirname(output_stats_path), exist_ok=True)
    with open(output_stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        
    print(f"Stats written successfully to {output_stats_path}")

if __name__ == "__main__":
    main()
