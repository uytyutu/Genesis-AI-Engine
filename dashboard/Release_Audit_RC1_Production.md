# Release Audit RC1 — Production Re-Audit

**Дата:** 2026-07-04  
**Commit:** `7e7eb6e` (+ OG fix follow-up)  
**Статус:** ✅ **Release Candidate RC1 PASSED** (technical)

---

## Deploy

| Service | Result |
|---------|--------|
| Git push `main` | ✅ `b889caa..7e7eb6e` |
| Vercel | ✅ ~45s to 200 on new routes |
| Railway | ✅ `/api/public/pricing` 200 |

---

## Frontend URLs (production)

| URL | Status |
|-----|--------|
| `/site` | ✅ 200 |
| `/services` | ✅ 200 |
| `/order` | ✅ 200 |
| `/pricing` | ✅ 200 |
| `/faq` | ✅ 200 |
| `/kontakt` | ✅ 200 |
| `/impressum` | ✅ 200 |
| `/datenschutz` | ✅ 200 |
| `/agb` | ✅ 200 |
| `/robots.txt` | ✅ 200 |
| `/sitemap.xml` | ✅ 200 |
| `/icon` | ✅ 200 |
| Unknown path | ✅ 404 |

---

## API (production)

| Endpoint | Status |
|----------|--------|
| `/api/sales/packages` | ✅ 200 |
| `/api/sales/payment-status` | ✅ 200 |
| `/api/sales/email-status` | ✅ 200 (`configured: true`) |
| `/api/public/pricing` | ✅ 200 |

---

## Trust & Footer

- ✅ Footer: Impressum, Datenschutz, AGB, FAQ, Kontakt
- ✅ Legal pages render (Gewerbe placeholder banner until env vars)
- ✅ Contact email in footer

---

## SEO & Security

| Check | Status |
|-------|--------|
| `robots.txt` | ✅ allow public, disallow MC |
| `sitemap.xml` | ✅ 9 public URLs |
| favicon `/icon` | ✅ 200 |
| Security headers | ✅ X-Frame-Options, nosniff, Referrer-Policy |
| Open Graph | 🔄 fixed on `/site` in follow-up commit |

---

## Email pipeline

| Step | Status |
|------|--------|
| Resend configured | ✅ |
| Order received email | ✅ code deployed |
| Payment receipt HTML | ✅ code deployed |
| Live send test | ⏳ CEO (no test order on prod) |

---

## Known — CEO gate (not RC1 blockers)

| Item | Status |
|------|--------|
| Stripe Live (`sk_live_`) | ⏳ `live_mode: false` |
| Webhook | ⏳ `webhook_configured: false` |
| Legal env vars | ⏳ after Gewerbe |
| Mobile manual pass | ⏳ recommended post-Gewerbe |

---

## Verdict

> **Release Candidate RC1 PASSED** — публичный продукт технически готов к показу после Gewerbe + Stripe Live.

**Next:** RC2 — Release Polish (Design Polish)
