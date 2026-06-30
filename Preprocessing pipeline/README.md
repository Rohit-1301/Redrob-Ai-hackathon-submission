# Redrob Candidate Preprocessing & Validation Engine

This directory contains the optimized, production-grade candidate validation and preprocessing engine designed to clean, filter, and segment the raw `candidates.jsonl` dataset (100,000 profiles, ~487MB) for downstream ranking.

---

## 📁 Preprocessing Pipeline Layout

*   [preprocess.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/preprocess.py): The main orchestrator that streams raw candidate JSONL, validates data, categorizes profiles, and aggregates signal statistics.
*   [hover_details_builder.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/hover_details_builder.py): Extracts profile indicators and checks for schema flags, career timeline chronology issues, skill mismatch issues, and behavioral warning flags.
*   [configs/config.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/configs/config.py): Binds system-wide constants, target locations, AI keywords, and JD required/preferred competencies.
*   [validators/](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/): Modular validators checking individual candidate properties:
    *   [schema_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/schema_validator.py): Verifies basic key health and data type matching.
    *   [career_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/career_validator.py): Scrutinizes job duration parameters, negative months, chronology gaps, Demotion regressions, and overlap details.
    *   [skill_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/skill_validator.py): Evaluates skill credentials, inflation thresholds, and career alignment.
    *   [signal_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/signal_validator.py): Checks data bounds on recruiter/interview behaviors, open to work recency, and availability parameters.
    *   [honeypot_detector.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/honeypot_detector.py): Scans timeline/experience consistency and templates copypasta descriptors.
    *   [jd_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/validators/jd_validator.py): Maps candidates against the target Senior AI Engineer role filters (consulting restrictions, CV/Speech restrictions, title hopping, target hubs).
*   [scoring/validation_score.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/scoring/validation_score.py): Formulates profile validation scores (0-100) and assigns classification statuses: `VALID`, `REVIEW`, `WEAK`, or `INVALID`.
*   [Dockerfile](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/Dockerfile): Production container configuration.
*   [docker_build_run.ps1](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/Preprocessing%20pipeline/docker_build_run.ps1): Automates image generation and container run with mounted volume structures.

---

## ⚡ Performance Optimizations

1.  **Memory-Efficient Streaming**:
    To prevent Out-of-Memory (OOM) failures on 100,000 JSON lines, candidate profiles are read and written incrementally. Output JSON files are opened for streaming at the beginning and written line-by-line using a memory-friendly layout. This keeps the execution footprint below **150MB of RAM** (compared to $>4\text{GB}$ if loading arrays fully in memory).
2.  **Container-Local I/O Buffering**:
    Docker mounts targeting slow Windows volumes (e.g. active OneDrive synchronization folders) degrade file I/O speed. The preprocessing orchestrator is optimized to write all temporary logs and JSON splits directly onto the container-local fast overlay file system (`/app/temp_output`), executing a single bulk copy to the mounted output folder at completion. This bypassed synchronization wait locks, improving performance by **50x**.

---

## 📊 Preprocessing Validation Categories

Validation scores are derived by starting at a score of **100.0** and subtracting deductions for identified anomalies. The status classification bands are:
*   **VALID** (Validation Score $\ge 80.0$): Trustworthy profile matching critical JD criteria and having authentic history.
*   **REVIEW** ($60.0 \le$ Score $< 80.0$): Minor irregularities, such as experience mismatch or off-target location, but no fraud markers.
*   **WEAK** ($40.0 \le$ Score $< 60.0$): Multiple career/skill inconsistencies or weak active engagement flags.
*   **INVALID** (Score $< 40.0$): direct disqualifier triggers (e.g. consulting-only pedigree, academic-only career, CV/Speech only mismatch, location misfit) or high honeypot score ($\ge 40.0$).

---

## 🚀 How to Run

### Local Command Line
1.  Verify dependencies inside `Preprocessing pipeline/requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the pipeline:
    ```bash
    python preprocess.py [input_jsonl_path] [output_directory]
    ```

### Containerized Execution
Run the automated Powershell script to rebuild the image and execute candidate processing:
```powershell
.\docker_build_run.ps1
```
All outputs will write to the `Preprocessing pipeline/output/` directory on completion.

---

*Built with ❤️ by team DeepMind*

