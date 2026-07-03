# Create Desktop shortcut "Genesis"
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "dist\Genesis.exe"
$ExeLegacy = Join-Path $Root "dist\Genesis Launcher.exe"
$Bat = Join-Path $Root "launcher\StartGenesis.bat"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Genesis.lnk"

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
$Shortcut = $Wsh.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = $Root
$Shortcut.Description = "Genesis ABOS launcher"
$Icon = Join-Path $Root "launcher\assets\genesis.ico"
if (Test-Path $Icon) {
    $Shortcut.IconLocation = "$Icon,0"
}
$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"
