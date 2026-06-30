# Preprocessing Validation & Scoring Engine Audit Report

This report documents the detailed scoring distributions, validation status checks, and data quality penalties applied to candidates in the **Redrob Intelligent Candidate Discovery & Ranking Challenge**. 

It specifically analyzes:
1. **Validation Penalties & Disqualifications**: How scores are deducted for data quality issues, anomalies, or suspicious patterns.
2. **Invalid Candidate Statistics**: Analysis of the 75,153 profiles marked as `INVALID`.
3. **Comparison of Output Files**: Why the baseline `submission.csv` contains invalid candidates, whereas the new `top_100_candidates.csv` is fully cleaned and optimized.

---

## 1. Executive Summary

During Stage 1 (Preprocessing and Validation), candidate profiles were evaluated against a series of schema, career timeline, skill credibility, and behavioral rules. Each candidate started with a **base validation score of 100.0**, from which deductions were subtracted. Candidates were classified into four categories:
- **VALID** (Validation Score $\ge 80.0$) - Eligible for ranking.
- **REVIEW** (Validation Score $60.0 \le S < 80.0$) - Eligible for ranking.
- **WEAK** (Validation Score $40.0 \le S < 60.0$) - Eligible for ranking with penalty.
- **INVALID** (Validation Score $< 40.0$) - Disqualified and excluded from final ranking.

### Dataset & Output Status Distributions

| Metric / Dataset | Full Dataset (100k) | Old `submission.csv` (100) | New `top_100_candidates.csv` (100) |
| :--- | :--- | :--- | :--- |
| **Total Candidates** | **100,000** | **100** | **100** |
| **VALID Profiles** | 14,019 (14.02%) | 71 (71.0%) | 100 (100.0%) |
| **REVIEW Profiles** | 9,111 (9.11%) | 20 (20.0%) | 0 (0.0%) |
| **WEAK Profiles** | 1,717 (1.72%) | 0 (0.0%) | 0 (0.0%) |
| **INVALID Profiles** | 75,153 (75.15%) | **9** (9.0%) | **0** (0.0%) |

> [!WARNING]
> The baseline `submission.csv` contains **9 INVALID candidates** and **20 REVIEW candidates**. Our updated pipeline generated a production-grade ranking in `top_100_candidates.csv` which has **100% VALID** candidates, ensuring absolute data integrity for downstream search and retrieval.

---

## 2. Validation Penalty & Deduction Framework

The candidate validation score is calculated using the following deduction values (baseline 100.0):

### 2.1 Deduction Points Table

| Category | Specific Risk / Anomaly | Deduction Points | Category Cap | Key File Source |
| :--- | :--- | :---: | :---: | :--- |
| **Schema Quality** | Malformed keys or critical schema violations | **30.0** | **40.0** | `schema_validator.py` |
| | Missing minor fields (e.g. summary, headline) | **10.0** | | |
| **Career Timeline** | Chronological timeline error (start > end date, future dates) | **15.0** | **35.0** | `career_validator.py` |
| | Negative job duration log | **20.0** | | |
| | Claimed experience vs actual duration mismatch | **10.0** | | |
| | Concurrent employment overlaps (>90 days overlap) | **10.0** | | |
| | Insufficient career length for Executive title (< 2 years) | **15.0** | | |
| | Severe career regression (Executive to Junior title) | **15.0** | | |
| **Skill Credibility** | Expert skill inflation (e.g. 15 expert skills with <3y career) | **15.0** | **35.0** | `skill_validator.py` |
| | Skill duration exceeds total career history duration | **15.0** | | |
| | Skill-employment inconsistency (claims tech skills but non-tech exp) | **10.0** | | |
| **Platform Behavior** | Behavioral engagement score < 40.0 | **15.0** | **25.0** | `signal_validator.py` |
| | Behavioral engagement score between 40.0 and 60.0 | **7.0** | | |
| | Out-of-bounds behavioral signal data values | **5.0** | | |
| **Honeypot Risks** | Fraud indicators (e.g. timeline mismatches, template copypasta) | **honeypot_score * 0.8** | **80.0** | `honeypot_detector.py` |

### 2.2 Critical Hard Caps (Auto-Disqualifications)
Regardless of the accumulated deductions, a candidate's validation score is **instantly capped at 35.0 (forcing INVALID status)** if:
1. **Any Hard Disqualifier** from `jd_validator.py` is triggered (e.g., location outside India, pure consulting background, CV/Speech background with no NLP/Search matching the JD, excessive job hopping).
2. **Honeypot Score $\ge 40.0$** (representing a high probability of a generated, synthetic, or bot profile).

---

## 3. Analysis of Invalid Candidates in the 100k Pool

Out of 100,000 evaluated candidates, **75,153 (75.15%)** were classified as `INVALID`.

- **Average Validation Score of Invalid Candidates**: **27.39** / 100.0

### 3.1 Validation Score Distribution of Invalid Candidates
The score distribution of disqualified profiles highlights the impact of the 35.0 hard cap:

- **Score 0 to 10**: 3,973 candidates
- **Score 11 to 20**: 15,856 candidates
- **Score 21 to 30**: 10,101 candidates
- **Score 31 to 35**: 45,018 candidates (60% of invalid candidates fall here due to the disqualifier cap)
- **Score 36 to 40**: 205 candidates

### 3.2 Top 15 Specific Disqualification Reasons & Frequencies
The table below shows the top 15 most frequent disqualification flags and code violations across all `INVALID` candidates:

| Disqualification Flag / Penalty Message | Frequency in Pool | Category / Explanation |
| :--- | :---: | :--- |
| **Capped due to high honeypot probability** | 46,789 | Honeypot score $\ge$ 40.0 (Timeline anomalies or templated text) |
| **DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND** | 18,240 | Background in Computer Vision or Speech; lack of Search/NLP |
| **DISQUALIFIED: LOCATION_OUTSIDE_INDIA** | 11,302 | Candidate is located outside India and unwilling to relocate |
| **DISQUALIFIED: LOCATION_OUTSIDE_INDIA, PURE_CV_SPEECH_BACKGROUND** | 3,998 | Multiple hard exclusions (Location + CV/Speech focus) |
| **DISQUALIFIED: CONSULTING_ONLY_BACKGROUND** | 3,972 | Candidate has only worked at consulting giants (TCS, Infosys, etc.) |
| **DISQUALIFIED: PURE_RESEARCH_BACKGROUND** | 2,246 | Purely academic background with no industry/deployment experience |
| **DISQUALIFIED: CONSULTING_ONLY_BACKGROUND, PURE_CV_SPEECH_BACKGROUND** | 1,472 | Multiple hard exclusions (Consulting + CV/Speech focus) |
| **DISQUALIFIED: TITLE_CHASER_JOB_HOPPER** | 1,140 | Job hopping: average tenure $\le$ 18 months across $\ge$ 3 switches |
| **DISQUALIFIED: LOCATION_OUTSIDE_INDIA, CONSULTING_ONLY_BACKGROUND** | 846 | Multiple hard exclusions (Location + Consulting focus) |
| **DISQUALIFIED: PURE_RESEARCH_BACKGROUND, PURE_CV_SPEECH_BACKGROUND** | 687 | Multiple hard exclusions (Academia + CV/Speech focus) |
| **DISQUALIFIED: CONSULTING_ONLY_BACKGROUND, PURE_RESEARCH_BACKGROUND** | 561 | Multiple hard exclusions (Consulting + Academia focus) |
| **DISQUALIFIED: LOCATION_OUTSIDE_INDIA, PURE_RESEARCH_BACKGROUND** | 464 | Multiple hard exclusions (Location + Academia focus) |
| **DISQUALIFIED: LANGCHAIN_ONLY_SHORT_EXPERIENCE** | 433 | LLM skills < 12 months, lacking core NLP/ML foundation |
| **DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND, TITLE_CHASER_JOB_HOPPER** | 386 | Multiple hard exclusions (CV/Speech focus + Job hopper) |
| **DISQUALIFIED: LOCATION_OUTSIDE_INDIA, CONSULTING_ONLY_BACKGROUND, PURE_CV_SPEECH_BACKGROUND** | 332 | Triple hard exclusion check failure |

---

## 4. Disqualified Candidates Audited from `submission.csv`

The baseline `submission.csv` ranked **9 invalid candidates** in the Top 100. Our pipeline has successfully disqualified them. Below is the detailed breakdown of the penalties and disqualification reasons for each:

| Rank in Submission | Candidate ID | Submission Score | Preprocessing Validation Score | Specific Invalidation Reason(s) & Applied Penalties |
| :---: | :--- | :---: | :---: | :--- |
| 4 | CAND_0039754 | 88.65 | 35.0 | • Claimed experience (16.2 yrs) differs significantly from career history sum (8.2 yrs)<br>• Candidate claims 16.2 years of experience but graduated in 2020 (max realistic: 7 years)<br>• Career consistency issue: Claimed experience (16.2 yrs) differs significantly from career history sum (8.2 yrs) (-10)<br>• Honeypot risk: Candidate claims 16.2 years of experience but graduated in 2020 (max realistic: 7 years) (-32)<br>• Capped due to high honeypot probability |
| 7 | CAND_0017648 | 86.6 | 35.0 | • DISQUALIFIED: TITLE_CHASER_JOB_HOPPER |
| 35 | CAND_0031842 | 84.15 | 35.0 | • Skill 'Hugging Face Transformers' duration (50 months) exceeds candidate's total career history duration (42 months)<br>• Skill credibility issue: Skill 'Hugging Face Transformers' duration (50 months) exceeds candidate's total career history duration (42 months) (-15)<br>• DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND |
| 36 | CAND_0072489 | 84.05 | 35.0 | • DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND |
| 37 | CAND_0032515 | 83.95 | 35.0 | • Skill 'PyTorch' duration (69 months) exceeds candidate's total career history duration (61 months)<br>• Skill 'Semantic Search' duration (93 months) exceeds candidate's total career history duration (61 months)<br>• Skill credibility issue: Skill 'PyTorch' duration (69 months) exceeds candidate's total career history duration (61 months) (-30)<br>• DISQUALIFIED: LOCATION_OUTSIDE_INDIA |
| 40 | CAND_0033445 | 83.7 | 35.0 | • DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND |
| 72 | CAND_0052335 | 82.5 | 35.0 | • Skill 'PyTorch' duration (83 months) exceeds candidate's total career history duration (76 months)<br>• Skill credibility issue: Skill 'PyTorch' duration (83 months) exceeds candidate's total career history duration (76 months) (-15)<br>• DISQUALIFIED: PURE_CV_SPEECH_BACKGROUND |
| 75 | CAND_0025109 | 82.45 | 35.0 | • DISQUALIFIED: TITLE_CHASER_JOB_HOPPER |
| 92 | CAND_0055992 | 82.1 | 35.0 | • Claimed experience (16.9 yrs) differs significantly from career history sum (6.7 yrs)<br>• Candidate claims 16.9 years of experience but graduated in 2013 (max realistic: 14 years)<br>• Career consistency issue: Claimed experience (16.9 yrs) differs significantly from career history sum (6.7 yrs) (-10)<br>• Honeypot risk: Candidate claims 16.9 years of experience but graduated in 2013 (max realistic: 14 years) (-32)<br>• Capped due to high honeypot probability |

### Critical Issues Flagged in Submission Candidates:
1. **CV/Speech Background Disqualifier**: 5 candidates (`CAND_0031842`, `CAND_0033445`, `CAND_0052335`, `CAND_0072489`) had Computer Vision or Speech processing backgrounds with zero NLP/ranking match for the Senior AI Engineer (Ranking & Retrieval) role.
2. **Job Hopping**: 2 candidates (`CAND_0017648`, `CAND_0025109`) were flagged as Title Chasers/Job Hoppers (tenure $\le$ 18 months).
3. **Severe Honeypots**: 2 candidates (`CAND_0039754`, `CAND_0055992`) were flagged as high-probability honeypots due to massive chronological experience inflation (e.g. claiming 16.2 and 16.9 years of experience despite graduating in 2020 and 2013 respectively).
4. **Location/Visa restrictions**: `CAND_0032515` was disqualified as they are based outside India and unwilling to relocate.

Our new pipeline outputs (`top_100_candidates.csv`) correctly filter out all 9 of these candidates, replacing them with fully verified, qualified, and high-scoring `VALID` candidates.

