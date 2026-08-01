#!/bin/bash
set -euo pipefail
API=http://127.0.0.1
TOKEN=$(sudo docker exec virtus-genesis python -c 'from app.integration.owner_auth import issue_owner_token; print(issue_owner_token())')
AUTH="Authorization: Bearer $TOKEN"
echo "=== OWNER TOKEN ISSUED (not printed) ==="
echo "=== ACQUISITION STATUS ==="
code=$(curl -s -o /tmp/acq.json -w "%{http_code}" -H "$AUTH" "$API/api/acquisition/status")
echo "code=$code"
python3 - <<'PY'
import json
d=json.load(open('/tmp/acq.json'))
if isinstance(d, dict):
    print('top_keys', sorted(d.keys())[:30])
    for k in ['runner','outreach_runner','ceo_outbox','status','ok','country_desk','places_quota']:
        if k in d:
            v=d[k]
            if isinstance(v, dict):
                print(k, {kk:v.get(kk) for kk in list(v)[:8]})
            else:
                print(k, v)
else:
    print(str(d)[:300])
PY
echo "=== OUTBOX ==="
curl -s -o /tmp/out.json -w "code=%{http_code}\n" -H "$AUTH" "$API/api/acquisition/outbox" || true
head -c 300 /tmp/out.json; echo
# try common outbox paths
for path in /api/acquisition/ceo-outbox /api/acquisition/outbox/summary /api/business/health; do
  c=$(curl -s -o /tmp/x.json -w "%{http_code}" -H "$AUTH" "$API$path" || true)
  echo "$path -> $c"
done
echo "=== EMAIL SEND TEST ==="
# Use email provider pool dry check / or send to support
sudo docker exec virtus-genesis python - <<'PY'
from app.integration.email_provider_pool import EmailProviderPool
pool = EmailProviderPool()
st = pool.status() if hasattr(pool, 'status') else None
print('pool_status_type', type(st).__name__)
if isinstance(st, dict):
    # booleans only
    for k,v in list(st.items())[:20]:
        if isinstance(v, dict):
            print(k, {kk: ('yes' if vv else 'no') if isinstance(vv, (str,bool)) and kk.endswith(('key','ready','ok','configured')) else type(vv).__name__ for kk,vv in list(v.items())[:10]})
        else:
            print(k, type(v).__name__)
# attempt send to GENESIS_SUPPORT_EMAIL if pool has send
import os
to = (os.getenv('GENESIS_SUPPORT_EMAIL') or 'hello@genesis-ai-engine.com').strip()
try:
    # discover send method
    send = getattr(pool, 'send', None) or getattr(pool, 'send_email', None)
    if callable(send):
        # try common signatures carefully
        try:
            r = send(to=to, subject='Virtus VPS Stage2 smoke', html='<p>Stage2 smoke from VPS — ignore</p>', text='Stage2 smoke from VPS')
        except TypeError:
            try:
                r = send(to, 'Virtus VPS Stage2 smoke', 'Stage2 smoke from VPS')
            except TypeError:
                r = send({'to': to, 'subject': 'Virtus VPS Stage2 smoke', 'text': 'Stage2 smoke'})
        print('send_result', type(r).__name__, str(r)[:200])
    else:
        print('no_send_method_on_pool')
except Exception as e:
    print('send_error', type(e).__name__, str(e)[:200])
PY
echo "=== SMOKE OWNER DONE ==="
