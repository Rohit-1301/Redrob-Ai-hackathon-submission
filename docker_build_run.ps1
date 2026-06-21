# Get absolute paths of current directories
$WorkspaceDir = Get-Location
$DataDir = Join-Path $WorkspaceDir "Redrobsdataset"
$OutputDir = Join-Path $WorkspaceDir "outputs"

Write-Host "Building Docker image 'redrob-validator'..." -ForegroundColor Green
docker build -t redrob-validator .

Write-Host "Running Docker container..." -ForegroundColor Green
docker run --rm `
  -v "${DataDir}:/app/data" `
  -v "${OutputDir}:/app/outputs" `
  redrob-validator

Write-Host "Execution finished. Outputs are saved in '$OutputDir'." -ForegroundColor Green
