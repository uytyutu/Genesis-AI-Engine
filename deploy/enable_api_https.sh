#!/usr/bin/env bash
# Enable HTTPS for public Farm API on OVH after DNS A → this host.
# Usage (on VPS): sudo bash deploy/enable_api_https.sh
# Default domain matches live product (Cloudflare → beta.genesis-ai-engine.com family).
set -euo pipefail

DOMAIN="${DOMAIN:-api.genesis-ai-engine.com}"
OVH_IP="${OVH_IP:-137.74.173.134}"
EMAIL="${CERTBOT_EMAIL:-hello@genesis-ai-engine.com}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY="$ROOT/deploy"
NGINX_CONF="$DEPLOY/nginx.conf"
export DOMAIN

echo "==> Checking DNS for $DOMAIN"
resolved="$(getent ahostsv4 "$DOMAIN" | awk '{print $1}' | head -n1 || true)"
echo "    resolved=$resolved expected=$OVH_IP"
if [[ "$resolved" != "$OVH_IP" ]]; then
  echo "FAIL: DNS not pointing at OVH yet."
  echo "Cloudflare → genesis-ai-engine.com → DNS → A name=api → $OVH_IP (DNS only / grey cloud)"
  exit 1
fi

echo "==> Issuing Let's Encrypt cert (webroot)"
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive \
  --keep-until-expiring

echo "==> Writing HTTPS nginx server block for $DOMAIN"
python3 - <<'PY'
import os
from pathlib import Path

domain = os.environ["DOMAIN"]
p = Path("/home/ubuntu/Genesis-AI-Engine/deploy/nginx.conf")
text = p.read_text(encoding="utf-8")
# Drop any previous HTTPS live/comment block markers
for marker in (
    "# --- HTTPS for api.virtuscore.com",
    "# --- HTTPS for api.genesis-ai-engine.com",
    f"# --- HTTPS for {domain}",
):
    idx = text.find(marker)
    if idx >= 0:
        text = text[:idx].rstrip() + "\n"
        break

live = f'''
# --- HTTPS for {domain} (LIVE) ---
server {{
    listen 443 ssl http2;
    server_name {domain};

    ssl_certificate     /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;

    client_max_body_size 50m;
    proxy_connect_timeout 60s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    location /health {{
        set $genesis_upstream http://genesis:8000;
        proxy_pass $genesis_upstream/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }}

    location /status {{
        set $genesis_upstream http://genesis:8000;
        proxy_pass $genesis_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /api/ {{
        set $genesis_upstream http://genesis:8000;
        proxy_pass $genesis_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
    }}

    location /webhooks/ {{
        set $genesis_upstream http://genesis:8000;
        proxy_pass $genesis_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location / {{
        return 404;
    }}
}}
'''
text = text.rstrip() + "\n" + live
# Ensure HTTP server_name includes domain
if domain not in text.split("server {", 1)[-1][:400]:
    text = text.replace(
        "server_name api.genesis-ai-engine.com api.virtuscore.com _;",
        f"server_name {domain} api.genesis-ai-engine.com api.virtuscore.com _;",
        1,
    )
# HTTP→HTTPS redirect for API host
redirect = f"""
    # Force HTTPS for API hostname (IP / other hosts stay HTTP).
    if ($host = {domain}) {{
        return 301 https://$host$request_uri;
    }}
"""
if f"if ($host = {domain})" not in text:
    text = text.replace(
        "server_name api.genesis-ai-engine.com api.virtuscore.com _;",
        "server_name api.genesis-ai-engine.com api.virtuscore.com _;" + redirect,
        1,
    )
p.write_text(text, encoding="utf-8")
print(f"nginx.conf HTTPS block written for {domain}")
PY

echo "==> Reload nginx"
cd "$DEPLOY"
docker compose up -d nginx
docker exec virtus-nginx nginx -t
docker exec virtus-nginx nginx -s reload

echo "==> Point Farm public URL to HTTPS"
ENVF="$DEPLOY/.env"
PUBLIC="https://${DOMAIN}"
if grep -q '^GENESIS_API_PUBLIC_URL=' "$ENVF"; then
  sed -i "s|^GENESIS_API_PUBLIC_URL=.*|GENESIS_API_PUBLIC_URL=${PUBLIC}|" "$ENVF"
else
  echo "GENESIS_API_PUBLIC_URL=${PUBLIC}" >> "$ENVF"
fi
if grep -q '^GENESIS_OVH_PUBLIC_API=' "$ENVF"; then
  sed -i "s|^GENESIS_OVH_PUBLIC_API=.*|GENESIS_OVH_PUBLIC_API=${PUBLIC}|" "$ENVF"
else
  echo "GENESIS_OVH_PUBLIC_API=${PUBLIC}" >> "$ENVF"
fi
docker compose up -d genesis

echo "==> Smoke"
curl -fsS "https://${DOMAIN}/api/farm/runtime/de-plz-city-lookup/health"
echo
echo "PASS: https://${DOMAIN} is live"
