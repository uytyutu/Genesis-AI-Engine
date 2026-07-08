# Create Desktop shortcut — Virtus Core / Vector icon from rebuilt exe
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "dist\Genesis.exe"
$ExeLegacy = Join-Path $Root "dist\Genesis Launcher.exe"
$Bat = Join-Path $Root "launcher\StartGenesis.bat"
$Ico = Join-Path $Root "launcher\assets\virtus.ico"
if (-not (Test-Path $Ico)) {
  $Ico = Join-Path $Root "launcher\assets\genesis.ico"
}
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Virtus Core.lnk"
$ShortcutLegacy = Join-Path $Desktop "Genesis.lnk"

if (Test-Path $Exe) {
    $Target = $Exe
} elseif (Test-Path $ExeLegacy) {
    $Target = $ExeLegacy
} elseif (Test-Path $Bat) {
    $Target = $Bat
} else {
    Write-Error "Build launcher first: launcher\build.ps1"
}

$Wsh = New-Object -ComObject WScript.Shell
foreach ($path in @($ShortcutPath, $ShortcutLegacy)) {
  if (Test-Path $path) { Remove-Item $path -Force }
}
$Shortcut = $Wsh.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = $Root
$Shortcut.Description = "Virtus Core — Vector Intelligent AI Assistant"

# Prefer icon embedded in exe (always matches last PyInstaller build)
if (Test-Path $Exe) {
    $Shortcut.IconLocation = "$Exe,0"
} elseif (Test-Path $Ico) {
    $Shortcut.IconLocation = "$Ico,0"
}

$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"
if (Test-Path $Exe) {
    Write-Host "Icon source: $Exe (embedded Virtus Core mark)"
} elseif (Test-Path $Ico) {
    Write-Host "Icon source: $Ico"
}
