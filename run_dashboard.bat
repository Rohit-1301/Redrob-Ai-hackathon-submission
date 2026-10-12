@echo off
echo ========================================================
echo  RedRob AI - Candidate Discovery & Ranking Web App
echo ========================================================
echo Starting Streamlit Dashboard on http://localhost:8501...
python -m streamlit run SelectedCandidates/app/streamlit_app.py --server.port 8501
pause
