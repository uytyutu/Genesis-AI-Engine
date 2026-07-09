# Collect Virtus Core Launcher diagnostics (run when frozen or from Cursor)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== Virtus Core Launcher Diagnostics ===" -ForegroundColor Cyan

$pyExe = $null
foreach ($candidate in @("py", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pyExe = $candidate
        break
    }
}
if (-not $pyExe) {
    Write-Host "[FAIL] Python not found" -ForegroundColor Red
    exit 1
}

$pidArg = @()
$genesis = Get-Process -Name Genesis -ErrorAction SilentlyContinue | Select-Object -First 1
if ($genesis) {
    $pidArg = @("--pid", "$($genesis.Id)")
    Write-Host "Genesis.exe pid=$($genesis.Id) Responding=$($genesis.Responding)" -ForegroundColor Yellow
} else {
    Write-Host "[WARN] Genesis.exe not running - logs and ports only" -ForegroundColor Yellow
}

& $pyExe -3.12 -m launcher.diagnostics_collect @pidArg
if ($LASTEXITCODE -ne 0) {
    & $pyExe -m launcher.diagnostics_collect @pidArg
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Send the diagnostics folder to Cursor." -ForegroundColor Green
