# Genesis Business Launch Gate v1.1

**Версия:** 1.1 · 2026-07-04  
**Статус:** 📐 SPEC + HORIZON — **не автоматизация**, не юридический совет  
**Модуль (будущее):** Business Readiness Advisor в Desktop (Executive / Home)

> **⚠️ Внутренний бизнес-порог Genesis.** Не является юридическим критерием и **не заменяет** требования законодательства или правил платёжных платформ.

---

## Что это НЕ

| ❌ | ✅ |
|----|-----|
| `$1500 = переход` | **Business Readiness Score** — совокупность признаков |
| Юридическое решение по баллам | Внутняя логика развития проекта |
| Genesis меняет payment / legal сам | Genesis говорит: *«Я считаю, компания готова»* → **CEO решает** |
| Cursor меняет env без CEO | Только после **Approve Business Launch** |

Юридические действия (Gewerbe, Jobcenter, налоги) — **всегда CEO**.

---

## Genesis Laws

| Law | Business Launch Gate |
|-----|----------------------|
| **№1** | Recommend → Approve → Act |
| **№4** | Mission 1 вручную → потом score в Desktop |
| **№5** | Ответственность за бизнес и право — у человека |

---

## Принцип

> **Genesis не даст CEO случайно нарушить правила.**

Genesis **никогда сам не меняет:**

* платёжную систему;
* юридические данные и реквизиты;
* статус бизнеса в env;
* публикации без approve.

Он **считает readiness**, показывает рекомендации, ждёт **Approve Business Launch**.

---

## Business Readiness Score

Бизнес определяется **не одной суммой**, а набором событий. Баллы **настраиваемые** (пример v1):

| Событие | Баллы |
|---------|------:|
| Первый оплаченный заказ | +20 |
| Второй **независимый** клиент (другой payer / email) | +20 |
| 5+ продаж за 7 дней | +20 |
| Первая активная подписка | +20 |
| Платёжная платформа запросила KYC / tax verification | +20 |
| *опционально* Выручка > настраиваемый USD порог | +10 |
| *опционально* Продажи 3+ дня подряд | +10 |

**Максимум в примере:** 100 (события не обязаны суммироваться выше cap — настраивается).

### Зоны

| Score | Зона | Смысл |
|------:|------|--------|
| **0–39** | 🟢 Experiment | Тестирование рынка, мониторинг |
| **40–79** | 🟡 Preparing | Готовиться к следующему этапу |
| **80–100** | 🔴 Ready | Genesis **рекомендует** Business Launch |

Пороги зон — в конфиге CEO, не в законе.

---

## Desktop UI (примеры)

### 🟡 Preparing — 72 / 100

```text
Business Readiness

72 / 100

🟡 Preparing

Что рекомендуется:
✓ Подготовить документы (Gewerbe — если применимо)
✓ Подготовить Stripe Business
✓ Проверить юридические страницы
✓ Подготовить уведомление Jobcenter (если применимо)

Ожидает решения CEO
```

### 🔴 Ready — 92 / 100

```text
Business Readiness

92 / 100

🔴 Ready

Рекомендуется перейти к следующему этапу развития.

Рекомендуемые действия:
1. Оформить Gewerbe (если требуется)
2. Уведомить Jobcenter (если применимо)
3. Настроить Stripe Business / KYC
4. Обновить реквизиты на сайте

[ Approve Business Launch ]
```

До нажатия Approve — **ноль** автоматических изменений в системе.

---

## После Approve Business Launch (Law №1 — Act)

Только после CEO — **техническое** (чек-лист Cursor):

1. Env Railway / Vercel по списку CEO
2. Payment Provider в конфиге (interim → Stripe Business)
3. Live keys, webhook
4. Legal pages / Impressum env
5. Smoke: `payment-status`, test payment
6. Запись Decision → Company Brain (Stage 3)

---

## Payment Provider (абстракция)

```text
○ Interim / test stack
○ Stripe Business
```

Переключение = конфиг + env + smoke. **После Approve.**

Mission 1: основной стек **Stripe** (test → live). Не планировать обход ToS платформ.

---

## Конфигурация (пример)

```json
{
  "business_readiness": {
    "zone_green_max": 39,
    "zone_yellow_max": 79,
    "zone_red_min": 80,
    "events": {
      "first_paid_order": 20,
      "second_independent_client": 20,
      "five_sales_per_week": 20,
      "first_subscription": 20,
      "platform_kyc_request": 20,
      "revenue_threshold_usd": 500,
      "revenue_threshold_points": 10,
      "consecutive_sales_days": 3,
      "consecutive_sales_points": 10
    }
  }
}
```

---

## Источники данных

| Событие | Источник |
|---------|----------|
| Заказы, клиенты | `/api/sales/orders`, finance |
| 5 за неделю / дни подряд | агрегация по датам |
| Подписки | Stripe webhooks / billing (будущее) |
| KYC запрос | `payment-status`, manual CEO flag, Stripe dashboard |

**Сейчас:** spec + ручной gate в `Genesis_Progress.md`.  
**После Daily Driver:** виджет score в Desktop.  
**Не сейчас:** auto env / provider switch.

---

## Сценарий CEO

```text
Этап 1 — тест + параллельная подготовка к легальному запуску
Genesis считает score

↓ 40+ Preparing — готовить документы заранее

↓ 80+ Ready — рекомендация, не автоматика

CEO: Gewerbe · Jobcenter · Stripe · Approve Business Launch

↓ Genesis: техническое переключение + smoke
```

---

## Genesis Story

> Почему Score, а не $1500?  
> Бизнес — это подписки, частота, независимые клиенты и сигналы платформы, не одна цифра. Law №1: Genesis рекомендует — CEO подтверждает.

---

## Связанные документы

* `client/docs/Genesis_Laws.md` (Story #4)
* `Genesis_Progress.md`
* `First_Customer_Plan_v1.md`

---

*Не юридическая консультация. Закон и платформы — отдельно от внутреннего score Genesis.*
