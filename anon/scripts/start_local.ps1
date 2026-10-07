# Start ANON locally on :3100 (webpack — Turbopack hangs on this repo).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$conns = Get-NetTCPConnection -LocalPort 3100 -ErrorAction SilentlyContinue |
  Where-Object { $_.State -eq "Listen" }
foreach ($c in $conns) {
  try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
}

if (-not (Test-Path "node_modules\next")) {
  npm ci
}

Write-Host "Starting ANON → http://localhost:3100"
npm run dev
