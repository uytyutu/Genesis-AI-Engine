# ANON — Production audit (pre-domain)

**Goal:** ship what works to a real domain. Not more concepts.  
**Date:** 2026-10-07 · Audit method: route HTTP probe + code review + smoke script · localhost:3100 available this session.

**Public product promise (must feel true):**

> ANON already works. Here’s what you can do right now.

DNA / Director / Assemble Me / … = **future** (`/dna`), never the first promise on `/`.

---

## Scoreboard

| Area | Status | Notes |
| --- | :---: | --- |
| Homepage | 🟡 | Live offers first; DNA demoted to footer teaser (fixed this pass) |
| Secrets `/secrets` | ✅ | Inbox + share link (auth) |
| Inbox `/inbox` | ✅ | Received gifts list |
| Moments `/moments` | 🟡 | Create path via `/create` — verify paid E2E on live Stripe |
| Drop `/drop` | 🟡 | UI live; needs live Stripe + webhook on domain |
| Open Later `/open-when` | 🟡 | Create + lock; unlock-after-date needs timed E2E |
| Games `/games` + `/play` + `/r/:code` | 🟡 | Rooms exist; full rematch E2E not fully certified this pass |
| ANON+ `/plus` | 🟡 | Entitlements server-side; needs live pack checkout |
| Profiles `/u/:user` · `/@user` | ✅ | Free secret send API |
| Auth register/login/logout | ✅ | Cookie session |
| Payments (sandbox local) | ✅ | Smoke PASS incl. ask_reveal no identity leak |
| Payments (live domain) | ❌ | Block until Stripe keys + webhook + `ANON_PUBLIC_URL=https://…` |
| API core | ✅ | Gifts / open / profile / engage |
| Mobile nav | 🟡 | Secrets-first nav present; visual QA pending |
| Security (tenant isolation) | 🟡 | Gift list by user; open by secret token; admin staff-gated — full pen-test pending |
| Production domain | ❌ | Not deployed; launch blockers via `/api/health` |
| DNA `/dna` | ✅ | Labeled Coming; not sold as Live |
| Error 404 | ✅ | `not-found.tsx` added |
| i18n RU/EN/DE | ✅ | Complete dicts; other locales fall back |
| Legal pages | 🟡 | Routes exist; operator entity must be real before DE ads |

Legend: ✅ ready · 🟡 works with caveats · ❌ blocks public domain

---

## A. Route audit (HTTP)

Probed `localhost:3100` — all returned **200** unless noted:

`/` · `/secrets` · `/inbox` · `/moments` · `/games` · `/plus` · `/open-when` · `/drop` · `/anonymous` · `/create` · `/play` · `/dna` · `/auth/*` · `/dashboard` · `/settings` · `/rank` · `/help` · `/impressum` · `/not-a-page` → **404**

Footer updated: Secrets · Drop · Moments · Open Later · Games · DNA (coming). Removed dead-feeling emphasis on `/anonymous` as primary.

---

## B. Copy honesty

| Claim | Rule |
| --- | --- |
| Secrets / Drop / Open Later / Moments / Games | May say Live / price / CTA |
| DNA, Assemble, Know Me, Director, Memory, Swap | **Coming** everywhere; homepage only a dashed teaser after Live loop |
| Voice | Flag `ANONYMOUS_VOICE=0` — Coming |
| Recipient paywall on open | Forbidden — Reply Economy |

---

## C. Payments & env (domain gate)

Before pointing DNS at ANON, `/api/health` → **`domainReady: true`**  
(`launchReady` can be true on localhost with sandbox — that does **not** mean deploy.)

| Env | Required |
| --- | --- |
| `ANON_PUBLIC_URL` | `https://your.domain` (not localhost) |
| `ANON_AUTH_SECRET` | long random ≠ example |
| `STRIPE_SECRET_KEY` or `_LIVE` | real |
| `STRIPE_WEBHOOK_SECRET` or `ANON_STRIPE_WEBHOOK_SECRET` | webhook → `/api/stripe/webhook` |
| `ANON_PAYMENT_SANDBOX` | **0** / unset on public host |

Code guards: sandbox auto-disabled if `NODE_ENV=production` and public URL is not local; see `src/lib/production-guard.ts`.

---

## D. Security (code-level)

| Check | Result |
| --- | --- |
| Inbox only own `recipient_id` | ✅ API filters by session user |
| Open gift by UUID enumeration | ✅ Open uses unguessable `token` |
| Engage / reveal only parties | ✅ sender or recipient |
| Admin APIs | ✅ `requireStaff` |
| Entitlements from client alone | ✅ grant only in `markOrderPaid` |
| Sandbox pay on public domain | ✅ blocked without Stripe (guard) |

Still needed before big traffic: rate-limit review, abuse/report path live test, legal entity fill.

---

## E. Smoke (local)

`node scripts/smoke.mjs` (with sandbox):

- register A → paid anon gift → B open free → free reply → ask_reveal pay → **no identity leak** → decline → still hidden → **PASS**

---

## F. Deploy checklist (when CEO picks domain)

1. Set production env (table C)  
2. `npm run build` GREEN  
3. Point domain → host; Stripe webhook to `https://domain/api/stripe/webhook`  
4. `GET /api/health` → `launchReady: true`  
5. Manual: register → username → share `/u/x` → secret → open → reply  
6. Manual: Drop sandbox-off live €1.99 → open free for recipient  
7. Only then: share link publicly  

**Do not deploy while DNA is the hero of the homepage.** (Fixed: Live first.)

---

## Verdict

| Question | Answer |
| --- | --- |
| Can we deploy *this exact build* to a public domain today? | **No** — payments/env/legal/domain ❌ |
| Is the product shape right for first users? | **Yes** — secrets + paid moments orbit; DNA future |
| Next work | Production env + live Stripe + one human E2E on domain — not new features |
