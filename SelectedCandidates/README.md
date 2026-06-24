# Redrob Candidate Discovery & Ranking Engine

This directory contains the core scoring, semantic vector matching, and ranking engine designed for the **Redrob Candidate Discovery & Ranking challenge**. It parses the target Job Description (JD), ingests preprocessed candidate lists (`VALID`, `REVIEW`, `WEAK`), embeds profiles using neural models, indexes them with FAISS, and ranks them to output the top 100 fits.

---

## 📁 Project Structure

*   [run_pipeline.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/run_pipeline.py): Pipeline orchestration script.
*   [src/ranking/ranker.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/src/ranking/ranker.py): Controls Stage 1 pre-filtering (down to 400 profiles) and Stage 2 hybrid sorting.
*   [src/scoring/score_engine.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/src/scoring/score_engine.py): Contains component scoring rules for Career fit, Skills match, Behavioral engagement, Quality validation, and Product Company pedigree.
*   [src/semantic/embeddings.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/src/semantic/embeddings.py): Computes SentenceTransformer embeddings and serializes them in a FAISS index.
*   [src/utils/jd_parser.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/src/utils/jd_parser.py): Parses input Word document (.docx) JDs using python-docx.
*   [src/explainability/explainer.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/src/explainability/explainer.py): Generates detailed structured natural language explanations for candidate matches.
*   [app/streamlit_app.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/app/streamlit_app.py): Streamlit dashboard to interactively inspect candidate scores and explanations.
*   [reports/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/): Evaluation and audit reports folder:
    *   [final_report.md](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/final_report.md): Output ranking summary statistics and charts.
    *   [reportlogic.md](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/reportlogic.md): Scoring weight specifications and visual flowchart.
    *   [honeypot_report.md](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/honeypot_report.md): Details on honeypot detector rules and preprocessing failure stats.
*   [Makefile](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/Makefile): Automation triggers.
*   [Dockerfile](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/Dockerfile) & [docker-compose.yml](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/docker-compose.yml): Non-root Docker execution configuration.

---

## ⚙️ Hybrid Scoring & Ranking Framework

Candidates matching valid/review/weak status are processed across two stages:

### Stage 1: Non-Semantic Pre-filtering
Computes non-semantic profiles for all candidates to compute a maximum potential score (assuming a perfect semantic match of 1.0). The pipeline filters candidate records down to the **top 400** to restrict expensive vector embedding operations to the most viable candidates, guaranteeing lossless candidate selection.

### Stage 2: Semantic Matching & Blended Score
Computes cosine similarity of candidate profile text versus Job Description embedding vectors using SentenceTransformers and FAISS index search. The score components are blended as follows:
1.  **Semantic Match (40% weight)**: Cosine similarity score.
2.  **Career Match (20% weight)**: Match of years of experience (preferred range 5–9 years), title seniority alignment, and non-consulting background pedigree.
3.  **Skill Match (15% weight)**: Required skill intersection (70%) and preferred skill intersection (30%).
4.  **Behavioral Health (10% weight)**: Blend of Computed behavior score (completeness, verified channel points, recruiter responsiveness) and dataset raw behavior score.
5.  **Validation Quality (10% weight)**: Blend of validation score (80%) and credibility score (20%).
6.  **Product Company Pedigree (5% weight)**: 1.0 if the career has zero consulting firm history, 0.0 otherwise.

### Category Multiplier & Penalties
*   **Multiplier**: VALID (x1.00), REVIEW (x0.85), WEAK (x0.60).
*   **Honeypot Penalty**: Subtracts 999.0 if candidate validation honeypot flag is active.

---

## 🚀 Execution Instructions

Use the automated `Makefile` targets to build and run the pipeline:

### 1. Local Run
To run the ranking pipeline locally:
```bash
make run
```
To launch the Streamlit sandbox dashboard:
```bash
make app
```

### 2. Docker Compose
To build the Docker image:
```bash
make docker-build
```
To run candidate ranking container:
```bash
make docker-run
```
To run the Streamlit dashboard inside Docker:
```bash
make docker-app
```
To clean volumes and cache:
```bash
make docker-clean
```
All outputs (ranked CSVs, explanations JSONs, final reports, and score charts) are written to the host `outputs/` and `reports/` directories.
