# Build Genesis Launcher.exe (run once from project root)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Installing launcher dependencies..."
py -m pip install -r launcher\requirements.txt -q

Write-Host "Building application icon..."
py "$Root\launcher\assets\build_icon.py"

Write-Host "Building Genesis Launcher.exe..."
$Icon = Join-Path $Root "launcher\assets\genesis.ico"
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
Write-Host "Done: $Root\dist\Genesis.exe"
Write-Host "Run launcher\install_shortcut.ps1 to create Desktop shortcut."
