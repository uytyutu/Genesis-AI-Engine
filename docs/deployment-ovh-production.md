# Virtus Core — Deployment Policy (SSOT)

## Production

**OVH Cloud** is the only Production.

```text
Cursor → Git → CI/CD → OVH Cloud (Production) → virtuscore.com
```

## Preview / test

**Vercel** = Preview, тестовые сборки, резерв.  
Успешный Vercel deploy **не** означает, что клиенты видят новую версию.

## Why the phone shows an old site

Live check (2026-08):

| Target | Result |
|--------|--------|
| `virtuscore.com` DNS | AWS IPs (`54.x` / `13.x`), Kestrel/ASP.NET |
| OVH `137.74.173.134` | Virtus API alive, `git_commit=unknown`, build ~2026-08-01 |
| Vercel | New frontend READY — but **not** the customer domain |

→ Domain ≠ OVH → phone sees old host.

## Env for Deployment Manager

```bash
GENESIS_OVH_HOST=137.74.173.134          # or OVH hostname
GENESIS_OVH_SSH=ubuntu@137.74.173.134    # optional, for remote git HEAD
GENESIS_OVH_SSH_USER=ubuntu              # alt to full SSH target
GENESIS_OVH_REMOTE_PATH=/srv/genesis
GENESIS_EXPECTED_PRODUCTION_HOST=ovh
# GENESIS_OVH_AUTO_DEPLOY=1              # only with SSH + explicit CEO intent
```

## CEO report

`GET /api/owner/ceo-dashboard` → `deployment_manager`

Commit chain:

```text
Local:        a1b2c3
Vercel:       a1b2c3 ✅   (Preview)
OVH:          98fd12 ❌   (Production)
Domain:       98fd12 ❌   (virtuscore.com)
Status:
Production behind by 1+ deployment.
```

Production Health (8 checks): Domain · DNS · OVH · Backend · Frontend · SSL · Build · Latest Commit.

## Deploy

```bash
# after SSH configured
export GENESIS_OVH_SSH=user@YOUR_OVH_IP
bash scripts/deploy_ovh.sh
```

Then point `virtuscore.com` A/AAAA → OVH IP.
