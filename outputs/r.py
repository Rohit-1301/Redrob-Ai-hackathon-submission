import pandas as pd

# Read CSV files
df1 = pd.read_csv("rohit_candidates.csv")
df2 = pd.read_csv("ndk_submission.csv")
df3 = pd.read_csv("kamran_submission.csv")
df4 = pd.read_csv("adit_submission.csv")

# Convert candidate_id columns to sets
ids1 = set(df1["candidate_id"].astype(str))
ids2 = set(df2["candidate_id"].astype(str))
ids3 = set(df3["candidate_id"].astype(str))
ids4 = set(df4["candidate_id"].astype(str))

# Find common candidate IDs in all three files
common_ids = ids1 & ids2 & ids3 & ids4

print(f"Total Common Candidates: {len(common_ids)}")

# Create DataFrame
common_df = pd.DataFrame(sorted(common_ids), columns=["candidate_id"])

# Save to CSV
common_df.to_csv("common_candidates.csv", index=False)

print("Saved to common_candidates.csv")
