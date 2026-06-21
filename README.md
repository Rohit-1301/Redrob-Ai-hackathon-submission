# Candidate Preprocessing & Validation Pipeline

Production-grade preprocessing and validation pipeline developed for the Redrob Intelligent Candidate Discovery & Ranking Hackathon. This pipeline is designed to ingest large candidate datasets, analyze profile completeness and chronology, filter out malicious/suspicious synthetic records, and score/classify candidate viability for modern search and ranking systems.

## Project Structure

```
redrobs/
│
├── configs/
│   └── config.py          # Threshold values, target locations, & AI/ML keyword sets
│
├── validators/
│   ├── schema_validator.py  # Top-level key checking and ID structure validation
│   ├── career_validator.py  # Chronology, overlap, regression, and duration check
│   ├── skill_validator.py   # Skill inflation, duration limit, and job title match
│   ├── signal_validator.py  # Bound validator, behavioral & availability scoring
│   ├── honeypot_detector.py # Timeline contradictions and template copy-paste detection
│   └── jd_validator.py      # JD requirements fit, disqualifiers, & pedigree checks
│
├── scoring/
│   └── validation_score.py  # Score synthesis and validation status classification
│
├── outputs/
│   ├── validated_candidates.parquet  # Evaluated output candidate records
│   └── validation_report.json       # Overall pipeline metrics and distributions
│
├── preprocess.py          # Pipeline orchestration script (reads JSON/JSONL)
├── Dockerfile             # Multi-stage production container specification
├── requirements.txt       # Python libraries requirements
└── README.md              # Documentation
```

## Running the Pipeline

### Local Run

1. Install Python 3.11 and dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute the preprocessing pipeline:
   ```bash
   python preprocess.py
   ```
   *Note: You can override the default paths by passing command line arguments:*
   ```bash
   python preprocess.py <input_path> <output_parquet_path> <report_json_path>
   ```

### Docker Run

To build and run the pipeline inside a Docker container:

1. Build the Docker image:
   ```bash
   docker build -t redrob-validator .
   ```
2. Run the image, mounting your input data and output directories:
   ```bash
   docker run -v /absolute/path/to/data:/app/data -v /absolute/path/to/outputs:/app/outputs redrob-validator
   ```

---

## Validation & Scoring Framework

Every candidate is analyzed across several validation layers:

1. **Schema Quality**: Verifies presence of crucial identifiers (`candidate_id`, nested structures).
2. **Career Consistency**: Detects experience mismatches, overlapping employments, and career demotion anomalies.
3. **Skill Credibility**: Flags skill inflation (many expert skills with brief experience) and skill-job context mismatch.
4. **Behavioral Processing**: Aggregates all 23 simulated platform activity signals into custom availability and behavioral metrics.
5. **Honeypot Detection**: Exposes copy-pasted generic templates and profile contradictions.
6. **JD Matching**: Scores candidates against the target Senior AI Engineer JD requirements (e.g. production ML experience, tiering, disqualifiers).

### Candidate Classifications

Based on the final synthesized `validation_score` (0-100):
- **VALID (80-100)**: Trustworthy profile matching critical JD criteria and having authentic history.
- **REVIEW (60-79)**: Minor irregularities (e.g. minor experience mismatch or off-target location, but no fraud).
- **WEAK (40-59)**: Multiple career/skill inconsistencies or weak activity indicators.
- **INVALID (0-39)**: Critical schema failures, high honeypot probability, or direct disqualifier matching (e.g. consulting-only career, academic-only, CV-only, or location misfit).
