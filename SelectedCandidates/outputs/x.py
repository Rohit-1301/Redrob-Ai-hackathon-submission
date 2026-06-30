import pandas as pd

# Read CSV files
df1 = pd.read_csv("submission.csv")
df2 = pd.read_csv("top_100_candidates.csv")

# Convert candidate IDs to sets
ids1 = set(df1["candidate_id"])
ids2 = set(df2["candidate_id"])

# Find common candidate IDs
common_ids = ids1.intersection(ids2)

print(f"Candidates in File 1: {len(ids1)}")
print(f"Candidates in File 2: {len(ids2)}")
print(f"Common Candidates: {len(common_ids)}")

# Save common candidates if needed
common_df = pd.DataFrame({"candidate_id": sorted(common_ids)})
common_df.to_csv("common_candidates.csv", index=False)

print("Common candidate IDs saved to common_candidates.csv")