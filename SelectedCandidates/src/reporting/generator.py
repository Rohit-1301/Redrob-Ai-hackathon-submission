import os
import sys
import json
import logging
import matplotlib.pyplot as plt

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

logger = logging.getLogger(__name__)

def generate_reports_and_charts(pipeline_results: dict, reports_dir: str):
    """
    Generates report charts (Matplotlib) and the final report markdown file.
    """
    os.makedirs(reports_dir, exist_ok=True)
    
    top_100 = pipeline_results["top_100"]
    
    # Extract data for charts
    final_scores = [c[1]["final_score"] for c in top_100]
    raw_scores = [c[1]["raw_hybrid_score"] for c in top_100]
    categories = [c[1]["category"] for c in top_100]
    experiences = [c[1]["career_details"]["experience_years"] for c in top_100]
    
    # 1. Score Distribution Chart
    plt.figure(figsize=(8, 5))
    plt.hist(final_scores, bins=15, color='#4A90E2', edgecolor='black', alpha=0.7, label='Final Scores (with Category Multiplier)')
    plt.hist(raw_scores, bins=15, color='#50E3C2', edgecolor='black', alpha=0.5, label='Raw Hybrid Scores')
    plt.title('Top 100 Candidate Score Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Score', fontsize=12)
    plt.ylabel('Candidate Count', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    score_chart_path = os.path.join(reports_dir, "score_distribution.png")
    plt.savefig(score_chart_path, bbox_inches='tight', dpi=150)
    plt.close()
    logger.info(f"Saved score distribution chart to {score_chart_path}")
    
    # 2. Category Distribution Chart
    plt.figure(figsize=(7, 5))
    cat_counts = {"VALID": categories.count("VALID"), "REVIEW": categories.count("REVIEW"), "WEAK": categories.count("WEAK")}
    plt.bar(cat_counts.keys(), cat_counts.values(), color=['#2ECC71', '#F1C40F', '#E67E22'], edgecolor='black', alpha=0.8)
    plt.title('Top 100 Candidate Category Breakdown', fontsize=14, fontweight='bold')
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Candidate Count', fontsize=12)
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    cat_chart_path = os.path.join(reports_dir, "category_distribution.png")
    plt.savefig(cat_chart_path, bbox_inches='tight', dpi=150)
    plt.close()
    logger.info(f"Saved category distribution chart to {cat_chart_path}")
    
    # 3. Experience Distribution Chart
    plt.figure(figsize=(8, 5))
    plt.hist(experiences, bins=10, color='#9B59B6', edgecolor='black', alpha=0.7)
    plt.axvline(5.0, color='red', linestyle='--', label='Min Preferred Exp (5y)')
    plt.axvline(9.0, color='red', linestyle='--', label='Max Preferred Exp (9y)')
    plt.title('Top 100 Candidate Experience Years', fontsize=14, fontweight='bold')
    plt.xlabel('Years of Experience', fontsize=12)
    plt.ylabel('Candidate Count', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    exp_chart_path = os.path.join(reports_dir, "experience_distribution.png")
    plt.savefig(exp_chart_path, bbox_inches='tight', dpi=150)
    plt.close()
    logger.info(f"Saved experience distribution chart to {exp_chart_path}")

    # 4. Skills Match Rates
    plt.figure(figsize=(8, 5))
    skill_scores = [c[1]["skill_score"] for c in top_100]
    plt.hist(skill_scores, bins=10, color='#F39C12', edgecolor='black', alpha=0.7)
    plt.title('Top 100 Skill Similarity Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Skill Match Score (0.0 - 1.0)', fontsize=12)
    plt.ylabel('Candidate Count', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    skills_chart_path = os.path.join(reports_dir, "skill_coverage.png")
    plt.savefig(skills_chart_path, bbox_inches='tight', dpi=150)
    plt.close()
    logger.info(f"Saved skills coverage chart to {skills_chart_path}")

    # 5. Generate final_report.md
    report_path = os.path.join(reports_dir, "final_report.md")
    logger.info(f"Writing final report markdown to {report_path}")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Candidate Discovery & Ranking Final Report\n\n")
        f.write("This report presents the analysis and final ranking outputs of the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.\n\n")
        
        f.write("## 1. Executive Summary\n")
        f.write("The candidate evaluation pipeline processed the eligible preprocessed candidate pools (VALID, REVIEW, and WEAK classifications). ")
        f.write("Using a custom multi-factor hybrid scoring model (Semantic, Career, Skills, Behavior, Quality, and Product-centric metrics), ")
        f.write("the system evaluated the candidates against the Senior AI Engineer (Ranking & Retrieval) Job Description. ")
        f.write("Exactly 100 top profiles were selected and ranked.\n\n")
        
        f.write("## 2. Ranking Statistics\n")
        f.write(f"- **Top candidate score**: {final_scores[0]:.4f}\n")
        f.write(f"- **100th candidate score**: {final_scores[-1]:.4f}\n")
        f.write(f"- **Mean score**: {sum(final_scores)/len(final_scores):.4f}\n")
        f.write("- **Category Breakdown in Top 100**:\n")
        for cat, cnt in cat_counts.items():
            f.write(f"  - **{cat}**: {cnt} candidates\n")
        f.write("\n")
        
        f.write("## 3. Top 10 Ranked Candidates\n\n")
        f.write("| Rank | Candidate ID | Score | Category | Experience | Current Title | Current Company | Matching Skills |\n")
        f.write("|------|--------------|-------|----------|------------|---------------|-----------------|-----------------|\n")
        for i in range(10):
            cand, info = top_100[i]
            skills_count = info["skill_details"]["total_skills"]
            f.write(
                f"| {i+1} | {info['candidate_id']} | {info['final_score']:.4f} | {info['category']} | "
                f"{info['career_details']['experience_years']:.1f}y | {info['career_details']['current_title']} | "
                f"{info['career_details']['current_company']} | {skills_count} skills |\n"
            )
        f.write("\n")
        
        f.write("## 4. Methodology & Weight Distribution\n")
        f.write("The final score of each candidate is calculated using the following components and weights:\n")
        f.write("- **Semantic Similarity (40% weight)**: Cosine similarity between candidate embedding (engineered from profile, headline, summary, skills, and work history) and Job Description embedding via SentenceTransformers and FAISS index search.\n")
        f.write("- **Career Match (20% weight)**: Scoring on experience match (optimal 5-9 years), job title seniority, and product-focused background.\n")
        f.write("- **Skill Alignment (15% weight)**: Overlap of candidate skills with required and preferred JD skills.\n")
        f.write("- **Behavioral Health (10% weight)**: Score computed from recruiter response rates, interview completion rates, open-to-work flag, login recency, and overall platform activity.\n")
        f.write("- **Quality & Integrity (10% weight)**: Profile validation checks from the preprocessing phase.\n")
        f.write("- **Product Company Preference (5% weight)**: Extra weight for candidates who have spent their career outside IT consulting giants.\n")
        f.write("- **Category Multipliers**: VALID candidates (1.00), REVIEW candidates (0.85), WEAK candidates (0.60).\n\n")
        
        f.write("## 5. Visualizations\n")
        f.write("The following charts have been exported to the reports folder:\n")
        f.write("1. **Score Distribution** (`score_distribution.png`): Shows the distribution of candidate raw scores vs final scores.\n")
        f.write("2. **Category Breakdown** (`category_distribution.png`): Visualizes the count of VALID vs REVIEW vs WEAK candidates in the Top 100.\n")
        f.write("3. **Experience Profile** (`experience_distribution.png`): Represents candidate work experience relative to target bounds.\n")
        f.write("4. **Skill Coverage** (`skill_coverage.png`): Shows how candidates score on skill match metrics.\n")
        
    logger.info("Report generation complete.")
