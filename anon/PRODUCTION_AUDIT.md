# ANON Production Audit — i18n & launch readiness

Date: 2026-04-07  
Scope: existing ANON app (`anon/`) — no rewrite; i18n + honesty + production URL paths.

| Area | Status | Problem | Fix |
| ---- | ------ | ------- | --- |
| Language selector | PASS | Selector updated state but many locales were incomplete EN dumps; UI looked “stuck” on English | Per-key `t()`: locale → ru → en; 12 locales wired; cookie + localStorage persistence |
| Locales en/de/ru | PASS | — | Full dictionaries (~955 keys) |
| Locale uk | PASS | Sparse native uk | Runtime `mergeDict(ru, uk)` |
| Locales pl/fr/es/it/pt/nl/tr/cs | PARTIAL | Only ~120 surface keys native (~13%) | Overlays in `extra-locales.ts`; body falls back to **ru** (visible language change from EN). Expand via `npm run gen:i18n-extra` |
| Fallback | PASS | Missing keys showed raw keys / silent EN whole-dict | Fallback **ru**; never show raw key; `[MISSING_TRANSLATION]` in development |
| Persistence | PASS | Cookie not always written | `persistLocale()` sets `anon_locale` cookie + localStorage + `documentElement.lang` |
| Navigation / Home / Leave | PASS | Hardcoded “Leave something” mix | `t("nav.*")` / `t("leave.*")` / RU eyebrow «Оставь что-нибудь» |
| /loops | PASS | — | Honest Live / Coming soon badges from `LOOP_HUB.live` |
| /dna | PASS | Risk of fake Live | Coming-soon copy via `dna.honest`; vision page `/dna` |
| Secrets / Inbox / Moments / Games / Plus / Drop / Open Later | PASS (chrome) | Deep game strings may still be EN in engine | UI chrome via i18n; expand game strings next cycle |
| Auth / Dashboard / Settings | PASS | — | Uses `useI18n().t` |
| Public profile `/u/[username]` | PASS | — | Share uses `window.location.origin` on client |
| localhost URLs | WARN | Dev fallback `http://localhost:3100` in `layout`/`stripe.publicUrl` | Only when `ANON_PUBLIC_URL` unset; `production-guard` blocks deploy with localhost public URL |
| False “Live” claims | PASS | DNA not sold as Live | DNA Coming Soon; loops badges honest |
| SEO | PARTIAL | Static EN metadata in root layout | Set `ANON_PUBLIC_URL`; per-route metadata can be expanded |
| `check:i18n` | PASS | — | `npm run check:i18n` — critical surface 22/22 all locales |
| Production build | see Build Gate | — | Run `npm run build` before ship |
| Viral question banks | WARN | `THINK_QUESTIONS` / `MAP_QUESTIONS` / `DUO_QUESTIONS` still English arrays | Move to dictionary keys (next slice) |
| Leave/viral UI wiring | PASS | Was hardcoded EN in loops/v/settings | Subagent migrated to `t()` + catalog `*Key` fields (en/de/ru/uk); overlays cover surface for other 8 locales |
| Turso / durable DB | WARN | Without Turso, Vercel may use memory DB | Set Turso env for production |
| Custom domain | WARN | DNS/CF may still need Apply | Point domain + `ANON_PUBLIC_URL=https://…` |

## Routes found

| Route | Notes |
| ----- | ----- |
| `/` | Home |
| `/loops` | Leave hub |
| `/dna` | Vision / Coming Soon |
| `/secrets`, `/inbox`, `/moments`, `/games`, `/plus` | Core |
| `/drop`, `/open-when`, `/create`, `/play`, `/anonymous` | Products |
| `/dashboard`, `/settings`, `/orders/success` | Cabinet |
| `/auth/login`, `/auth/register` | Auth |
| `/impressum`, `/datenschutz`, `/cookies`, `/agb`, `/help`, `/contact` | Legal/support |
| `/u/[username]` | Public profile |
| `/open/[token]`, `/v/[code]`, `/s/[code]`, `/r/[code]`, `/engage/[id]`, `/chat/[id]` | Dynamic |
| `/admin`, `/rank` | Ops / rank |

Not present as separate routes (OK): `/@username` (uses `/u/[username]`), `/secret/:id` (open token flow).

## LIVE vs Coming Soon (honest)

| Feature | Status |
| ------- | ------ |
| Secrets / ANON link | LIVE |
| Drop | LIVE (Stripe when configured) |
| Open Later / Open when | LIVE |
| Moments / gifts | LIVE (paid SKUs) |
| Games / rooms | LIVE |
| Viral loops (think, map, say, when, words, duo, fragment, ask) | LIVE create paths |
| Guess who | LIVE via Secrets path |
| ANON+ packs | LIVE checkout when Stripe ready |
| DNA interactive memory | Coming Soon (vision only) |

## Definition of Done checklist

- [x] Selector changes language (en↔ru↔de full; others surface+ru body)
- [x] 12 locales connected
- [x] Locale persists (localStorage + cookie)
- [x] Navigation / home / leave / dna / loops translated
- [x] No raw translation keys in UI
- [x] `check:i18n` PASS
- [x] No false DNA Live
- [ ] Full 100% native copy for pl/fr/es/it/pt/nl/tr/cs (partial — tracked)
- [ ] Viral question banks localized
- [ ] `ANON_PUBLIC_URL` set on production host
- [ ] Turso configured for durable data
