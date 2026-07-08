# Connect Cloud LLM to Genesis (employee cortex). Key is never printed.
param(
    [Parameter(Mandatory = $true)][string]$ApiKey,
    [string]$Model = "gpt-4o-mini",
    [ValidateSet("openai", "openrouter", "groq", "gemini")][string]$Provider = "groq"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root "dashboard\backend"
$secretsDir = Join-Path $backend "secrets"
$llmKeyFile = Join-Path $secretsDir "llm.key"
$envFile = Join-Path $backend ".env"

New-Item -ItemType Directory -Force -Path $secretsDir | Out-Null
Set-Content -Path $llmKeyFile -Value $ApiKey.Trim() -Encoding UTF8 -NoNewline
Write-Host "Saved key to dashboard/backend/secrets/llm.key"

if ($Provider -eq "openrouter") {
    $line = "GENESIS_OPENROUTER_API_KEY=$($ApiKey.Trim())"
    $modelLine = "GENESIS_OPENROUTER_MODEL=google/gemini-2.0-flash-001"
} elseif ($Provider -eq "groq") {
    $line = "GENESIS_GROQ_API_KEY=$($ApiKey.Trim())"
    $modelLine = "GENESIS_GROQ_MODEL=llama-3.3-70b-versatile"
} elseif ($Provider -eq "gemini") {
    $line = "GENESIS_GEMINI_API_KEY=$($ApiKey.Trim())"
    $modelLine = "GENESIS_GEMINI_MODEL=gemini-2.0-flash"
} else {
    $line = "GENESIS_LLM_API_KEY=$($ApiKey.Trim())"
    $modelLine = "GENESIS_LLM_MODEL=$Model"
}

$envContent = @()
if (Test-Path $envFile) { $envContent = Get-Content $envFile }
$out = @()
$doneKey = $false
$doneModel = $false
foreach ($l in $envContent) {
    if ($l -match '^GENESIS_(LLM|GROQ|GEMINI|OPENROUTER)_API_KEY=') {
        if (-not $doneKey) { $out += $line; $doneKey = $true }
        continue
    }
    if ($l -match '^GENESIS_(LLM|GROQ|GEMINI|OPENROUTER)_MODEL=') {
        if (-not $doneModel) { $out += $modelLine; $doneModel = $true }
        continue
    }
    $out += $l
}
if (-not $doneKey) { $out += ""; $out += "# Genesis LLM"; $out += $line }
if (-not $doneModel) { $out += $modelLine }
Set-Content -Path $envFile -Value ($out -join "`n") -Encoding UTF8

Write-Host "Updated $envFile"
Write-Host "Verifying via backend..."

$py = @"
import os, sys
sys.path.insert(0, r'$backend')
from app.env_loader import load_local_env
load_local_env()
from app.integration.genesis_ai_service import GenesisAIService
ok = GenesisAIService([]).llm_configured()
print('LLM_CONFIGURED=' + ('1' if ok else '0'))
"@
$result = python -c $py 2>&1
Write-Host $result

if ($result -match 'LLM_CONFIGURED=1') {
    Write-Host "Genesis cloud cortex ready. Open http://localhost:3000/site" -ForegroundColor Green
} else {
    Write-Host "Key saved but verify failed — check key validity or restart backend." -ForegroundColor Yellow
    Write-Host "Run: .\scripts\ensure-genesis-running.ps1"
}
