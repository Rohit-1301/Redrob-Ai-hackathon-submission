# Redrob Candidate Discovery & Ranking System

This folder contains the complete, production-grade, containerized candidate discovery and ranking system for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

The system ingests preprocessed candidate profile segments, parses the Senior AI Engineer Job Description (JD), computes semantic similarity using SentenceTransformers and FAISS vector indexing, applies a multi-factor hybrid scoring mechanism, and ranks candidates to output the optimal Top 100 talent pool.

---

## 🚀 Quick Start

You can orchestrate and run this entire system using the provided **Makefile**.

### 1. Local execution
To run the ranking pipeline locally:
```bash
make run
```
To launch the Streamlit sandbox dashboard:
```bash
make app
```

### 2. Containerized execution (Docker Compose)
To build the Docker image:
```bash
make docker-build
```
To execute the pipeline inside a non-root container (outputs will be written back to the host `outputs/` and `reports/` folders):
```bash
make docker-run
```
To run the Streamlit interactive dashboard in Docker:
```bash
make docker-app
```
To clean container cache and volumes:
```bash
make docker-clean
```

---

## 📐 Architecture & Hybrid Scoring Engine

The ranking engine uses a multi-factor scoring mechanism to ensure high alignment with the JD while accounting for candidate intent, profile credibility, and background suitability.

### Scoring Weights
- **Semantic Similarity (40%)**: Cosine similarity between candidate embedding (engineered from profile headline, summary, skills, and career history descriptions) and parsed JD embedding using the `BAAI/bge-small-en-v1.5` model.
- **Career Score (20%)**: Experience years alignment (preferred range is 5-9 years, with moderate penalties for over/under-qualification), job title seniority, and company type.
- **Skill Score (15%)**: Match rate against JD mandatory (`JD_REQUIRED_SKILLS`) and preferred (`JD_PREFERRED_SKILLS`) competencies.
- **Behavior Score (10%)**: Computed based on recruiter response rates, interview attendance rate, open-to-work flag, login recency, and overall platform activity.
- **Quality Score (10%)**: Profile validation and completeness scoring from the preprocessing phase.
- **Product Company Score (5%)**: Extra weight for candidates who have spent their career outside IT consulting giants.

### Multipliers & Penalties
- **Category Multipliers**: Applied based on preprocessed split classification:
  - `VALID` $\times$ **1.00**
  - `REVIEW` $\times$ **0.85**
  - `WEAK` $\times$ **0.60**
- **Honeypot Penalty (-999 filter)**: Candidates with a honeypot score $>80$ or flagged as honeypot indicators are automatically penalized by $-999.0$, filtering them out of the selection.

---

## 📁 Project Structure

```
SelectedCandidates/
├── app/
│   └── streamlit_app.py      # Streamlit interactive sandbox application
├── config/                   # Configuration bindings
├── data/
│   └── jd_analysis.json      # Structured competencies extracted from JD
├── logs/                     # Pipeline execution logs
├── models/
│   ├── embeddings.pkl        # Cached local candidate embeddings
│   └── faiss/
│       └── index.faiss       # Serialized FAISS IndexFlatIP vector database
├── outputs/
│   ├── top_100_candidates.csv     # Final ranked submission CSV
│   └── top_100_explanations.json  # Explanations for candidate selection
├── reports/
│   ├── final_report.md            # Detailed performance analysis
│   ├── category_distribution.png  # Distribution chart
│   ├── experience_distribution.png# Experience profile histogram
│   ├── score_distribution.png     # Scoring profile comparison
│   └── skill_coverage.png         # Skill match coverage
├── src/
│   ├── explainability/       # Natural language explanations generator
│   ├── ranking/              # Main ranker and sorting engine
│   ├── reporting/            # Report compiling and chart exporter
│   ├── scoring/              # Component-level hybrid scoring formulas
│   ├── semantic/             # SentenceTransformers loader & FAISS indexer
│   └── utils/                # Job description Word document parser
├── Dockerfile                # Non-root, offline-capable docker build instructions
├── docker-compose.yml        # Orchestration configuration
├── Makefile                  # Automated make triggers
└── run_pipeline.py           # Pipeline entry-point coordinator
```

---

## 📜 Compliance and Verification

- The output format of `outputs/top_100_candidates.csv` exactly matches the `sample_submission.csv` format, including columns: `candidate_id`, `rank`, `score`, `reasoning`.
- Sorting is fully deterministic and includes strict tie-breaking where equal scores are sorted in ascending order of `candidate_id`.
- The final output is automatically validated against the official `Redrobsdataset/validate_submission.py` rules on every run, guaranteeing compliance.
