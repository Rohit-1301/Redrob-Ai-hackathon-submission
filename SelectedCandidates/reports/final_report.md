# Candidate Discovery & Ranking Final Report

This report presents the analysis and final ranking outputs of the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

## 1. Executive Summary
The candidate evaluation pipeline processed the eligible preprocessed candidate pools (VALID, REVIEW, and WEAK classifications). Using a custom multi-factor hybrid scoring model (Semantic, Career, Skills, Behavior, Quality, and Product-centric metrics), the system evaluated the candidates against the Senior AI Engineer (Ranking & Retrieval) Job Description. Exactly 100 top profiles were selected and ranked.

## 2. Ranking Statistics
- **Top candidate score**: 0.8246
- **100th candidate score**: 0.7655
- **Mean score**: 0.7792
- **Category Breakdown in Top 100**:
  - **VALID**: 100 candidates
  - **REVIEW**: 0 candidates
  - **WEAK**: 0 candidates

## 3. Top 10 Ranked Candidates

| Rank | Candidate ID | Score | Category | Experience | Current Title | Current Company | Matching Skills |
|------|--------------|-------|----------|------------|---------------|-----------------|-----------------|
| 1 | CAND_0071974 | 0.8246 | VALID | 7.8y | Senior AI Engineer | Netflix | 19 skills |
| 2 | CAND_0046064 | 0.8192 | VALID | 8.9y | Senior NLP Engineer | Salesforce | 16 skills |
| 3 | CAND_0041669 | 0.8091 | VALID | 8.0y | Recommendation Systems Engineer | CRED | 20 skills |
| 4 | CAND_0080766 | 0.8066 | VALID | 8.8y | Staff Machine Learning Engineer | Salesforce | 21 skills |
| 5 | CAND_0011687 | 0.8064 | VALID | 7.8y | Senior NLP Engineer | Niramai | 13 skills |
| 6 | CAND_0077337 | 0.8018 | VALID | 7.0y | Staff Machine Learning Engineer | Paytm | 20 skills |
| 7 | CAND_0088025 | 0.8003 | VALID | 8.6y | Staff Machine Learning Engineer | Yellow.ai | 19 skills |
| 8 | CAND_0079387 | 0.7991 | VALID | 6.9y | AI Engineer | Microsoft | 20 skills |
| 9 | CAND_0083307 | 0.7972 | VALID | 7.8y | Search Engineer | CRED | 18 skills |
| 10 | CAND_0061257 | 0.7931 | VALID | 8.0y | Staff Machine Learning Engineer | LinkedIn | 16 skills |

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
