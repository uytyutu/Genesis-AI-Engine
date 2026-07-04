# Genesis Business Launch Gate v1.2

**Версия:** 1.2 · 2026-07-04  
**Статус:** 📐 **FROZEN** до первых реальных пользователей — не добавлять события, только веса в конфиге  
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

Бизнес определяется **не одной суммой**, а набором **фиксированных** событий v1.2.  
**Не добавлять новые события** до реальных пользователей — только менять **веса** в конфиге по опыту (Law №4).

| Событие (фиксированный набор v1.2) | Вес по умолчанию |
|------------------------------------|-----------------:|
| Первый оплаченный заказ | 20 |
| Второй **независимый** клиент | 20 |
| 5+ продаж за 7 дней | 20 |
| Первая активная подписка | 20 |
| KYC / tax verification от платформы | 20 |

Через год опыт может показать, что второй клиент важнее KYC — **меняем веса, не архитектуру:**

```text
BusinessReadinessWeights (пример после 12 мес.)

first_sale        = 15
second_client     = 30   ← сильный сигнал по опыту
five_sales_week   = 20
subscription      = 25
kyc               = 10   ← редко на раннем этапе
```

### Зоны

| Score | Зона | Смысл |
|------:|------|--------|
| **0–39** | 🟢 Experiment | Тестирование рынка, мониторинг |
| **40–79** | 🟡 Preparing | Готовиться к следующему этапу |
| **80–100** | 🔴 Ready | Genesis **рекомендует** Business Launch |

Пороги зон — в конфиге CEO, не в законе.

---

## Desktop UI — объяснимость обязательна

CEO видит **не только число**, но и **почему** (доверие к системе).

### Пример — Ready с разбором

```text
Business Readiness

82 / 100

Почему?

✓ Первый оплаченный заказ        (+20)
✓ Второй независимый клиент      (+30)
✓ Повторные продажи за неделю    (+20)
✗ Подписка ещё отсутствует       (0)
✗ KYC от платформы не запрошен   (0)

Рекомендация

Компания выглядит готовой к следующему этапу развития.

[ Approve Business Launch ]
```

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
    "weights": {
      "first_paid_order": 20,
      "second_independent_client": 20,
      "five_sales_per_week": 20,
      "first_subscription": 20,
      "platform_kyc_request": 20
    }
  }
}
```

**v1.2 rule:** менять только `weights` и пороги зон — не список событий — до post-EL3 review.

---

## Операционная философия (не Laws)

Пауза в расширении философии. Накапливать **реальные истории** (`Daily_Driver_Journal.md`, Genesis Stories).

1. Не автоматизировать догадки.
2. Автоматизировать только проверенные процессы.
3. ИИ рекомендует — человек решает.
4. Новое сначала внутри Genesis Company.
5. **Каждое решение объяснимо** — что и почему.

---

## Источники данных

| Событие | Источник |
|---------|----------|
| Заказы, клиенты | `/api/sales/orders`, finance |
| 5 за неделю / дни подряд | агрегация по датам |
| Подписки | Stripe webhooks / billing (будущее) |
| KYC запрос | `payment-status`, manual CEO flag, Stripe dashboard |

**Сейчас:** spec **FROZEN** · ручной gate · журнал · Mission 1 evidence.  
**После Daily Driver + реальные пользователи:** виджет с explainability.  
**Не сейчас:** новые события score · auto env switch.

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
