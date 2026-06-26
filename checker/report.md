# Candidate Submission Validation & Honeypot Analysis Report
**Generated on:** 2026-06-26 18:21:09

This report validates submitted competitor ranking `.csv` files against formatting requirements and audits them for synthetic honeypot trap profiles.

## 1. High-Level Submissions Summary

| Submission File | Total Rows | Valid Candidates | Honeypots Found | Honeypot Rate % | Format Check | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| adit_submission.csv | 100 | 96 | 4 | 4.0% | ❌ ERRORS | ❌ DISQUALIFIED |
| kamran_submission.csv | 100 | 92 | 8 | 8.0% | ✅ OK | ✅ PASSED |
| ndk_submission.csv | 100 | 99 | 1 | 1.0% | ✅ OK | ✅ PASSED |
| rohit_candidates.csv | 100 | 88 | 12 | 12.0% | ✅ OK | ❌ DISQUALIFIED |
| submission_valid.csv | 100 | 100 | 0 | 0.0% | ✅ OK | ✅ PASSED |

---

## 2. Detailed Diagnostics per Submission

### File: `adit_submission.csv`
> [!CAUTION]
> **Status: DISQUALIFIED** (Format Check Failed)
> - *Format Error:* Missing required column(s): score, reasoning

**Submissions breakdown:**
- Stated rows: `100`
- Valid candidates: `96`
- Traps/Honeypots: `4`
- Unregistered candidate IDs: `0`

**Flagged Honeypots details:**

| Rank | Candidate ID | Candidate Name | Current Title | Honeypot Reason |
| :---: | :---: | :--- | :--- | :--- |
| 1 | `CAND_0068513` | Tanya Joshi | Computer Vision Engineer | Started at sarvam ai in 2022, but company was founded in 2023 |
| 20 | `CAND_0005649` | Riya Kapoor | Senior Data Scientist | Started at glance in 2018, but company was founded in 2019 |
| 30 | `CAND_0065878` | Suresh Kapoor | Senior Data Scientist | Started at rephrase.ai in 2018, but company was founded in 2019 |
| 90 | `CAND_0069248` | Yash Kapoor | AI Research Engineer | Started at sarvam ai in 2021, but company was founded in 2023 |

---

### File: `kamran_submission.csv`
> [!NOTE]
> **Status: PASSED** (Honeypot Rate: **8.0%** is within the allowed limit)
> - Format is valid. 0% honeypot presence. Fully compliant.

**Submissions breakdown:**
- Stated rows: `100`
- Valid candidates: `92`
- Traps/Honeypots: `8`
- Unregistered candidate IDs: `0`

**Flagged Honeypots details:**

| Rank | Candidate ID | Candidate Name | Current Title | Honeypot Reason |
| :---: | :---: | :--- | :--- | :--- |
| 4 | `CAND_0017960` | Pari Shah | Recommendation Systems Engineer | Started at sarvam ai in 2018, but company was founded in 2023 |
| 5 | `CAND_0055905` | Anika Rao | Senior Machine Learning Engineer | Started at rephrase.ai in 2018, but company was founded in 2019 |
| 8 | `CAND_0011687` | Shreya Tiwari | Senior NLP Engineer | Started at krutrim in 2018, but company was founded in 2023 |
| 9 | `CAND_0005649` | Riya Kapoor | Senior Data Scientist | Started at glance in 2018, but company was founded in 2019 |
| 51 | `CAND_0011327` | Pranav Krishnan | AI Research Engineer | Started at krutrim in 2022, but company was founded in 2023 |
| 61 | `CAND_0068932` | Anil Mukherjee | ML Engineer | Started at krutrim in 2022, but company was founded in 2023 |
| 90 | `CAND_0018701` | Advik Khanna | Junior ML Engineer | Started at krutrim in 2022, but company was founded in 2023 |
| 92 | `CAND_0018293` | Divya Joshi | Data Scientist | Started at sarvam ai in 2020, but company was founded in 2023 |

---

### File: `ndk_submission.csv`
> [!NOTE]
> **Status: PASSED** (Honeypot Rate: **1.0%** is within the allowed limit)
> - Format is valid. 0% honeypot presence. Fully compliant.

**Submissions breakdown:**
- Stated rows: `100`
- Valid candidates: `99`
- Traps/Honeypots: `1`
- Unregistered candidate IDs: `0`

**Flagged Honeypots details:**

| Rank | Candidate ID | Candidate Name | Current Title | Honeypot Reason |
| :---: | :---: | :--- | :--- | :--- |
| 88 | `CAND_0006567` | Aditya Subramanian | Senior AI Engineer | Started at glance in 2018, but company was founded in 2019 |

---

### File: `rohit_candidates.csv`
> [!WARNING]
> **Status: DISQUALIFIED** (Honeypot Rate: **12.0%** exceeds the 10.0% limit)
> - Total honeypots flagged: 12 in top 100.

**Submissions breakdown:**
- Stated rows: `100`
- Valid candidates: `88`
- Traps/Honeypots: `12`
- Unregistered candidate IDs: `0`

**Flagged Honeypots details:**

| Rank | Candidate ID | Candidate Name | Current Title | Honeypot Reason |
| :---: | :---: | :--- | :--- | :--- |
| 5 | `CAND_0011687` | Shreya Tiwari | Senior NLP Engineer | Started at krutrim in 2018, but company was founded in 2023 |
| 29 | `CAND_0033861` | Kabir Kapoor | Senior NLP Engineer | Started at sarvam ai in 2020, but company was founded in 2023 |
| 30 | `CAND_0011432` | Deepak Trivedi | Senior Data Scientist | Started at krutrim in 2020, but company was founded in 2023 |
| 38 | `CAND_0005649` | Riya Kapoor | Senior Data Scientist | Started at glance in 2018, but company was founded in 2019 |
| 39 | `CAND_0024878` | Aanya Shetty | AI Specialist | Started at krutrim in 2020, but company was founded in 2023 |
| 47 | `CAND_0015528` | Aisha Reddy | Applied ML Engineer | Started at krutrim in 2022, but company was founded in 2023 |
| 48 | `CAND_0017960` | Pari Shah | Recommendation Systems Engineer | Started at sarvam ai in 2018, but company was founded in 2023 |
| 53 | `CAND_0006567` | Aditya Subramanian | Senior AI Engineer | Started at glance in 2018, but company was founded in 2019 |
| 63 | `CAND_0005269` | Nisha Bose | Senior Software Engineer (ML) | Started at sarvam ai in 2022, but company was founded in 2023 |
| 76 | `CAND_0015097` | Om Trivedi | Senior Software Engineer (ML) | Started at krutrim in 2020, but company was founded in 2023 |
| 91 | `CAND_0065878` | Suresh Kapoor | Senior Data Scientist | Started at rephrase.ai in 2018, but company was founded in 2019 |
| 96 | `CAND_0049978` | Kabir Arora | Senior Software Engineer (ML) | Started at sarvam ai in 2022, but company was founded in 2023 |

---

### File: `submission_valid.csv`
> [!NOTE]
> **Status: PASSED** (Honeypot Rate: **0.0%** is within the allowed limit)
> - Format is valid. 0% honeypot presence. Fully compliant.

**Submissions breakdown:**
- Stated rows: `100`
- Valid candidates: `100`
- Traps/Honeypots: `0`
- Unregistered candidate IDs: `0`

🎉 **No honeypot profiles found in this submission.**

---