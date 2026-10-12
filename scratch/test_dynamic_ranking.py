import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from SelectedCandidates.src.utils.dynamic_jd_parser import parse_jd
from SelectedCandidates.src.ranking.dynamic_ranker import run_dynamic_ranking

t0 = time.time()
print("1. Parsing test PDF JD...")
jd = parse_jd("scratch/sample_jd.pdf")
print(f"Parsed JD in {time.time()-t0:.2f}s: {jd['title']}")
print("Required skills:", jd["required_competencies"])

t1 = time.time()
print("2. Loading 100,000 candidates cache...")
df_cands = pd.read_parquet("data/candidates_cache.parquet")
print(f"Loaded 100k cache in {time.time()-t1:.2f}s")

t2 = time.time()
print("3. Running dynamic ranking on 100,000 candidates...")
res = run_dynamic_ranking(jd, df_cands, top_limit=100)
print(f"Dynamic ranking completed in {time.time()-t2:.2f}s!")

df = res["df"]
print("\nTop 5 Ranked Candidates:")
print(df[["rank", "candidate_id", "name", "title", "score", "reasoning"]].head(5).to_string())
