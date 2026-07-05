# Refresh Windows icon cache after replacing genesis.ico / Genesis.exe
# Run from project root: powershell -ExecutionPolicy Bypass -File launcher\refresh_windows_icons.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Write-Host "Genesis Brand v1.0 — refreshing desktop identity..."
Write-Host ""

# 1. Rebuild shortcut (icon from dist\Genesis.exe)
& "$PSScriptRoot\install_shortcut.ps1"

# 2. Soft refresh
if (Get-Command ie4uinit.exe -ErrorAction SilentlyContinue) {
    Write-Host "Running ie4uinit -show..."
    ie4uinit.exe -show
    Start-Sleep -Seconds 2
}

# 3. Clear Explorer icon cache (Windows 10/11)
$ExplorerCache = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Explorer"
$patterns = @("iconcache*", "thumbcache_*.db", "thumbcache_*.db_tmp")

Write-Host "Clearing icon cache in $ExplorerCache ..."
foreach ($pattern in $patterns) {
    Get-ChildItem -Path $ExplorerCache -Filter $pattern -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# 4. Restart Explorer to reload icons
Write-Host "Restarting Explorer..."
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process explorer.exe

Write-Host ""
Write-Host "Done. Check desktop shortcut 'Genesis' — should show Orbit Stack (blue gradient, white stack bars)."
Write-Host ""
Write-Host "If still wrong:"
Write-Host "  Right-click Genesis.lnk -> Properties -> Change Icon -> browse to:"
Write-Host "  $Root\launcher\assets\genesis.ico"
Write-Host "  Or sign out once."
