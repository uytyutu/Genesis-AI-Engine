# ANON public tunnel — same pattern as Virtus API cloudflared (trycloudflare).
# Usage: pwsh anon/scripts/start_public.ps1
$ErrorActionPreference = "Stop"
$Anon = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Anon

# Ensure :3100 is up
try {
  $null = Invoke-WebRequest -Uri "http://127.0.0.1:3100/api/health" -UseBasicParsing -TimeoutSec 3
} catch {
  Write-Host "Starting ANON on :3100 ..."
  Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory $Anon -WindowStyle Minimized
  $ok = $false
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 2
    try {
      $null = Invoke-WebRequest -Uri "http://127.0.0.1:3100/api/health" -UseBasicParsing -TimeoutSec 3
      $ok = $true
      break
    } catch {}
  }
  if (-not $ok) { throw "ANON did not become healthy on :3100" }
}

$log = Join-Path $env:TEMP "anon-cloudflared.log"
$err = Join-Path $env:TEMP "anon-cloudflared.err"
Remove-Item $log, $err -ErrorAction SilentlyContinue

Write-Host "Opening Cloudflare quick tunnel → http://127.0.0.1:3100"
$p = Start-Process -FilePath "npx" -ArgumentList @(
  "--yes","cloudflared","tunnel","--url","http://127.0.0.1:3100"
) -PassThru -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden

$url = $null
for ($i = 0; $i -lt 45; $i++) {
  Start-Sleep -Seconds 2
  $blob = ""
  if (Test-Path $err) { $blob += Get-Content $err -Raw -ErrorAction SilentlyContinue }
  if (Test-Path $log) { $blob += Get-Content $log -Raw -ErrorAction SilentlyContinue }
  if ($blob -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
    $url = $Matches[0]
    break
  }
}

if (-not $url) {
  Write-Host "Tunnel log:"
  if (Test-Path $err) { Get-Content $err -Tail 40 }
  throw "Could not parse trycloudflare URL"
}

# Persist public URL for Stripe redirects / OG
$envFile = Join-Path $Anon ".env.local"
if (Test-Path $envFile) {
  $txt = Get-Content $envFile -Raw
  if ($txt -match '(?m)^ANON_PUBLIC_URL=') {
    $txt = $txt -replace '(?m)^ANON_PUBLIC_URL=.*$', "ANON_PUBLIC_URL=$url"
  } else {
    $txt = "ANON_PUBLIC_URL=$url`n" + $txt
  }
  Set-Content -Path $envFile -Value $txt -Encoding utf8
}

Write-Host ""
Write-Host "ANON public URL:  $url"
Write-Host "Mission Control:  $url/auth/login?next=/admin"
Write-Host "Local MC:         http://127.0.0.1:3100/auth/login?next=/admin"
Write-Host "Owner email:      admin@anon.app  (ANON_ADMIN_EMAIL)"
Write-Host "cloudflared pid:  $($p.Id)"
Write-Host ""
Write-Host "Restart npm run dev once if cookies/OG still use old URL."
