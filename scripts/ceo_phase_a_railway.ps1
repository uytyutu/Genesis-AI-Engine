# Phase A - set Groq key on Railway genesis-beta
# Usage: powershell -ExecutionPolicy Bypass -File scripts/ceo_phase_a_railway.ps1

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent

$envFile = Join-Path $repo "dashboard\backend\.env.local"
$key = $null
foreach ($line in Get-Content $envFile -Encoding UTF8) {
    if ($line -match '^GENESIS_GROQ_API_KEY=(.+)$') {
        $key = $matches[1].Trim().Trim('"').Trim("'")
        break
    }
}
if (-not $key) {
    Write-Host "ERROR: GENESIS_GROQ_API_KEY not found in $envFile"
    exit 1
}

Set-Clipboard -Value $key
Write-Host "Groq key copied to clipboard."
Write-Host ""
Write-Host "1. Open Railway -> genesis-beta -> Variables"
Write-Host "   https://railway.app/dashboard"
Write-Host "2. Add: GENESIS_GROQ_API_KEY = paste Ctrl+V"
Write-Host "3. Redeploy"
Write-Host ""

$railway = Get-Command railway -ErrorAction SilentlyContinue
if ($railway) {
    Write-Host "Railway CLI detected - attempting automatic set..."
    Push-Location $repo
    railway variables --set "GENESIS_GROQ_API_KEY=$key" --service genesis-beta
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Variable set. Waiting 90s for redeploy..."
        Start-Sleep -Seconds 90
        py scripts/prove_deploy_report.py
    }
    Pop-Location
} else {
    Write-Host "No Railway CLI - use clipboard paste in dashboard."
}
