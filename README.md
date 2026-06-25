# Intelligent Candidate Discovery & Ranking Engine

This repository contains the candidate discovery and ranking system built for the Redrob Hackathon. It is designed to rank 100,000 candidate profiles against a target "Senior AI Engineer (Founding Team)" job description.

## Architecture & Methodology

The ranking engine scores each candidate using a weighted composite formula:

$$FinalScore = 0.35 \cdot CareerScore + 0.20 \cdot SemanticScore + 0.15 \cdot SkillScore + 0.15 \cdot BehaviorScore + 0.10 \cdot ExperienceScore + 0.05 \cdot StabilityScore - Penalty$$

*   **Career Score (35%):** Analyzes titles matching target profiles, filters service-giant consultants unless they have product startup history, and inspects description details.
*   **Semantic Score (20%):** Computes the cosine similarity of candidate headlines against the job description using local SentenceTransformer embeddings (`all-MiniLM-L6-v2`).
*   **Skill Score (15%):** Computes proficiency and endorsement-weighted matches for required and preferred skills.
*   **Behavior Score (15%):** Weighs platform activity (recency, recruiter response rate, open-to-work flag, notice period, and location preference).
*   **Experience Score (10%):** Matches the target 5-9 years experience range.
*   **Stability Score (5%):** Down-weights candidate profiles with high job-hopping rates (frequent title changes every < 18 months).
*   **Honeypot Filter (Hard Filter):** Instantly filters out synthetic honeypots with impossible durations or expert skills of 0 duration, forcing their score to `-999.0` to keep them out of the top 100.

---

## Setup & Reproduction

### Prerequisites
*   Python $\geq$ 3.13
*   Libraries: `numpy`, `sentence-transformers`, `torch`

### Installation
You can install dependencies using pip:
```bash
pip install -r requirements.txt
```
Or install the package in editable mode:
```bash
pip install -e .
```

### Reproducing Results
1.  **Candidate Preprocessing (Honeypot Splitting):**
    ```bash
    python preprocess.py
    ```
    This script separates the honeypot candidates from the valid ones, outputting `data/valid_candidates.jsonl` and `data/invalid_candidates.jsonl`.
2.  **Generate Ranks (Valid Candidates):**
    ```bash
    python rank.py --candidates data/valid_candidates.jsonl --out submission_valid.csv
    ```
3.  **Generate Ranks (Overall Candidates):**
    ```bash
    python rank.py --candidates data/cleaned_candidates.jsonl --out submission_overall.csv
    ```
    *(Note: This execution relies on `embeddings.npz` containing the precomputed headline embeddings, completing in less than 2 minutes on CPU.)*

If you need to regenerate the precomputed embeddings archive from scratch, run:
```bash
python precompute_embeddings.py
```
This script will encode all 100,000 headlines locally in under 3 minutes.
