# Get absolute paths of current directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!$ScriptDir) { $ScriptDir = Get-Location }

$WorkspaceDir = (Get-Item $ScriptDir).Parent.FullName
$DataDir = Join-Path $WorkspaceDir "Redrobsdataset"
$OutputDir = Join-Path $ScriptDir "output"

# Ensure output folder exists on host
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Building Docker image 'redrob-new-validator'..." -ForegroundColor Green
docker build -t redrob-new-validator $ScriptDir

Write-Host "Running Docker container..." -ForegroundColor Green
docker run --rm `
  -v "${DataDir}:/app/data" `
  -v "${OutputDir}:/app/output" `
  redrob-new-validator

Write-Host "Execution finished. Outputs are saved in '$OutputDir'." -ForegroundColor Green
