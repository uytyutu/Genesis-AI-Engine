# Restart Genesis public site (fixes 500 / hang after build deleted .next while dev was running)
$frontend = Join-Path $PSScriptRoot "..\dashboard\frontend" | Resolve-Path

foreach ($port in @(3000, 3001)) {
    Write-Host "Stopping anything on port $port..."
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

Write-Host "Cleaning .next cache..."
Remove-Item -Recurse -Force (Join-Path $frontend ".next") -ErrorAction SilentlyContinue

Write-Host "Starting frontend on http://localhost:3000/site ..."
Set-Location $frontend
npm run dev
