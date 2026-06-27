import os
import sys
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

# Page Configuration
st.set_page_config(
    page_title="Redrob Candidate Discovery & Ranking Hub",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Harmonious Palettes)
st.markdown("""
<style>
    .main {
        background-color: #0F172A;
        color: #E2E8F0;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #F8FAFC;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    .candidate-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.2s ease;
    }
    .candidate-card:hover {
        border-color: #3B82F6;
        background: rgba(30, 41, 59, 0.8);
    }
</style>
""", unsafe_allow_html=True)

# Relative Paths to Outputs
csv_path = os.path.join(project_root, "SelectedCandidates/outputs/top_100_candidates.csv")
explanations_path = os.path.join(project_root, "SelectedCandidates/outputs/top_100_explanations.json")
reports_dir = os.path.join(project_root, "SelectedCandidates/reports")
report_path = os.path.join(reports_dir, "final_report.md")

st.title("🎯 Redrob Candidate Discovery & Ranking Hub")
st.subheader("Senior AI Engineer (Ranking & Retrieval) Talent Pipeline")

# Check if outputs exist
files_exist = os.path.exists(csv_path) and os.path.exists(explanations_path)

if not files_exist:
    st.warning("⚠️ Ranking pipeline outputs not found. Please run the pipeline script `run_pipeline.py` first to generate the outputs.")
    if st.button("🚀 Run Ranking Pipeline"):
        with st.spinner("Executing candidate ranking system (FAISS Indexing + Hybrid Scoring)..."):
            try:
                # Run the ranking script
                import subprocess
                run_script = os.path.join(project_root, "SelectedCandidates/run_pipeline.py")
                res = subprocess.run([sys.executable, run_script], capture_output=True, text=True, check=True)
                st.success("✅ Ranking pipeline ran successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error running pipeline: {e}")
else:
    # Sidebar
    st.sidebar.image("https://redrob.io/static/media/logo.20cfbf60.svg", width=120)
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard Overview", "Candidate Deep-Dive", "Interactive Charts", "System Report"])
    
    # Load Data
    df = pd.read_csv(csv_path)
    with open(explanations_path, 'r', encoding='utf-8') as f:
        explanations = json.load(f)
        
    # Create dictionary lookup for detailed explanations
    exp_dict = {item["candidate_id"]: item for item in explanations}
    
    if page == "Dashboard Overview":
        st.markdown("### 📊 Pipeline Insights")
        
        # Metric Grid
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Candidates Evaluated", "~24,800")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Top Candidate Score", f"{df['score'].max():.4f}")
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Cut-off Score (Rank 100)", f"{df['score'].min():.4f}")
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            cats = [item["category"] for item in explanations]
            st.metric("Valid Category Share", f"{(cats.count('VALID')/len(cats))*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Top 10 Table
        st.markdown("### 🏆 Top 10 Discovery Candidates")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Download Panel
        st.markdown("### 📥 Export Submission Artifacts")
        col_c, col_j = st.columns(2)
        with col_c:
            with open(csv_path, 'rb') as f:
                st.download_button(
                    label="Download Submission CSV",
                    data=f,
                    file_name="top_100_candidates.csv",
                    mime="text/csv"
                )
        with col_j:
            with open(explanations_path, 'rb') as f:
                st.download_button(
                    label="Download Detailed Explanations JSON",
                    data=f,
                    file_name="top_100_explanations.json",
                    mime="application/json"
                )
                
    elif page == "Candidate Deep-Dive":
        st.markdown("### 🔍 Candidate Verification & Explainability")
        
        selected_id = st.selectbox("Select a Candidate to analyze:", df["candidate_id"].tolist())
        
        if selected_id in exp_dict:
            item = exp_dict[selected_id]
            highlights = item.get("profile_highlights", {})
            breakdown = item.get("scoring_breakdown", {})
            strengths = item.get("strengths", {})
            weaknesses = item.get("weaknesses", {})
            
            col_l, col_r = st.columns([1, 1])
            
            with col_l:
                st.markdown(f"#### Profile: {highlights.get('name', 'Anonymized Candidate')}")
                st.write(f"**Headline:** {highlights.get('headline', 'N/A')}")
                st.write(f"**Current Role:** {highlights.get('current_title', 'N/A')} at {highlights.get('current_company', 'N/A')}")
                st.write(f"**Location:** {highlights.get('location', 'N/A')}")
                st.write(f"**Work Experience:** {strengths.get('experience_years', 0.0)} years")
                
                # Strengths & Weaknesses
                st.markdown("##### 🌟 Key Highlights")
                st.info(f"✔️ **Required Skills Matched:** {', '.join(strengths.get('matched_required_skills', [])) or 'None'}")
                st.info(f"✔️ **Preferred Skills Matched:** {', '.join(strengths.get('matched_preferred_skills', [])) or 'None'}")
                st.info(f"⚡ **Recruiter Response Rate:** {strengths.get('recruiter_response_rate', 0.0)*100:.1f}%")
                
                if weaknesses.get("consulting_history"):
                    st.warning("⚠️ **Consulting Career Flag:** Candidate has history at an IT consulting firm.")
                    
            with col_r:
                st.markdown("#### Hybrid Score Breakdown")
                
                score_data = {
                    "Metric": [
                        "Semantic Fit (40%)", 
                        "Career Match (20%)", 
                        "Skill Alignment (15%)", 
                        "Behavioral Score (10%)", 
                        "Quality Verification (10%)", 
                        "Product Company Bonus (5%)"
                    ],
                    "Score (0.0 - 1.0)": [
                        breakdown.get("semantic_score_40pct", 0.0),
                        breakdown.get("career_score_20pct", 0.0),
                        breakdown.get("skill_score_15pct", 0.0),
                        breakdown.get("behavior_score_10pct", 0.0),
                        breakdown.get("quality_score_10pct", 0.0),
                        breakdown.get("product_company_score_5pct", 0.0)
                    ]
                }
                score_df = pd.DataFrame(score_data)
                
                # Chart
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0F172A')
                ax.set_facecolor('#1E293B')
                
                bars = ax.barh(score_df["Metric"], score_df["Score (0.0 - 1.0)"], color='#3B82F6', edgecolor='white', height=0.5)
                ax.set_xlim(0, 1.05)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#E2E8F0')
                ax.spines['bottom'].set_color('#E2E8F0')
                ax.tick_params(colors='#E2E8F0')
                ax.xaxis.grid(True, linestyle='--', alpha=0.3)
                
                # Add text labels on the bars
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, f"{width:.2f}", 
                            va='center', ha='left', color='#E2E8F0', fontweight='bold')
                
                st.pyplot(fig)
                
                st.markdown(f"**Raw Combined Score:** {item['raw_hybrid_score']:.4f}")
                st.markdown(f"**Multiplier Applied:** x{item['multiplier']:.2f} ({item['category']})")
                st.markdown(f"**Final Ranking Score:** `{item['final_score']:.4f}`")
                
    elif page == "Interactive Charts":
        st.markdown("### 📈 Visualizing the Talent Pool")
        
        # Load the pre-computed stats of all 100K candidates
        stats_path = os.path.join(project_root, "SelectedCandidates/outputs/all_candidates_stats.json")
        if os.path.exists(stats_path):
            with open(stats_path, "r", encoding="utf-8") as f:
                all_stats = json.load(f)
                
            st.markdown("#### 📊 Analysis of All Candidates (100,000 Pool)")
            
            # Row 1: Status Distribution and Experience Distribution
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown("##### Candidate Classification Breakdown")
                status_df = pd.DataFrame(
                    list(all_stats["status_distribution"].items()), 
                    columns=["Status", "Count"]
                ).set_index("Status")
                st.bar_chart(status_df)
                
            with col_s2:
                st.markdown("##### Years of Experience Distribution")
                exp_df = pd.DataFrame(all_stats["experience_distribution"])
                exp_df = exp_df.rename(columns={"experience_years": "Years of Experience", "count": "Candidate Count"}).set_index("Years of Experience")
                st.bar_chart(exp_df)
                
            # Row 2: Top Skills and Top Locations
            col_s3, col_s4 = st.columns(2)
            with col_s3:
                st.markdown("##### Top 15 Most Common Skills")
                skills_df = pd.DataFrame(all_stats["top_skills"][:15])
                skills_df = skills_df.rename(columns={"skill": "Skill", "count": "Frequency"}).set_index("Skill")
                st.bar_chart(skills_df)
                
            with col_s4:
                st.markdown("##### Top 15 Candidate Locations")
                loc_df = pd.DataFrame(all_stats["top_locations"][:15])
                loc_df = loc_df.rename(columns={"location": "Location", "count": "Frequency"}).set_index("Location")
                st.bar_chart(loc_df)
                
            # Row 3: Common Companies worked at
            st.markdown("##### Top 15 Most Common Companies Candidates Have Worked For")
            comp_df = pd.DataFrame(all_stats["top_companies"][:15])
            comp_df = comp_df.rename(columns={"company": "Company", "count": "Frequency"}).set_index("Company")
            st.bar_chart(comp_df, use_container_width=True)
            
        else:
            st.warning("⚠️ All candidates statistics file not found. Showing top 100 distributions instead.")
            
        st.markdown("---")
        st.markdown("#### 🏆 Top 100 Selected Candidate Distributions")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            if os.path.exists(os.path.join(reports_dir, "score_distribution.png")):
                st.image(os.path.join(reports_dir, "score_distribution.png"), caption="Score Distribution Profile", use_container_width=True)
            if os.path.exists(os.path.join(reports_dir, "experience_distribution.png")):
                st.image(os.path.join(reports_dir, "experience_distribution.png"), caption="Candidate Experience Range", use_container_width=True)
            
        with col_c2:
            if os.path.exists(os.path.join(reports_dir, "category_distribution.png")):
                st.image(os.path.join(reports_dir, "category_distribution.png"), caption="Eligible Category Splits", use_container_width=True)
            if os.path.exists(os.path.join(reports_dir, "skill_coverage.png")):
                st.image(os.path.join(reports_dir, "skill_coverage.png"), caption="Skills Coverage Spectrum", use_container_width=True)
            
    elif page == "System Report":
        st.markdown("### 📄 Pipeline Execution & Methodology")
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                st.markdown(f.read())
        else:
            st.error("Report markdown file not found.")
