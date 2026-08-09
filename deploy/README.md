# Virtus Core — VPS deploy

**Storefront (vitrine)** on this VPS via Next.js. Owner Mission Control stays gated (middleware → strangers get `/site`).

```
Internet → nginx :80
              ├─ /api /health /webhooks → genesis :8000
              └─ /                      → frontend :3000  (/site, /order, …)
                    └─ /data  (GENESIS_MEMORY_DIR)
```

No PostgreSQL. No Redis. One `genesis` container (`restart: unless-stopped`).

| File | Role |
|------|------|
| `docker-compose.yml` | `genesis` + `frontend` + `nginx` |
| `Dockerfile.frontend` | Next.js production image |
| `nginx.conf` | API vs storefront split |
| `.env.example` | Secrets template → `.env` on server |
| `.gitignore` | Ignores `.env` |

Root `Dockerfile` = API (unchanged).

## Before first up

1. Backup Railway/Vercel env + Stripe/Resend webhook URLs.
2. Copy volume `/data` if migrating live state.
3. Leave DNS on Vercel until Stage 3 CEO OK.

## Deploy (Stage 2 — no DNS)

```bash
cd /path/to/Genesis-AI-Engine/deploy
cp .env.example .env   # fill from Railway backup
sudo mkdir -p /srv/genesis/data
sudo chown "$USER:$USER" /srv/genesis/data
docker compose up -d --build
```

Smoke (replace `VPS_IP`):

```bash
curl -fsS "http://VPS_IP/health"
curl -fsS "http://VPS_IP/api/status"
curl -fsSI "http://VPS_IP/site"    # storefront
curl -fsSI "http://VPS_IP/order"   # order path
```

## Hard rules

1. Single `genesis` instance — no `uvicorn --workers`, no scale.
2. Volume `/srv/genesis/data` → `/data` required.
3. Do not switch DNS until storefront smoke PASS + CEO OK.
4. Stripe/Resend webhooks switch **after** DNS (Stage 3).
5. Never commit `deploy/.env`.

## Stage 3 (separate approval)

1. Point `virtuscore.com` → this OVH VPS (Production).
2. TLS (certbot) + uncomment 443.
3. Update Stripe webhook URL.
4. Keep Vercel as **Preview only** (~48h warm as rollback). Do not leave customer DNS on Vercel.
