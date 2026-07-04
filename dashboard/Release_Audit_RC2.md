# Release Audit RC2

**Дата:** 2026-07-04  
**Статус:** ✅ **READY FOR COMMIT** (локально) · ⏳ Production после push  
**Правило:** один commit RC2 → push → production re-audit

---

## UI Kit Coverage — публичные страницы

| Страница | UI Kit | Hero | Card | Button | Badge | Loader/Skeleton |
|----------|--------|------|------|--------|-------|-----------------|
| `/site` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/order` | ✅ | steps | ✅ | ✅ | ✅ | ✅ |
| `/order/pay` | ✅ | — | ✅ | ✅ | — | — |
| `/order/status` | ✅ | — | ✅ | ✅ | — | ✅ |
| `/services` | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `/pricing` | ✅ | Card | ✅ | ✅ | ✅ | — |
| `/faq` | ✅ | ✅ | ✅ | ✅ | — | — |
| `/kontakt` | ✅ | ✅ | ✅ | ✅ | — | — |
| `/impressum` | ✅ | ✅ | ✅ | — | — | — |
| `/datenschutz` | ✅ | ✅ | ✅ | — | — | — |
| `/agb` | ✅ | ✅ | ✅ | — | — | — |
| `404` / `500` | ✅ | — | — | ✅ | — | — |

**Shared:** `PublicPageShell` (skip link, `main`), `PublicPageHero`, `FaqList`, `GenesisMark`

---

## Performance (Lighthouse — production `/site`, pre-RC2 deploy)

| Категория | Score |
|-----------|-------|
| Performance | **99** |
| Accessibility | **98** |
| Best Practices | **100** |
| SEO | **100** |

*RC2 deploy ожидается ≥ RC1. System fonts — без лишних загрузок.*

---

## Accessibility

| Check | Status |
|-------|--------|
| Skip to content link | ✅ `PublicPageShell` |
| `:focus-visible` rings | ✅ globals + UI Kit |
| `aria-label` на steps, loaders | ✅ |
| `role="main"` | ✅ |
| `prefers-reduced-motion` | ✅ globals.css |
| Section headings `aria-labelledby` | ✅ `/site`, `/pricing` |
| Keyboard TAB (manual) | ⏳ рекомендуется CEO post-deploy |

**Remaining:** полный screen reader pass — post-deploy.

---

## Design Consistency

| Element | Стандарт |
|---------|----------|
| Radius | `rounded-xl` / `rounded-2xl` (Card, Input, Button) |
| Spacing | `PublicPageShell` px-4 sm:px-6, Card padding sm/md/lg |
| Hover | `transition-smooth` + Card genesis-card |
| Colors | `tokens.ts` + tailwind `genesis.*` |
| Loaders | `ui/Loader` единый Spinner |
| Skeleton | `PackageSkeleton`, site pricing grid |

---

## Mobile (code review)

| Viewport | Проверка |
|----------|----------|
| 320–375px | Mobile nav menu, full-width CTAs |
| 768px | 2-col grids на site/services |
| 1024px+ | max-w-5xl shell |

*Ручная проверка на устройстве — post-deploy.*

---

## Genesis Client Foundation — Stage 1

| Task | Status |
|------|--------|
| Stack: Tauri 2 + React | ✅ |
| `client/ARCHITECTURE.md` | ✅ |
| `client/shared/design-tokens.json` | ✅ |
| Tauri scaffold | ⏳ после RC2 deploy |

---

## Remaining Improvements (не блокируют RC2)

- OG image asset (`opengraph-image.tsx`)
- CSP header (post-EL3)
- Полный keyboard audit на production
- `/site` — вынести FAQ в shared constant с `/faq` (DRY)
- Client: `tauri init` desktop shell

---

## Next Steps

```
1. Commit RC2 (один раз)     ← CEO approval
2. Push → Vercel
3. Production Re-Audit
4. RC2 PASSED
5. Genesis Client Stage 1 → tauri init
```

---

## Политика

`dashboard/Genesis_Development_Policy.md` — непрерывная разработка, gate на публикацию.
