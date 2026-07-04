# Release Audit RC1

**Дата:** 2026-07-04  
**Среда проверки:** production (live) + локальный build  
**Цель:** найти блокеры до первого реального клиента

---

## Резюме

| Уровень | Найдено | Исправлено в коде | Требует deploy / CEO |
|---------|---------|-------------------|----------------------|
| **Critical** | 2 | 0 | 2 |
| **High** | 4 | 3 | 1 |
| **Medium** | 6 | 1 | 5 |
| **Low** | 5 | 0 | 5 |

**Главный вывод:** RC1-работа **не задеплоена** на production. Клиент сегодня видит только `/site` и `/order`. Всё остальное (legal, SEO, services, pricing) — **404**.

---

## 🔴 Critical

### C1 — RC1 не на production (Vercel + Railway)

**Проверка:** HEAD на `genesis-ai-engine.vercel.app`

| URL | Production | После deploy (local build) |
|-----|------------|----------------------------|
| `/site` | ✅ 200 | ✅ |
| `/order` | ✅ 200 | ✅ |
| `/services` | ❌ 404 | ✅ |
| `/pricing` | ❌ 404 | ✅ |
| `/faq`, `/kontakt`, `/impressum`, `/datenschutz`, `/agb` | ❌ 404 | ✅ |
| `/robots.txt`, `/sitemap.xml`, `/icon` | ❌ 404 | ✅ |

**API:**

| Endpoint | Production |
|----------|------------|
| `/api/sales/packages` | ✅ 200 |
| `/api/sales/payment-status` | ✅ 200 (test Stripe) |
| `/api/public/pricing` | ❌ 404 (код есть, не задеплоен) |

**Действие CEO/Cursor:** `git push main` → Vercel + Railway redeploy. Без этого outreach невозможен юридически (нет Impressum на сайте).

---

### C2 — Stripe Live + Webhook не готовы

```json
{
  "configured": true,
  "live_mode": false,
  "webhook_configured": false,
  "provider_label": "Stripe (test)"
}
```

**Риск:** реальный клиент не сможет оплатить live-деньгами; webhook не подтвердит оплату автоматически.

**Действие CEO:** KYC → `sk_live_` → live webhook → Railway vars → smoke test €1.

---

## 🟠 High

### H1 — Email «Оплатить» вёл на sandbox `/order/pay` ✅ ИСПРАВЛЕНО

Письмо «Заказ получен» ссылало на `/order/pay` (тестовый UI), а production использует **Stripe Checkout**.

**Fix:** CTA → `/order/status/{id}` + кнопка «Оплатить» на странице статуса.

---

### H2 — Страница статуса без оплаты и без public shell ✅ ИСПРАВЛЕНО

Клиент из email попадал на голую страницу без header/footer и без кнопки оплаты.

**Fix:** `PublicPageShell` + `startOrderCheckout()` при `awaiting_payment`.

---

### H3 — `/order/pay` только sandbox ✅ ИСПРАВЛЕНО

**Fix:** Stripe checkout через общий `orderCheckout.ts`; sandbox только если `payment-status.sandbox === true`.

---

### H4 — Нет security headers на frontend ✅ ИСПРАВЛЕНО

**Fix:** `next.config.ts` — X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy.

*(После deploy — перепроверить заголовки на production.)*

---

## 🟡 Medium

### M1 — Legal placeholders до Gewerbe

Impressum/Datenschutz показывают `[Name nach Gewerbeanmeldung]` пока нет env:
`NEXT_PUBLIC_LEGAL_NAME`, `ADDRESS`, `PHONE`.

**Действие CEO:** после Gewerbe — заполнить в Vercel.

---

### M2 — Email «заказ завершён» отсутствует

Есть: заказ получен + оплата подтверждена.  
Нет: письмо при `delivered`.

**Действие:** hook в `mark_delivered` — после EL3 polish.

---

### M3 — `confirm-payment` на `?paid=1` (хрупкий fallback)

Статус-страница вызывает `confirm-payment` при return из Stripe. Основной путь — **webhook**. Без webhook оплата может не зафиксироваться.

**Действие CEO:** live webhook обязателен (см. C2).

---

### M4 — Backend email на create_order не на production

`send_order_received` в `main.py` — в незакоммиченном коде.

**Действие:** deploy backend.

---

### M5 — Mobile audit не автоматизирован

Public header имеет mobile menu (код). Нужна ручная проверка на 375px / 768px после deploy.

---

### M6 — `launch_ready: false` в public-launch checklist

`soft_ready: true`, но `stripe_live` = error. Согласовано с Mission 1 gate.

---

## 🟢 Low

| # | Issue | Note |
|---|-------|------|
| L1 | Нет CSP header | Добавить после стабилизации inline styles |
| L2 | OG image — нет `opengraph-image` | Только meta tags |
| L3 | MC routes не закрыты auth | OK для EL2; не публичный marketing |
| L4 | Нет rate limit на POST `/api/sales/orders` | Post-EL3 |
| L5 | Email optional в backend schema | Frontend требует; backend — нет |

---

## Исправлено автоматически (эта сессия)

- [x] Email CTA → status page + оплата на статусе
- [x] `orderCheckout.ts` — единый Stripe flow
- [x] `/order/pay` — Stripe или sandbox
- [x] `/order/status` — public shell + pay button + Suspense
- [x] Security headers в `next.config.ts`
- [x] HTML emails (предыдущая сессия RC1)

---

## Требует решения CEO

1. **Deploy** всех RC1 + audit fixes (`git push`)
2. **Gewerbe** → legal env vars
3. **Stripe Live** + webhook + smoke
4. **DPAs** (Vercel, Railway, Resend, Stripe) перед публичным Datenschutz
5. **Ручной mobile pass** после deploy

---

## Demo Mode — путь клиента

> *Я владелец строительной компании в Берлине. Мне нужен сайт. Я ничего не знаю о Genesis.*

### Секунда 0 — Google / ссылка

Попадаю на **`/site`** (работает на production).

| | |
|---|---|
| ✅ Доверие | Цена «от 350 €», шаги, FAQ, CTA «Заказать» |
| ⚠️ Вопрос | Footer без Impressum/Datenschutz (404 на production) |
| ⚠️ Недоверие | Нет юридических ссылок внизу — для DE это red flag |

### Клик «Заказать» → `/order`

| | |
|---|---|
| ✅ | Понятная форма, пакеты справа, цена видна |
| ⚠️ | Нет header/footer на production (старая версия) |
| ❓ | «Нужен логотип» — неясно, входит ли в Basic |

### Отправка формы

| | |
|---|---|
| ✅ | Сразу видно цену и «Оплатить» |
| ⚠️ | Без email на production письмо не придёт |
| ⚠️ | Если уйду — только номер заказа, нет «сохраните ссылку» на экране подтверждения |

### Оплата (Stripe test на production)

| | |
|---|---|
| ✅ | Stripe Checkout работает (test keys) |
| ⚠️ | Return URL — нужен `?paid=1` + webhook для надёжности |
| ❓ | Клиент не знает, что это test mode |

### После оплаты — статус

| | |
|---|---|
| ✅ | Timeline, срок ~48ч |
| ⚠️ | На production нет кнопки оплаты если вернулся из email |
| ⚠️ | «Скопировать подтверждение» — внутренний инструмент, клиенту не нужно |

### Что хотелось нажать

1. **Impressum** в footer — не работает (404)
2. **Пример готового сайта** — нет portfolio (OK для v1)
3. **WhatsApp** — только в форме, нет кнопки связи на landing

### Рекомендации UX (после deploy)

1. На экране «Спасибо» после заказа — **жирно**: «Сохраните ссылку на статус»
2. Убрать «Скопировать подтверждение» с публичной статус-страницы (owner-only)
3. Добавить WhatsApp/email в footer Kontakt
4. После Gewerbe — полный Impressum без placeholder banner

---

## Следующий шаг

```
1. Deploy RC1 + audit fixes  ← СЕЙЧАС
2. Re-run URL checklist на production
3. CEO: Gewerbe + Stripe Live
4. Manual mobile/tablet pass
5. Design Polish (loader, transitions)
6. Outreach 25
```

---

*Mission RC1 Release Audit — завершён. Genesis Client Foundation — после deploy (см. `Genesis_Client_Foundation.md`).*
