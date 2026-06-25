import streamlit as st
import json
import pandas as pd
import sys
import os
import io

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.score_candidates import score_candidate
from src.utils.rank_candidates import rank_candidates
from src.jd.senion_ai_engineer import senior_ai_enginerr_jd

st.set_page_config(page_title="Redrob Ranker Sandbox", layout="wide")

st.title("🎯 Redrob Candidate Ranking Sandbox")
st.write("This sandbox runs the Intelligent Discovery & Ranking engine on a sample of candidates.")

# Load JD
jd = senior_ai_enginerr_jd()

# Display Job Description details
with st.expander("📄 View Job Description (Senior AI Engineer - Founding Team)"):
    st.json(jd)

st.subheader("1. Upload Candidate Sample")
uploaded_file = st.file_uploader("Upload candidates file (.jsonl or .json array, max 100 candidates)", type=["json", "jsonl"])

if uploaded_file is not None:
    # Load candidates
    candidates = []
    content = uploaded_file.getvalue().decode("utf-8")
    
    try:
        # Check if JSON array
        if content.strip().startswith("["):
            candidates = json.loads(content)
        else:
            # Assume JSONL
            for line in content.splitlines():
                if line.strip():
                    candidates.append(json.loads(line))
        
        st.success(f"Loaded {len(candidates)} candidates successfully!")
        
        if len(candidates) > 100:
            st.warning("Warning: Input sample has more than 100 candidates. Showing top 100 output.")
            candidates = candidates[:100]
            
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        candidates = []
        
    if candidates:
        st.subheader("2. Scoring & Ranking")
        if st.button("🚀 Run Ranking Engine"):
            with st.spinner("Processing candidates (Scoring + Honeypot Check)..."):
                # Run engine
                scored = score_candidate(candidates, jd)
                ranked = rank_candidates(scored)
                
                # Convert to DataFrame
                df = pd.DataFrame(ranked)
                # Assign 1-indexed ranks
                df.insert(1, "rank", range(1, len(df) + 1))
                
                st.write("### Top Ranked Candidates")
                st.dataframe(
                    df[["rank", "candidate_id", "name", "score", "reasoning"]],
                    use_container_width=True
                )
                
                # Download CSV button
                csv_buffer = io.StringIO()
                df[["candidate_id", "rank", "score", "reasoning"]].to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📥 Download Ranked CSV",
                    data=csv_buffer.getvalue(),
                    file_name="ranked_candidates_sandbox.csv",
                    mime="text/csv"
                )
                
else:
    st.info("Please upload a .jsonl or .json file to start.")
    
    # Add a button to load sample candidates
    if st.button("📂 Load sample candidates (First 50 Candidates)"):
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_candidates.json")
        if not os.path.exists(sample_path):
            sample_path = "sample_candidates.json"
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                candidates = json.load(f)
            st.success(f"Loaded {len(candidates)} sample candidates from {sample_path}.")
            
            scored = score_candidate(candidates, jd)
            ranked = rank_candidates(scored)
            df = pd.DataFrame(ranked)
            df.insert(1, "rank", range(1, len(df) + 1))
            
            st.write("### Top Ranked Candidates")
            st.dataframe(
                df[["rank", "candidate_id", "name", "score", "reasoning"]],
                use_container_width=True
            )
            
            csv_buffer = io.StringIO()
            df[["candidate_id", "rank", "score", "reasoning"]].to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Ranked CSV",
                data=csv_buffer.getvalue(),
                file_name="ranked_candidates_sandbox.csv",
                mime="text/csv"
            )
        else:
            st.error(f"Sample candidates file {sample_path} not found!")
