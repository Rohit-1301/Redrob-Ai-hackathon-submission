# Candidate Discovery & Ranking Final Report

This report presents the analysis and final ranking outputs of the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

## 1. Executive Summary
The candidate evaluation pipeline processed the eligible preprocessed candidate pools (VALID, REVIEW, and WEAK classifications). Using a custom multi-factor hybrid scoring model (Semantic, Career, Skills, Behavior, Quality, and Product-centric metrics), the system evaluated the candidates against the Senior AI Engineer (Ranking & Retrieval) Job Description. Exactly 100 top profiles were selected and ranked.

## 2. Ranking Statistics
- **Top candidate score**: 0.6818
- **100th candidate score**: 0.3482
- **Mean score**: 0.5775
- **Category Breakdown in Top 100**:
  - **VALID**: 9 candidates
  - **REVIEW**: 2 candidates
  - **WEAK**: 1 candidates

## 3. Top 10 Ranked Candidates

| Rank | Candidate ID | Score | Category | Experience | Current Title | Current Company | Matching Skills |
|------|--------------|-------|----------|------------|---------------|-----------------|-----------------|
| 1 | CAND_0000014 | 0.6818 | VALID | 8.4y | Frontend Engineer | Zomato | 13 skills |
| 2 | CAND_0000015 | 0.6816 | VALID | 5.4y | Software Engineer | Razorpay | 10 skills |
| 3 | CAND_0000038 | 0.6700 | VALID | 6.7y | Java Developer | Swiggy | 11 skills |
| 4 | CAND_0000018 | 0.6465 | VALID | 6.6y | Frontend Engineer | Acme Corp | 6 skills |
| 5 | CAND_0000044 | 0.6448 | VALID | 5.7y | Frontend Engineer | Tech Mahindra | 6 skills |
| 6 | CAND_0000025 | 0.5979 | VALID | 7.3y | Frontend Engineer | Tech Mahindra | 9 skills |
| 7 | CAND_0000043 | 0.5861 | VALID | 8.3y | Cloud Engineer | Swiggy | 17 skills |
| 8 | CAND_0000048 | 0.5775 | VALID | 9.7y | Mobile Developer | CRED | 5 skills |
| 9 | CAND_0000032 | 0.5759 | VALID | 8.1y | .NET Developer | Cognizant | 10 skills |
| 10 | CAND_0000020 | 0.4748 | REVIEW | 6.3y | Mechanical Engineer | Wipro | 7 skills |

## 4. Methodology & Weight Distribution
The final score of each candidate is calculated using the following components and weights:
- **Semantic Similarity (40% weight)**: Cosine similarity between candidate embedding (engineered from profile, headline, summary, skills, and work history) and Job Description embedding via SentenceTransformers and FAISS index search.
- **Career Match (20% weight)**: Scoring on experience match (optimal 5-9 years), job title seniority, and product-focused background.
- **Skill Alignment (15% weight)**: Overlap of candidate skills with required and preferred JD skills.
- **Behavioral Health (10% weight)**: Score computed from recruiter response rates, interview completion rates, open-to-work flag, login recency, and overall platform activity.
- **Quality & Integrity (10% weight)**: Profile validation checks from the preprocessing phase.
- **Product Company Preference (5% weight)**: Extra weight for candidates who have spent their career outside IT consulting giants.
- **Category Multipliers**: VALID candidates (1.00), REVIEW candidates (0.85), WEAK candidates (0.60).

## 5. Visualizations
The following charts have been exported to the reports folder:
1. **Score Distribution** (`score_distribution.png`): Shows the distribution of candidate raw scores vs final scores.
2. **Category Breakdown** (`category_distribution.png`): Visualizes the count of VALID vs REVIEW vs WEAK candidates in the Top 100.
3. **Experience Profile** (`experience_distribution.png`): Represents candidate work experience relative to target bounds.
4. **Skill Coverage** (`skill_coverage.png`): Shows how candidates score on skill match metrics.
