# Keep Genesis site + API running (idempotent — safe to run anytime)
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root "dashboard\backend"
$frontend = Join-Path $root "dashboard\frontend"

function Test-PortHttp($port, $path) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$port$path" -UseBasicParsing -TimeoutSec 8
        return $r.StatusCode -eq 200
    } catch { return $false }
}

function Stop-Port($port) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$apiOk = Test-PortHttp 8000 "/api/public/genesis-ai/status"
$siteOk = Test-PortHttp 3000 "/site"

if (-not $apiOk) {
    Write-Host "Starting backend on :8000..."
    Stop-Port 8000
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    ) -WindowStyle Minimized
    Start-Sleep -Seconds 4
}

if (-not $siteOk) {
    Write-Host "Starting frontend on :3000..."
    Stop-Port 3000
    Stop-Port 3001
    Remove-Item -Recurse -Force (Join-Path $frontend ".next") -ErrorAction SilentlyContinue
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$frontend'; npm run dev"
    ) -WindowStyle Minimized
    Start-Sleep -Seconds 8
}

& (Join-Path $PSScriptRoot "check-genesis-health.ps1")
