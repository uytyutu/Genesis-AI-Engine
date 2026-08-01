#!/bin/bash
set -euo pipefail
cd /home/ubuntu/Genesis-AI-Engine/deploy
sudo docker compose up -d genesis
sleep 10
echo "=== HEALTH ==="
curl -fsS http://127.0.0.1/health; echo
echo "=== ACQUISITION ==="
code=$(curl -s -o /tmp/a.json -w "%{http_code}" http://127.0.0.1/api/acquisition/status || true)
echo "code=$code"
head -c 400 /tmp/a.json; echo
echo "=== RUNNER STATE FILE ==="
sudo docker exec virtus-genesis sh -c 'ls -la /data/outreach_runner_state.json /data/outreach_ceo_prefs.json 2>/dev/null; python -c "import json;print(json.load(open(\"/data/outreach_ceo_prefs.json\")))"'
echo "=== EMAIL TEST (Resend API key present only) ==="
sudo docker exec virtus-genesis python -c "import os,httpx; k=os.getenv('RESEND_API_KEY',''); print('resend_key', 'yes' if k else 'no');
# dry identity check without sending if possible
print('from', (os.getenv('GENESIS_EMAIL_FROM') or '')[:40])"
echo "=== DONE ==="
