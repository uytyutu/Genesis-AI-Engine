# Build Genesis Launcher.exe (run once from project root)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Installing launcher dependencies..."
py -m pip install -r launcher\requirements.txt -q

Write-Host "Building application icon (brand master SVG)..."
py "$Root\scripts\generate_brand_assets.py"

Write-Host "Building Genesis Launcher.exe..."
foreach ($stale in @("Genesis Launcher.exe", "Genesis-test.exe")) {
  $p = Join-Path $Root "dist\$stale"
  if (Test-Path $p) {
    Remove-Item $p -Force
    Write-Host "Removed stale: $stale"
  }
}
$Icon = Join-Path $Root "launcher\assets\genesis.ico"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
@(
  '"""Build stamp shown in Launcher — CEO can verify which exe is running."""',
  '',
  'from __future__ import annotations',
  '',
  'import sys',
  'from pathlib import Path',
  '',
  "BUILD_STAMP = '$stamp UTC'",
  '',
  'if getattr(sys, "frozen", False):',
  '    _exe = Path(sys.executable).resolve()',
  '    BUILD_ID = f"build {BUILD_STAMP} · {_exe.name}"',
  'else:',
  '    BUILD_ID = f"dev {BUILD_STAMP} · launcher/app.py"',
  ''
) | Set-Content -Encoding UTF8 "$Root\launcher\build_info.py"
$CommonArgs = @(
  "--noconfirm",
  "--onefile",
  "--windowed",
  "--name", "Genesis",
  "--paths", "$Root",
  "--hidden-import", "customtkinter",
  "--collect-all", "customtkinter",
  "$Root\launcher\app.py"
)
if (Test-Path $Icon) {
  Write-Host "Using icon: $Icon"
  py -m PyInstaller @CommonArgs --icon $Icon
} else {
  py -m PyInstaller @CommonArgs
}

Write-Host ""
Write-Host "Updating desktop shortcut and icon cache..."
py "$Root\launcher\ensure_identity.py"

Write-Host ""
Write-Host "Done: $Root\dist\Genesis.exe"
Write-Host "Desktop shortcut updated automatically."
