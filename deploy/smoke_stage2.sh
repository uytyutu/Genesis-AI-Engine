#!/bin/bash
set -euo pipefail
API=http://127.0.0.1
echo "=== 1 HEALTH ==="
curl -fsS "$API/health"; echo
echo "=== 2 STATUS ==="
curl -fsS "$API/api/status" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("name", d.get("name")); print("paused", d.get("paused")); print("keys", len(d))'
echo "=== 3 KEY ENDPOINTS ==="
for path in \
  /api/acquisition/status \
  /api/acquisition/studio/status \
  /api/business/health \
  /api/owner/notifications \
  /api/sales/packages
do
  code=$(curl -s -o /tmp/acq.json -w "%{http_code}" "$API$path" || true)
  echo "$path -> $code"
  python3 -c 'import pathlib; t=pathlib.Path("/tmp/acq.json").read_text(errors="replace"); print(t[:180].replace("\n"," "))'
done
echo "=== 4 DATA WRITE PROBE ==="
MARKER="smoke-$(date -u +%Y%m%dT%H%M%SZ)"
echo "$MARKER" | sudo tee /srv/genesis/data/smoke_host_marker.txt >/dev/null
sudo docker exec virtus-genesis sh -c "echo container-$MARKER > /data/smoke_container_marker.txt && ls -la /data | head -25 && cat /data/smoke_container_marker.txt"
if test -f /srv/genesis/data/smoke_container_marker.txt; then echo HOST_SEES_CONTAINER_WRITE=YES; else echo HOST_SEES_CONTAINER_WRITE=NO; fi
echo "=== 5 RESTART PERSISTENCE ==="
cd /home/ubuntu/Genesis-AI-Engine/deploy
sudo docker compose restart genesis
sleep 12
curl -fsS "$API/health"; echo
sudo docker exec virtus-genesis sh -c 'test -f /data/smoke_container_marker.txt && cat /data/smoke_container_marker.txt'
if test -f /srv/genesis/data/smoke_container_marker.txt; then echo AFTER_RESTART_PERSIST=YES; else echo AFTER_RESTART_PERSIST=NO; fi
echo "=== 6 EXTERNAL IP ==="
curl -fsS --connect-timeout 8 http://137.74.173.134/health || echo EXTERNAL_FAIL
echo
echo "=== 7 ENV PRESENCE IN CONTAINER ==="
sudo docker exec virtus-genesis python -c "import os; keys=['RESEND_API_KEY','GENESIS_EMAIL_FROM','MAILBOX_SMTP_HOST','MAILBOX_SMTP_USER','STRIPE_SECRET_KEY','GOOGLE_API_KEY','GENESIS_MEMORY_DIR'];
[print(k, 'yes' if (os.getenv(k) or '').strip() else 'no') for k in keys]; print('MEMORY_DIR', os.getenv('GENESIS_MEMORY_DIR'))"
echo "=== SMOKE DONE ==="
