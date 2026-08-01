#!/bin/bash
set -euo pipefail
API=http://127.0.0.1
echo "=== HEALTH ==="
curl -fsS "$API/health"; echo
echo "=== PACKAGES ==="
curl -fsS "$API/api/sales/packages" > /tmp/pkgs.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/pkgs.json'))
pkgs=d.get('packages') or []
print('count', len(pkgs))
if pkgs:
    print('first_id', pkgs[0].get('id'), 'price', pkgs[0].get('price_eur'))
PY
PKG=$(python3 -c 'import json;print((json.load(open("/tmp/pkgs.json")).get("packages") or [{}])[0].get("id") or "basic")')
echo "=== CREATE ORDER pkg=$PKG ==="
curl -s -o /tmp/order.json -w "http=%{http_code}\n" -X POST "$API/api/sales/orders" \
  -H 'Content-Type: application/json' \
  -d "{\"package_id\":\"$PKG\",\"business_name\":\"Virtus Smoke GmbH\",\"description\":\"Stage2 smoke order for VPS validation\",\"email\":\"stage2-smoke@example.com\",\"city\":\"Dresden\",\"niche\":\"it\"}"
python3 - <<'PY'
import json
from pathlib import Path
t=Path('/tmp/order.json').read_text()
print(t[:500])
try:
  d=json.loads(t)
  print('order_id', d.get('order_id') or d.get('id') or d.get('order',{}).get('id'))
except Exception as e:
  print('parse_err', e)
PY
echo "=== STRIPE WEBHOOK ENDPOINT REACHABLE ==="
# unsigned body should fail validation with 400 — proves route is live
code=$(curl -s -o /tmp/wh.json -w "%{http_code}" -X POST "$API/api/webhooks/stripe" \
  -H 'Content-Type: application/json' \
  -H 'Stripe-Signature: t=1,v1=invalid' \
  -d '{"type":"checkout.session.completed","data":{"object":{"id":"cs_test_smoke"}}}')
echo "unsigned_or_invalid_sig_http=$code"
head -c 200 /tmp/wh.json; echo
echo "=== PERSISTENCE ==="
test -f /srv/genesis/data/smoke_container_marker.txt && echo PERSIST_MARKER=YES
ls /srv/genesis/data/*order* 2>/dev/null | head -10 || true
ls /srv/genesis/data/ | head -30
echo "=== DONE ==="
