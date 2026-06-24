# Redrob Candidate Validation & Honeypot Detection Audit Report

This report documents the detailed technical rules, heuristic algorithms, and logic validation frameworks designed to flag synthetic profiles (**Honeypots**) and verify profile credibility in the **Redrob Candidate Validation Pipeline**.

---

## 1. What are Profile Honeypots?

**Honeypots** are programmatic, synthetic, or fraudulent candidate profiles designed to game automated recruitment systems. They often look highly qualified at a high level (e.g., claiming expert status in advanced AI frameworks), but contain underlying logical contradictions, date timeline anomalies, or templated copy-pasted details. 

Key patterns of honeypots detected in this repository:
1. **Date Chronology Fraud**: Profiles claiming decades of experience or executive titles with graduation dates that make the timeline physically impossible.
2. **Copypasta template stuffing**: Boilerplate job description strings copied directly from templates into the work history, completely misaligned with the job titles claimed.
3. **Synthetic distribution artifacts**: Programmatic data generation artifacts, such as identical month durations or endorsements across entirely different tech skills.
4. **Keyword Stuffing**: Claiming advanced AI/ML skills to pass query matching while the candidate's actual job title/history is in an entirely unrelated domain (e.g., Accountant, HR Manager, Mechanical Designer).

---

## 2. Honeypot Detection Logic & Rules

Honeypot detection is processed inside [honeypot_detector.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/honeypot_detector.py). The rules compute a cumulative `honeypot_score` between `0.0` and `100.0`.

### 2.1 Timeline & Graduation Anomalies
* **Rule 1: Impossible Work-Graduation Gap**
  * *Heuristic*: Checks the minimum graduation year from the `education` array against the earliest start date year in `career_history`.
  * *Condition*: $\text{Min Graduation Year} - \text{Earliest Job Start Year} > 6$.
  * *Logic*: An individual starting professional career work more than 6 years before graduating represents a severe timeline contradiction.
  * *Penalty*: **+40.0 Honeypot Score** (Flags `IMPOSSIBLE_WORK_GRADUATION_TIMELINE`).
* **Rule 2: Impossible Experience Duration**
  * *Heuristic*: Compares the candidate's claimed `years_of_experience` against the total time elapsed since their graduation.
  * *Condition*: $\text{Claimed Experience} > (2026 - \text{Min Graduation Year} + 1) + 2$ (with 2 years padding allowed).
  * *Logic*: A candidate claiming 15 years of experience who graduated in 2021 can have at most 6 years of post-graduation experience.
  * *Penalty*: **+40.0 Honeypot Score** (Flags `IMPOSSIBLE_EXPERIENCE_DURATION`).

### 2.2 Templated Copypasta & Mismatch Detection
* **Rule 3: Title-Description Template Mismatches**
  * *Heuristic*: Scans job descriptions in the career history for known boilerplate phrases. If a template match is found, checks if the job title belongs to an allowed set.
  * *Templates checked*:
    1. **Mechanical Design**: `"mechanical engineering design role"` (Requires title words: `mechanical`, `hardware`, `design`, `engineer`, `cad`, `creo`, `ansys`).
    2. **Customer Support**: `"customer support team lead"` (Requires title words: `support`, `customer`, `service`, `helpdesk`, `help desk`).
    3. **Content Writing**: `"content writing and seo"` (Requires title words: `content`, `writer`, `seo`, `editor`, `marketing`, `copywriter`, `editorial`).
    4. **Business Analyst**: `"business analyst at a consulting"` (Requires title words: `analyst`, `consultant`, `business`, `consulting`, `strategy`).
    5. **Brand Design**: `"brand design and creative"` (Requires title words: `design`, `brand`, `creative`, `art`, `marketing`, `graphic`, `designer`).
    6. **Accounting**: `"senior accounting role"` (Requires title words: `accounting`, `accountant`, `finance`, `financial`, `auditor`, `gl`).
    7. **Operations**: `"operations management role"` (Requires title words: `operations`, `operator`, `ops`, `logistics`, `warehouse`, `fulfillment`).
  * *Penalty*: **+30.0 Honeypot Score** per mismatch incident (Flags `TITLE_DESCRIPTION_MISMATCH`).

### 2.3 Synthetic Artifact Anomalies
* **Rule 4: Identical Skill Durations**
  * *Heuristic*: Analyzes the `duration_months` attribute for candidates listing $\ge 5$ skills.
  * *Condition*: Length of the unique set of skill durations is exactly $1$.
  * *Logic*: In organic profiles, the durations of different technical skills differ (e.g. Python for 4 years, PyTorch for 2 years). Identical month counts across all skills indicates synthetic programmatic generation.
  * *Penalty*: **+25.0 Honeypot Score** (Flags `SUSPICIOUS_SKILL_DISTRIBUTION`).

### 2.4 Profile Keyword Stuffing
* **Rule 5: Non-Tech Profile Stuffing**
  * *Heuristic*: Identifies if a candidate's current title is non-technical (e.g. `Marketing Manager`, `Accountant`, `Customer Support`, `Operations Manager`, `HR Manager`) but they claim $\ge 5$ advanced AI/ML skills.
  * *Penalty*: **+50.0 Honeypot Score** (Flags `KEYWORD_STUFFED_HONEYPOT`).

---

## 3. General Validation Logic Frameworks

In addition to honeypot checks, candidates are verified against five baseline quality validators:

### 3.1 Schema Validator ([schema_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/schema_validator.py))
Verifies structural compliance:
* Missing top-level keys (`candidate_id`, `profile`, `career_history`, `education`, `skills`, `redrob_signals`).
* Formatting constraints for Candidate ID (regex: `^CAND_[0-9]{7}$`).
* Missing profile attributes (`headline`, `summary`, `location`, `years_of_experience`, `current_title`).
* Validation of data types (e.g., lists for career history, objects for profile).

### 3.2 Career Validator ([career_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/career_validator.py))
Validates timeline health:
* **Future starts/ends**: Job dates exceeding the reference date of June 20, 2026.
* **Invalid chronology**: Job start date after its end date.
* **Negative durations**: Negative months values in career logs.
* **Employment overlap**: Overlaps between different jobs exceeding 90 days.
* **Career Regression**: Demotion from executive/VP titles to junior/intern titles.
* **Low Experience Executive**: Candidates claiming VP/Director titles with $<2$ years of total experience.

### 3.3 Skill Validator ([skill_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/skill_validator.py))
Validates credential integrity:
* **Skill Inflation**: $\ge 15$ expert skills with $<3$ years of career history, or $\ge 30$ total skills with $<2$ years of experience.
* **Skill Duration Mismatch**: Any skill duration exceeding the candidate's total career history duration (plus 6 months padding).
* **Skill-Employment Mismatch**: Claiming core ML/AI skills but having zero ML/AI keywords in job titles or descriptions.

### 3.4 Signal Validator ([signal_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/signal_validator.py))
Processes 23 platform activity markers to compute:
* **Availability Score (0-100)**: Higher scores for open-to-work flags, recent active dates ($\le 7$ days), high response rates, and short notice periods ($\le 30$ days).
* **Behavioral Score (0-100)**: Higher scores for profile completeness, linked active GitHub, endorsements, connections, identity verification, and fast recruiter response times ($\le 24$ hours).

### 3.5 JD Eligibility Validator ([jd_validator.py](file:///c:/Users/rg975/OneDrive%20-%20Vidyalankar%20Institute%20of%20Technology/23101A0019%20Rohit%20Gupta%20INFT-A/redrobs/validators/jd_validator.py))
Flags hard disqualifiers against the Senior AI Engineer role:
* **Location Check**: Candidate is outside India and unwilling to relocate.
* **Consulting Exclusion**: Career history entirely consisting of consulting firms (Wipro, Infosys, TCS, Cognizant, etc.).
* **Pure Research Exclusion**: Purely academic career without deployment or system scaling experience.
* **CV/Speech Exclusion**: Competency background in computer vision (YOLO, OpenCV) or speech (TTS, Whisper) with zero NLP/Search/Information Retrieval experience.
* **Title Chasing**: Swapping employers every $\le 1.8$ years on average.

---

## 4. Audit Validation & Honeypot Statistics

Running the pipeline on the full dataset of **100,000 candidates** revealed the following status distribution and failure metrics:

### 4.1 Candidate Status Classification Distribution
* **VALID**: **14,019** candidates (14.02%)
* **REVIEW**: **9,111** candidates (9.11%)
* **WEAK**: **1,717** candidates (1.72%)
* **INVALID**: **75,153** candidates (75.15%)

### 4.2 Top Identified Failure Reasons
Below are the count statistics of validation issues and honeypot flags identified during audit:

| Code / Failure Name | Incidents Detected | Category | Impact |
| :--- | :--- | :--- | :--- |
| `TITLE_DESCRIPTION_MISMATCH` | 152,735 | Honeypot | Deducts 30 points per incident; triggers capping to 35.0 (INVALID) |
| `SKILL_DURATION_MISMATCH` | 29,777 | Skill Mismatch | Deducts 15 points; invalidates credibility |
| `SKILL_EMPLOYMENT_INCONSISTENCY` | 14,173 | Skill Pedigree | Deducts 10 points |
| `IMPOSSIBLE_EXPERIENCE_DURATION` | 7,734 | Honeypot | Deducts 40 points; triggers capping to 35.0 (INVALID) |
| `IMPOSSIBLE_WORK_GRADUATION_TIMELINE`| 2,282 | Honeypot | Deducts 40 points; triggers capping to 35.0 (INVALID) |
| `KEYWORD_STUFFED_HONEYPOT` | 1,676 | Honeypot | Deducts 50 points; triggers capping to 35.0 (INVALID) |
| `EXPERIENCE_MISMATCH` | 49 | Career Mismatch| Deducts 10 points |
| `SUSPICIOUS_SKILL_DISTRIBUTION` | 1 | Honeypot | Deducts 25 points |
| `SKILL_INFLATION` | 1 | Skill Mismatch | Deducts 15 points |
