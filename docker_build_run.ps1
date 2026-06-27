# Get absolute paths of current directories
$WorkspaceDir = Get-Location
$DataDir = Join-Path $WorkspaceDir "Redrobsdataset"
$OutputDir = Join-Path $WorkspaceDir "outputs"

# Ensure output directory exists on host
if (!(Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Building Docker image 'redrob-validator'..." -ForegroundColor Green
docker build -t redrob-validator .

Write-Host "Running Docker container..." -ForegroundColor Green
Write-Host "Interactive Streamlit app will start at http://localhost:8501 after preprocessing completes." -ForegroundColor Yellow

docker run --rm `
  -p 8501:8501 `
  -v "${DataDir}:/app/data" `
  -v "${OutputDir}:/app/outputs" `
  redrob-validator

Write-Host "Execution finished. Outputs are saved in '$OutputDir'." -ForegroundColor Green
