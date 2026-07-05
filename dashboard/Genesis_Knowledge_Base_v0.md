# Genesis Knowledge Base v0

**Zweck:** Reестр идей и решений — чтобы через год не гадать: «мы это уже обсуждали?»

**Status:** v0 — ручной seed из Foundation. Полная «организационная память» — **после EL3** (Deep Review).

**Правило обновления:** Новая идея → одна строка сюда. Решение принято → статус + причина + дата.

---

## Легенда

| Статус | Значение |
|--------|----------|
| ✅ Реализовано | В production или закрыто в Mission |
| 🟡 В работе | Активная Mission / текущий шаг |
| 🔵 Horizon | Зафиксировано, не строим до evidence |
| 🔴 Отказались | Решение принято — не возвращаться без новых данных |
| ⭐ Исследование | Нужны данные, не код |

---

## ✅ Реализовано

| Идея | Решение | Дата / Evidence |
|------|---------|-----------------|
| Revenue Pipeline v1 | Stripe test → Factory → Email | EL2 |
| Public Launch checklist | `public_launch_service.py`, `legal: ok` | 2026-07 |
| Domain + corporate email | genesis-ai-engine.com, Resend | 2026-07 |
| Foundation (13 principles, EL0–EL6) | Закрыт, frozen до EL3 | 2026-07-04 |
| Business Registration Kit v1 | Gewerbe + Impressum + DSGVO + AGB Vorlagen | 2026-07-04 |
| Payment live_mode API diagnostic | `live_mode`, `webhook_configured` in payment-status | 2026-07-04 |
| Partner framing (не «продажа сайта») | First Customer Plan v1.1 | 2026-07-04 |

---

## 🟡 В работе (Mission 1)

| Идея | Следующий шаг | Блокер |
|------|---------------|--------|
| Stripe Live + smoke test | CEO: sk_live, webhook, Railway | CEO |
| Gewerbeanmeldung Dresden | Kit v1 прочитать → данные → подать | CEO review |
| First Customer outreach | 25 компаний → 5 сообщений | После Stripe Live |
| EL3 | Первый незнакомый платёж live € | Outreach |

---

## 🔵 Horizon (не строим до EL3)

| Идея | Где зафиксировано | Почему ждём |
|------|---------------------|-------------|
| Executive Dashboard / Company Brain | `DIGITAL_COMPANY_VISION.md`, Horizon Brief | Нет рыночных данных |
| **Digital Employee Strategy** (Vision) | `docs/DIGITAL_EMPLOYEE_STRATEGY.md` | Клиентское позиционирование — после EL3 |
| **Role Marketplace** (роли vs инструменты) | `DIGITAL_EMPLOYEE_STRATEGY.md` § Marketplace | После ≥1 доказанного Skill |
| Marketplace (Skills от разработчиков) | `docs/MARKETPLACE.md` | После первого Skill E2E |
| **Pricing Strategy v1** | `dashboard/Genesis_Pricing_Strategy_v1.md` | Launch display live; final policy после EL3 |
| **Business Units Strategy** | `dashboard/Genesis_Business_Units_Strategy.md` | Horizon — отделы, не тарифы |
| Genesis Client App (Win/Mac/Linux/Android) | Horizon Brand Brief | После EL3 + Deep Review |
| Marketplace, Payment Hub | `docs/MARKETPLACE.md`, `docs/ECONOMY.md` | Нет первого Skill proof |
| Preview Engine | First Customer Plan — вручную в M1 | Автоматизация после evidence |
| Communication Center (ceo@, triage) | `Genesis_Progress.md` Horizon | Post-EL3 |
| Подписки Free/Pro/Business | Обсуждение | Нет платящей базы |
| AI-команда автономная | WHY.md owner gates | Только с gates |
| Genesis Knowledge Base полная | Этот файл v0 | После EL3 — автоматизация |

---

## 🔴 Отказались (пока нет новых данных)

| Идея | Причина | Пересмотр когда |
|------|---------|-----------------|
| Berlin как старт outreach | Высокая конкуренция | После первого € в Sachsen |
| `/order` в первом сообщении | Нужно доверие сначала | Mission 1 правило |
| Новые движки / принципы до EL3 | Foundation frozen | Deep Review |
| Railway Volume для public_launch | Git deploy достаточно | — |
| Массовый cold spam | Партнёрский подход, 25 контактов KPI | — |

---

## ⭐ Будущие исследования

| Вопрос | Что нужно для ответа |
|--------|----------------------|
| Kleinunternehmerregelung §19 UStG? | Finanzamt + Steuerberater nach Gewerbe |
| Нужна ли Handwerkskarte? | Nein für 62.09.0 — bestätigt в Kit |
| Авто-память «14 похожих идей» | После EL3: индекс + теги в Knowledge Base v1 |
| Genesis Brain как продукт | Сначала EL3 — memory для себя, потом для клиентов |

---

## Как Cursor должен использовать этот файл

При **новой миссии** или **новой идее**:

1. Поиск по этому файлу + `WHY.md` + `Genesis_Progress.md`
2. Краткий отчёт: «N похожих идей: X реализовано, Y отклонено, Z Horizon»
3. Рекомендация только с evidence — не из памяти чата

**Шаблон ответа (цель на будущее):**

```
Нашёл N похожих идей.
— X реализованы
— Y отклонены (причина: …)
— Z в Horizon
Рекомендация: …
```

---

*v0 · 2026-07-04 · Обновлять при смене статуса Mission, не при каждом чате*
