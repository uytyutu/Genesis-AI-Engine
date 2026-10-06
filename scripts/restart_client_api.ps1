# Restart Virtus Core client API + Cloudflare quick tunnel (Windows).
# Keeps customer login working while OVH is down.
$ErrorActionPreference = "Continue"
$root = "d:\Games\Genesis-AI-Engine"
$backend = Join-Path $root "dashboard\backend"
$runtime = Join-Path $root ".runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

# Stop previous listeners on 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -match 'cloudflared' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2

# Load deploy/.env without printing values
$envFile = Join-Path $root "deploy\.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $i = $_.IndexOf('=')
    $k = $_.Substring(0, $i).Trim()
    $v = $_.Substring($i + 1).Trim()
    if ($k) { Set-Item -Path "Env:$k" -Value $v }
  }
}

$env:PYTHONPATH = $root
$env:HOST = "127.0.0.1"
$env:PORT = "8000"
$env:GENESIS_ENV = "production"
Remove-Item Env:GENESIS_MEMORY_DIR -ErrorAction SilentlyContinue
$env:GENESIS_CORS_ORIGINS = "https://genesis-ai-engine.vercel.app,https://genesis-ai-engine.com,http://localhost:3000"
$env:GENESIS_PUBLIC_URL = "https://genesis-ai-engine.vercel.app"

$apiLog = Join-Path $runtime "api_boot.log"
$apiErr = Join-Path $runtime "api_boot.err"
Remove-Item $apiLog, $apiErr -ErrorAction SilentlyContinue

$api = Start-Process -FilePath "py" -ArgumentList "-3.12","-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
  -WorkingDirectory $backend -RedirectStandardOutput $apiLog -RedirectStandardError $apiErr -PassThru -WindowStyle Hidden
"API_PID=$($api.Id)"

for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  try {
    $h = Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3
    if ($h.StatusCode -eq 200) { "API_OK $($h.Content)"; break }
  } catch {}
  if ($i -eq 29) { "API_FAIL"; Get-Content $apiErr -Tail 40 -ErrorAction SilentlyContinue; exit 1 }
}

$cfLog = Join-Path $runtime "cf.log"
$cfErr = Join-Path $runtime "cf.err"
Remove-Item $cfLog, $cfErr -ErrorAction SilentlyContinue
$cf = Start-Process -FilePath "D:\Progs\node.exe" -ArgumentList "D:\Progs\node_modules\npm\bin\npx-cli.js","--yes","cloudflared","tunnel","--url","http://127.0.0.1:8000" `
  -RedirectStandardOutput $cfLog -RedirectStandardError $cfErr -PassThru -WindowStyle Hidden
"CF_PID=$($cf.Id)"

$tunnel = $null
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 2
  $m = Select-String -Path $cfErr, $cfLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue |
    Select-Object -Last 1
  if ($m -and $m.Matches.Count -gt 0) {
    $tunnel = $m.Matches[0].Value
    break
  }
}

if (-not $tunnel) { "TUNNEL_FAIL"; Get-Content $cfErr -Tail 20; exit 2 }
"TUNNEL=$tunnel"
Set-Content -Path (Join-Path $runtime "client_api_tunnel.txt") -Value $tunnel -Encoding utf8
try {
  $th = Invoke-WebRequest "$tunnel/health" -UseBasicParsing -TimeoutSec 20
  "TUNNEL_HEALTH=$($th.StatusCode) $($th.Content)"
} catch { "TUNNEL_HEALTH_FAIL $($_.Exception.Message)" }
