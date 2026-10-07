# Deploy ANON to OVH VPS (Stage 2 — IP:3100, no DNS required).
# Usage (from Windows, repo machine):
#   pwsh anon/scripts/deploy_ovh.ps1
# Requires: ssh access as ubuntu@137.74.173.134 (or set ANON_OVH_SSH)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $Root "anon\package.json"))) {
  $Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
}
$Anon = Join-Path $Root "anon"
$Ssh = if ($env:ANON_OVH_SSH) { $env:ANON_OVH_SSH } else { "ubuntu@137.74.173.134" }
$Remote = if ($env:ANON_OVH_REMOTE) { $env:ANON_OVH_REMOTE } else { "/srv/anon" }

Write-Host "ANON dir: $Anon"
Write-Host "SSH:      $Ssh"
Write-Host "Remote:   $Remote"

# Ensure remote dir
ssh $Ssh "sudo mkdir -p $Remote /srv/anon-data && sudo chown -R `$USER:`$USER $Remote /srv/anon-data"

# Sync (exclude heavy / local-only)
$excludes = @(
  "--exclude=node_modules",
  "--exclude=.next",
  "--exclude=data",
  "--exclude=.git",
  "--exclude=.env.local"
)

# Prefer rsync if present; else tar over ssh
$hasRsync = Get-Command rsync -ErrorAction SilentlyContinue
if ($hasRsync) {
  & rsync -az --delete @excludes "$Anon/" "${Ssh}:${Remote}/"
} else {
  Write-Host "rsync not found — using tar+ssh"
  $tarArgs = @("-czf", "-", "--exclude=node_modules", "--exclude=.next", "--exclude=data", "--exclude=.git", "--exclude=.env.local", "-C", $Anon, ".")
  & tar @tarArgs | ssh $Ssh "mkdir -p $Remote && tar -xzf - -C $Remote"
}

# Seed .env on server if missing
ssh $Ssh @"
set -e
cd $Remote
if [ ! -f .env ]; then
  if [ -f .env.example ]; then cp .env.example .env; fi
  # Public smoke URL = VPS IP:3100 until DNS
  sed -i 's|^ANON_PUBLIC_URL=.*|ANON_PUBLIC_URL=http://137.74.173.134:3100|' .env || true
  grep -q '^ANON_PUBLIC_URL=' .env || echo 'ANON_PUBLIC_URL=http://137.74.173.134:3100' >> .env
  grep -q '^ANON_PAYMENT_SANDBOX=' .env || echo 'ANON_PAYMENT_SANDBOX=1' >> .env
  if ! grep -q '^ANON_AUTH_SECRET=.\+' .env || grep -q 'change-me' .env; then
    SECRET=\$(openssl rand -hex 32)
    if grep -q '^ANON_AUTH_SECRET=' .env; then
      sed -i \"s|^ANON_AUTH_SECRET=.*|ANON_AUTH_SECRET=\$SECRET|\" .env
    else
      echo \"ANON_AUTH_SECRET=\$SECRET\" >> .env
    fi
  fi
fi
docker compose up -d --build
sleep 3
curl -fsS http://127.0.0.1:3100/api/health || curl -fsS http://127.0.0.1:3100/ || true
"@

Write-Host ""
Write-Host "Public smoke: http://137.74.173.134:3100"
Write-Host "Health:       http://137.74.173.134:3100/api/health"
