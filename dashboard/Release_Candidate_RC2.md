# Mission RC2 — Release Polish

**Статус:** ✅ **READY FOR COMMIT** (локально завершён) · ⏳ push по команде CEO  
**Цель:** Genesis выглядит как **премиальный продукт**, без изменения Mission 1.

**Правило:** только улучшение существующего. Новые большие функции → Horizon.

---

## Priority A — Brand System

- [x] Design tokens (`app/lib/tokens.ts`, `globals.css`)
- [x] Logo mark (`GenesisMark`)
- [x] Палитра, типографика, радиусы, тени
- [x] Единые кнопки, карточки, поля, бейджи

## Priority B — Micro UX

- [x] Плавные переходы (`transition-smooth`, `animate-fade-up`)
- [x] Skeleton loading
- [x] Empty states
- [x] Hover / loading / error states
- [x] `prefers-reduced-motion` respected

## Priority C — UI Kit (`app/components/ui/`)

- [x] Button, Card, Input, Badge, Loader, EmptyState, Modal, Dialog, Tabs
- [x] Toast (enhanced styling)
- [x] Все публичные страницы на UI Kit

## Priority D — Accessibility

- [x] `:focus-visible` ring
- [x] `aria-*` на Modal, Loader, steps
- [ ] Полный keyboard audit — post-deploy

## Priority E — Performance

- [x] System font stack (no extra font download)
- [ ] Lighthouse pass — post-deploy

---

## 🚫 До EL3

Marketplace · новые AI-модули · Executive · новые платные фичи

---

## Параллельно

**Genesis Client Foundation** — отдельно, без давления на RC2.
