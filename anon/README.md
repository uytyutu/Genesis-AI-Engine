# ANON

Social platform for digital emotional moments — anonymous notes, surprises, Open When.

```text
💌 SEND   🕵️ ANON   🔒 OPEN WHEN
```

## Quick start

```bash
cd anon
npm install
npm run dev          # :3100 — uses webpack (Turbopack hangs in this monorepo)
# or: pwsh scripts/start_local.ps1
```

Open [http://localhost:3100](http://localhost:3100).  
Health: [http://localhost:3100/api/health](http://localhost:3100/api/health)

### Public tunnel (same pattern as Virtus API / Oracle reachability)

```powershell
pwsh anon/scripts/start_public.ps1
# → https://….trycloudflare.com
```

Mission Control: `{public}/auth/login?next=/admin`  
Owner: email = `ANON_ADMIN_EMAIL` (default `admin@anon.app`).  
Reset local owner password: `node scripts/reset_owner_password.mjs 'YourPass'`

### Deploy to OVH (when SSH works)

```powershell
pwsh anon/scripts/deploy_ovh.ps1
```

Before custom DNS: `/api/health` → `domainReady: true` (Stripe + non-localhost URL).

Sandbox payments are on by default (`ANON_PAYMENT_SANDBOX=1`).  
To use real Stripe, set `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` and turn sandbox off.

## Docs

- [docs/ANON.md](./docs/ANON.md) — architecture, pricing, security, deploy
- [docs/SEND.md](./docs/SEND.md) — SEND loop inside ANON

## KPI

Microtransaction revenue + viral reply rate — separate track from Virtus Core.
