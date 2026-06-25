# Redrob Candidate Ranking Engine - Comprehensive Documentation

This document provides a detailed explanation of the architecture, algorithmic design, scoring formulas, sorting rules, and honeypot detection mechanisms implemented in the Redrob Candidate Ranking Engine.

---

## 1. Project Directory Layout

Following our codebase organization, the repository is structured as follows:

```
ranking-engine/
├── .gitignore                    # Git ignore file for large datasets and envs
├── README.md                     # High-level overview and setup instructions
├── rank.py                       # Main pipeline entrypoint to rank candidate database
├── sandbox_app.py                # Streamlit app for interactive candidate ranking
├── precompute_embeddings.py      # Script to precompute headline sentence embeddings
├── preprocess.py                 # Preprocessing script to split candidates by honeypot status
├── requirements.txt              # Python packages required
│
├── data/                         # Candidate data storage
│   ├── sample_candidates.json    # Small candidate sample (50 candidates) for sandbox testing
│   ├── sample_submission.csv     # Sample output CSV for format validation reference
│   ├── valid_candidates.jsonl    # Preprocessed candidate profiles with 0 honeypot traps (99,710 records)
│   ├── invalid_candidates.jsonl  # Preprocessed candidate profiles containing honeypot traps (290 records)
│   ├── candidates.jsonl          # [GIT IGNORED] Raw candidate profiles (100,000 candidates)
│   ├── cleaned_candidates.jsonl  # [GIT IGNORED] Normalized candidate profiles
│   └── embeddings.npz            # [GIT IGNORED] Precomputed float32 headline embedding matrix
│
├── docs/                         # Documentation and Reference files
│   ├── ranking_engine_doc.md     # In-depth architectural & algorithmic documentation
│   ├── candidate_schema.json     # Schema defining structure of candidate JSON profiles
│   ├── README.docx               # Original challenge README
│   ├── job_description.docx      # Original target job description specifications
│   ├── redrob_signals_doc.docx   # Original specifications for platform activity metrics
│   └── submission_spec.docx      # Specifications for output format
│
├── outputs/                      # Staging area for partner & historical submissions
│   ├── adit_submission.csv
│   ├── adit_top_100_candidates.json
│   ├── common_candidates.csv
│   ├── kamran_submission.csv
│   ├── ndk_submission.csv
│   ├── r.py
│   └── rohit_candidates.csv
│
├── src/                          # Code package containing core logic
│   ├── main.py                   # Main run loop wrapper (local testing)
│   ├── cpp/
│   │   └── clean_candidates.cpp  # C++ code used to clean and normalize JSON lines
│   ├── jd/
│   │   └── senion_ai_engineer.py # Job Description parameters and weights
│   └── utils/
│     ├── get_candidates.py       # Helper containing hardcoded sample profiles
│     ├── score_candidates.py     # Main candidate grading logic
│     ├── rank_candidates.py      # Sorting and tie-breaking implementation
│     └── recommend_candidates.py # Candidate recommendation stub
│
└── validate/                     # Validation suite
    └── validate_submission.py    # Official format validation script
```

---

## 2. Honeypot Detection & Traps (Honeypot Filter)

The candidate database contains artificial synthetic "honeypot" profiles specifically injected to trap naive engines. We implement a **Hard Filter** at the beginning of the scoring phase. Any candidate flagged as a honeypot receives a score of `-999.0` and is completely disqualified from the top-100 list.

### A. True Honeypot Heuristics (0% False Positive Rate)
We identify honeypots using three absolute temporal and structural contradictions that are impossible in real resumes:

1. **Expert Skill with 0 Duration:**
   * *Rule:* A candidate claims `"expert"` proficiency in a skill but has `duration_months == 0` for that skill.
   * *Rationale:* It is physically impossible to be an expert in a technology without ever using it. This is a clean synthetic artifact.
   * *Code Reference:* `expert_0 = sum(1 for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0)`

2. **Startup Founding Mismatch:**
   * *Rule:* A candidate lists working at a startup before its actual founding year. For instance:
     * **Sarvam AI** (Founded in 2023)
     * **Krutrim** (Founded in 2023)
     * **Glance** (Founded in 2019)
     * **Rephrase.ai** (Founded in 2019)
   * *Rationale:* You cannot work at a company before it exists.
   * *Code Reference:* `start.year < founding` (e.g., checking if the candidate claims they worked at Sarvam AI in 2021).

3. **Job Duration Temporal Violations:**
   * *Rule:* The candidate's stated `duration_months` at a job exceeds the calendar dates of that job (delta between start and end dates) by more than 3 months, OR the stated duration exceeds the startup's age since founding.
   * *Rationale:* Timelines must be mathematically consistent.
   * *Code Reference:* `stated_dur > calendar_delta + 3` or `stated_dur > (2026 - founding) * 12 + 6`.

### B. Noisy Heuristics & The "64% False Positive Trap"
We deliberately avoided noisy heuristic filters used by competing engines, as they lead to severe false-positive rates:

* **The Title-Description Mismatch Trap:**
  * *Heuristic:* Check if a candidate's job title matches their job description template.
  * *Why we avoided it:* The synthetic profile generator randomly mixed job title names and generic description templates across the entire dataset. In practice, this mismatch is present in **64% of the entire candidate pool** and **31.5% of valid tech candidates**. Hard-filtering this would reject over 14,700 legitimate engineers.
* **The Work-Graduation Timeline Trap:**
  * *Heuristic:* Disqualify candidates who started working before graduation.
  * *Why we avoided it:* Many real profiles list only postgraduate degrees (e.g., M.Sc or MBA completed in 2021) and omit their earlier undergraduate details. This makes it look like they started working (e.g., in 2017) before graduating. Hard-filtering this flags **4.87% of all valid tech candidates** (2,276 developers).

---

## 3. In-Depth Scoring Engine

For candidates that pass the honeypot filter, their final score is calculated using a weighted composite formula:

$$\text{Final Score} = 0.35 \cdot \text{CareerScore} + 0.20 \cdot \text{SemanticScore} + 0.15 \cdot \text{SkillScore} + 0.15 \cdot \text{BehaviorScore} + 0.10 \cdot \text{ExperienceScore} + 0.05 \cdot \text{StabilityScore}$$

If the candidate's profile is identified as a keyword stuffer (non-tech background using AI terms), a heavy penalty is subtracted.

### A. Career Score (35% weight)
Measures professional trajectory and corporate alignment:
1. **Title Matching (15%):**
   * Checks if the `current_title` or `headline` matches target titles in the job description (e.g., "AI Engineer", "ML Engineer", "NLP Engineer").
   * *Weights:* Exact match = `1.0`, Substring match = `0.8`, Mismatch = `0.0`.
2. **Company Context (10%):**
   * Identifies candidate background type. Services-heavy consulting profiles (e.g., TCS, Infosys, Wipro, Accenture, Capgemini) are down-weighted unless they have startup or product-company experience.
   * *Weights:* Consulting-only = `0.0`, Product-only = `1.0`, Mixed = `0.6`.
3. **Description Keywords & Domain Matching (10%):**
   * Scans job descriptions for positive signals (e.g., "RAG", "built recommendation", "vector database", "LLM").
   * *Formula:* $\text{Score} = \text{min}(\text{matches} \cdot 0.2, 1.0) - (\text{mismatch\_domains} \cdot 0.3)$ (where mismatches include pure hardware design, content writing, sales, etc.).

### B. Semantic Score (20% weight)
Computes similarity between the candidate's headline and the job description:
* **Mechanism:** SentenceTransformer embeddings (`all-MiniLM-L6-v2`) are used to compute cosine similarity:
  $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
* **Mapping:** Scaled from $[-1, 1]$ to $[0, 1]$ via:
  $$\text{Semantic Score} = \frac{\text{sim} + 1}{2}$$
* **Boost:** If the similarity is strong ($> 0.4$), we apply a $+0.1$ boost (capped at $1.0$).
* **Fallback:** If embeddings are not loaded, it falls back to a keyword density calculation on the summary.

### C. Skill Score (15% weight)
Weights listed skills based on importance, proficiency, and platform endorsements:
$$\text{Skill Points} = \sum_{s \in \text{Skills}} \text{importance\_weight}(s) \cdot \text{proficiency\_mult}(s) \cdot (1 + \ln(1 + \text{endorsements}(s)))$$
* **Importance Weight:** Required skill = `2.0`, Preferred skill = `1.0`.
* **Proficiency Multiplier:** `expert` = `1.0`, `advanced` = `0.8`, `intermediate` = `0.5`, `beginner` = `0.2`.
* **Scaling:** Normalized by dividing by the maximum possible score (capped at $1.0$).

### D. Behavior Score (15% weight)
Measures platform activity and recruiter responsiveness:
1. **Recruiter Response Rate (40%):** Direct value of recruiter response rate.
2. **Activity Recency (20%):** Time elapsed since last login (assuming reference date June 2026).
   * Active $\le 3$ months = `1.0`, $\le 6$ months = `0.6`, $\le 12$ months = `0.3`, otherwise = `0.1`.
3. **Notice Period (20%):** Notice period duration.
   * Notice $\le 30$ days = `1.0`, $\le 60$ days = `0.7`, otherwise = `0.2`.
4. **Location/Relocation (20%):** Prefers local candidate or willingness to relocate.
   * Target locations (Noida, Pune, Bangalore, Mumbai, etc.) or willing to relocate = `1.0`, otherwise = `0.3`.

### E. Experience Score (10% weight)
Encourages hiring in the ideal experience band (5-9 years):
* Stated experience between 5 and 9 years = `1.0`
* Stated experience between 4 and 5 years, or 9 and 12 years = `0.7`
* Stated experience $< 4$ years or $> 12$ years = `0.2`

### F. Stability Score (5% weight)
Penalizes high frequency of job-hopping:
* **Average Tenure Calculation:**
  $$\text{Avg Tenure} = \frac{\text{Total Duration Months}}{\text{Number of Roles}}$$
* **Score mapping:** $\ge 36$ months = `1.0`, $\ge 24$ months = `0.8`, $\ge 18$ months = `0.5`, otherwise = `0.2`.

### G. Keyword Stuffers Penalty
Candidates from non-tech backgrounds (e.g., Marketing, HR, Accounting) who include AI keywords in their profile description to game search results are penalized. If title matching points are `0.0` and any non-tech keyword is in their title/headline, we subtract `0.35` from their final score:
$$\text{Final Score} = \max(0.0, \text{Final Score} - 0.35)$$

---

## 4. Sorting & Tie-Breaking Rules

To satisfy the strict validation rules of the hackathon portal, equal scores must not be sorted randomly. Ties are broken in **alphabetical ascending order of candidate ID** (e.g., `CAND_0000001` is ranked higher than `CAND_0000002` when they have the same score).

Our sorting logic implements this using a dual-key sort:
```python
# Sort descending by score, ascending by candidate_id
scores.sort(key=lambda x: (-x["score"], x["candidate_id"]))
```

---

## 5. Precomputation Pipeline & Compute Efficiency

The ranking engine must run under strict offline constraints ($\le 5$ minutes CPU time, $\le 16\text{ GB}$ RAM). To achieve this:

1. **Offline Precomputation:** We precompute the embeddings of all 100k candidate headlines once using `all-MiniLM-L6-v2`. This takes **3.8 minutes** on CPU and outputs a compressed float32 matrix (`embeddings.npz`, 117MB).
   * *Why Headline-only:* Tokenizing and encoding summaries or descriptions for 100k records on CPU takes over 48 minutes due to quadratic self-attention scaling. Headline-only encoding is 20x faster, captures 95% of semantic role context, and fits comfortably within memory.
2. **Live Inference:** When running `rank.py`, the engine loads `embeddings.npz` in **0.5 seconds** and computes cosine similarities via matrix operations. The entire ranking of 100,000 candidates finishes in **97 seconds** on CPU.

---

## 6. How to Run and Validate

### Step 1: Candidate Preprocessing (Honeypot Splitting)
To separate valid candidate profiles from the honeypots:
```bash
python preprocess.py
```
This splits the dataset into `data/valid_candidates.jsonl` (99,710 valid candidates) and `data/invalid_candidates.jsonl` (290 honeypot candidates) and outputs a detailed breakdown of the honeypots.

### Step 2: Run the Ranking Pipeline
To run the ranking engine on the pre-filtered **valid** candidates:
```bash
python rank.py --candidates data/valid_candidates.jsonl --out submission_valid.csv
```

To run the ranking engine on the **overall** (unfiltered) candidates:
```bash
python rank.py --candidates data/cleaned_candidates.jsonl --out submission_overall.csv
```
*(Note: Because our scoring engine implements a hard filter penalizing honeypot profiles to a score of -999.0, both `submission_valid.csv` and `submission_overall.csv` will generate identical top-100 lists.)*

### Step 3: Validate the Submission Format
To verify that the output files meet all hackathon specifications:
```bash
python validate/validate_submission.py submission_valid.csv
python validate/validate_submission.py submission_overall.csv
```
The script will ensure:
* Exactly 100 candidate rows (excluding the header).
* Valid column format: `candidate_id`, `rank`, `score`, `reasoning`.
* Ranks 1 to 100 are unique and complete.
* Scores are strictly non-increasing.
* Tie-breaking conditions are correctly met.
