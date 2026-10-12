# RedRob AI - Streamlit Dashboard Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " RedRob AI - Candidate Discovery & Ranking Web App" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting Streamlit Dashboard on http://localhost:8501..." -ForegroundColor Green

python -m streamlit run SelectedCandidates/app/streamlit_app.py --server.port 8501
