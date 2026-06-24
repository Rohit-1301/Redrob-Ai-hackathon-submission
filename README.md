# End-to-End Candidate Discovery, Validation, & Ranking Pipeline

This repository contains the end-to-end automated platform designed for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**. The system filters out fraudulent/unqualified candidate profiles from a dataset of 100,000 records, evaluates viability against a Senior AI Engineer (Ranking & Retrieval) Job Description, and ranks the candidates using a hybrid multi-factor vector model to deliver the top 100 fits.

---

## 📐 System Architecture Workflow

The framework operates as a **two-stage cascaded architecture**:

```mermaid
flowchart TD
    Dataset["Raw Candidates Dataset (Redrobsdataset/candidates.jsonl)"] --> Stage1["Stage 1: Preprocessing & Validation Engine"]
    
    subgraph "Preprocessing Pipeline"
        Stage1 --> Validation["Logical & Quality Validation"]
        Stage1 --> Honeypot["Honeypot & Fraud Detector"]
        Stage1 --> JD_Eligible["JD Eligibility Validator"]
        
        Validation & Honeypot & JD_Eligible --> Classification["Status Splitting"]
        Classification --> Valid_Split["valid.json (14.0%)"]
        Classification --> Review_Split["review.json (9.1%)"]
        Classification --> Weak_Split["weak.json (1.7%)"]
        Classification --> Invalid_Split["invalid.json (75.2%)"]
    end
    
    Valid_Split & Review_Split & Weak_Split --> Stage2["Stage 2: Semantic Vector Ranking Engine"]
    Invalid_Split --> Excluded["Excluded Pool"]
    
    subgraph "Selected Candidates Engine"
        Stage2 --> Parsed_JD["Parsed JD Competencies"]
        Stage2 --> PreFilter["Stage 1 Lossless Pre-Filtering"]
        Stage2 --> Embeddings["SentenceTransformers & FAISS Vector Index"]
        Stage2 --> HybridScore["Hybrid Score Blender (40% Semantic, 60% Pedigree)"]
        
        PreFilter & Embeddings & HybridScore --> Ranking["Sorted Ranking & Secondary Tie-Breaking"]
    end
    
    Ranking --> Top100["Top 100 Ranked Candidates (outputs/top_100_candidates.csv)"]
    Ranking --> Explain["Detailed Matches (outputs/top_100_explanations.json)"]
```

---

## 📁 Repository Structure

*   [Redrobsdataset/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Redrobsdataset/): Workspace folder containing the raw source candidates dataset (`candidates.jsonl`), job description documents, and submission validators.
*   [Preprocessing pipeline/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/): Stage 1 data validation system. Responsible for filtering missing schemas, chronology conflicts, skill inflation, and honeypot indicators. Outlines statistics inside `Preprocessing pipeline/output/validation_report.json`.
*   [SelectedCandidates/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/): Stage 2 semantic vector indexing, FAISS retrieval engine, and hybrid scoring blender.
*   [configs/config.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/configs/config.py): Shared settings (AI keywords, required competencies, target locations, consulting companies).
*   [validators/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/): Validation modules imported across preprocess and ranking steps.
*   [scoring/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/scoring/): Synthesis scoring logic.

---

## ⚡ Execution Roadmap

Follow these two sequential steps to compile data and generate candidate selections:

### Step 1: Preprocess Candidate Records
Executes data validators on 100,000 candidates to split them into clean lists.
1.  Navigate to the preprocessing folder:
    ```bash
    cd "Preprocessing pipeline"
    ```
2.  Run the validation container:
    ```powershell
    .\docker_build_run.ps1
    ```
    *Output splits will be saved under `Preprocessing pipeline/output/`.*

### Step 2: Rank Candidates & Select Top 100
Ingests preprocessed VALID/REVIEW/WEAK splits, executes semantic vector indexing, scores credentials, and ranks the candidates.
1.  Navigate to the selection folder:
    ```bash
    cd "SelectedCandidates"
    ```
2.  Build the ranking docker container:
    ```bash
    make docker-build
    ```
3.  Execute ranking:
    ```bash
    make docker-run
    ```
    *Top 100 CSV outputs are written back to `SelectedCandidates/outputs/top_100_candidates.csv` and report analytics plots are stored under `SelectedCandidates/reports/`.*

---

## 📜 Compliance and Verification

All output ranked results are deterministically sorted and automatically verified on completion using `Redrobsdataset/validate_submission.py`. Detailed system logic reports and anti-fraud indicators can be found inside:
*   [SelectedCandidates/reports/reportlogic.md](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/reportlogic.md) (Flowchart & scoring formulas)
*   [SelectedCandidates/reports/honeypot_report.md](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/SelectedCandidates/reports/honeypot_report.md) (Honeypot audits and validator rules)
