# Genesis health check - site + API + LLM (run before every play test)
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
$backendEnv = Join-Path $root "dashboard\backend\.env.local"

Write-Host "=== Genesis Health Check ===" -ForegroundColor Cyan

function Test-Url($url, $label) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        Write-Host "[OK] $label HTTP $($r.StatusCode)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[FAIL] $label $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$siteOk = Test-Url "http://localhost:3000/site" "Public site /site"
$apiOk = $false
$llmOk = $false

try {
    $st = Invoke-RestMethod -Uri "http://localhost:8000/api/public/genesis-ai/status" -TimeoutSec 10
    $apiOk = $true
    $llmOk = [bool]$st.llm_configured
    Write-Host "[OK] Backend API brain $($st.brain_version)" -ForegroundColor Green
    if ($llmOk) {
        Write-Host "[OK] Cloud LLM configured" -ForegroundColor Green
    } else {
        Write-Host "[WARN] No cloud employees configured - genesis-local only" -ForegroundColor Yellow
        Write-Host "       Free tier: GENESIS_GROQ_API_KEY + GENESIS_GEMINI_API_KEY" -ForegroundColor Yellow
        Write-Host "       .\scripts\connect-genesis-llm.ps1 -Provider groq -ApiKey gsk_..." -ForegroundColor Yellow
        Write-Host "       http://localhost:3000/setup" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Backend API $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "       Start: cd dashboard/backend; python -m uvicorn app.main:app --port 8000" -ForegroundColor Yellow
}

if (-not $siteOk) {
    Write-Host "       Fix site: .\scripts\restart-public-site.ps1" -ForegroundColor Yellow
}

if (Test-Path $backendEnv) {
    Write-Host "[INFO] Found $backendEnv" -ForegroundColor DarkGray
} else {
    Write-Host "[INFO] No .env.local - copy from dashboard/backend/.env.example" -ForegroundColor DarkGray
}

if ($siteOk -and $apiOk -and $llmOk) {
    Write-Host ""
    Write-Host "All green - ready for Human Review on /site" -ForegroundColor Green
    exit 0
}
if ($siteOk -and $apiOk) {
    Write-Host ""
    Write-Host "Site works but mind is limited until LLM key is set" -ForegroundColor Yellow
    exit 1
}
exit 2
