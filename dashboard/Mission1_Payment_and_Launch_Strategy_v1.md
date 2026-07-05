# Mission 1 — Payment & Launch Strategy v1

**Дата:** 2026-07-04  
**Для:** CEO (Ramish)  
**Статус:** 📋 Решение CEO — не юридическая консультация

> Genesis **рекомендует и готовит**. CEO **решает** Gewerbe, Jobcenter, платформу.  
> Law №1: Recommend → Approve → Act. Ничего не переключается автоматически.

---

## Две параллельные линии (зафиксировано)

### Линия A — Genesis Company (деньги и опыт)

Сайты · лендинги · боты · автоматизация · услуги · Mission 1 · Acquisition Studio.

**Цель:** первый независимый клиент (EL3) → кейсы → отзывы.

### Линия B — Genesis Platform (строится, не продаётся)

Desktop · Windows · Android · iOS · Linux · Company Brain · Executive · Marketplace.

**Правило:** разработка **не останавливается**. Публикация, подписки, маркетинг платформы — только после **Platform Launch Gate** (после устойчивой Линии A).

```
Genesis Company → услуги → деньги → Gewerbe → Stripe → кейсы
        ↓
Platform Launch Gate (CEO)
        ↓
Windows · Android · iOS · подписки · Marketplace
```

См. `Genesis_Development_Policy.md` — параллельные треки.

---

## Дорожная карта CEO (4 этапа)

| # | Этап | Действие |
|---|------|----------|
| **1** | Platform | Cursor строит каждый день — **не продаёт** |
| **2** | Acquisition Studio | Лиды · анализ · КП · CRM · без массовой автоотправки |
| **3** | Jobcenter | Короткий звонок — **сейчас**, параллельно с этапом 2 |
| **4** | Первый клиент / заказ | Gewerbe → Stripe Live → Approve Business Launch |

**Формулировка Genesis:**

> Компания, которая **помогает владельцу принимать хорошие решения** — не «ИИ, который всё делает».

---

## Три варианта оплаты — сравнение для решения CEO

**⚠️ Заполняйте «?» с Jobcenter / Steuerberater / ToS платформы.** Genesis не заменяет юристов.

| Вопрос | Вариант 1: Gewerbe + Stripe сразу | Вариант 2: Lemon Squeezy (временно) | Вариант 3: Ждать с реальными € |
|--------|-----------------------------------|--------------------------------------|--------------------------------|
| **Можно ли в ситуации Bürgergeld?** | Да, **если** уведомить Jobcenter и соблюдать Freibetrag / правила Nebenerwerb — **уточнить у JC** | Доход всё равно может быть доходом в DE — **уточнить у JC**; MoR не отменяет отчётность | Самый консервативный; спрос не проверяется |
| **Документы** | Gewerbe (или Freiberufler), Steuernummer, Stripe KYC | Аккаунт LS + их KYC; бизнес-статус по их ToS | Нет |
| **Когда нужна регистрация бизнеса** | До или сразу с первым регулярным доходом (DE: gewerblich) | LS ToS может требовать легальный статус — **проверить ToS** | При первом реальном € |
| **Выплаты** | Stripe → ваш банк (DE) | LS → банк / PayPal (зависит от настройки) | — |
| **Риск для Jobcenter** | Низкий **при** своевременном уведомлении | Средний, если доход не задекларирован / скрыт | Минимальный сейчас |
| **Риск ToS платформы** | Низкий при честном KYC | **Средний** — нельзя «притворяться» физлицом, если нужен Gewerbe | Нет |
| **Миграция потом** | Уже на целевом стеке | Клиенты, налоги, история — **ручной** переход на Stripe | Потом с нуля |
| **Совместимость с Genesis сейчас** | ✅ Stripe уже в коде (test → live) | ❌ нет в коде; новый провайдер + gate | ✅ test + ручной outreach |
| **Проверка спроса без вреда** | Stripe **test** + ручные письма | Реальные € без Gewerbe — **риск** | Только интерес, без оплаты |

---

## Рекомендация Genesis (внутренняя, не юридическая)

### Сейчас — «опробовать без вреда»

```
1. Acquisition Studio — outreach, Approve, CRM (уже есть)
2. Stripe TEST — техническая проверка /order (без live €)
3. Jobcenter — один визит/звонок: «планирую Nebenerwerb IT-Dienstleistungen, ab wann melden?»
4. НЕ включать GENESIS_OUTREACH_ENABLED для массовых писем до ясности
5. НЕ принимать live € через обходные схемы
```

**Почему не Lemon по умолчанию:** Mission 1 стек — **Stripe** (`Genesis_Business_Launch_Gate_v1.md`). LS = новый провайдер, ToS-риск, сложный переход. Имеет смысл **только** если Steuerberater/JC + ToS LS явно OK.

**Почему не «Gewerbe завтра без спроса»:** можно, но необязательно до первых сигналов. **Параллельная подготовка** — да (документы, Impressum, Stripe account draft).

### Когда первый реальный €

```
Gewerbe (или уточнённый статус) → Jobcenter melden → Stripe Live → Approve Business Launch → smoke
```

---

## Business Readiness Score — это НЕ лимит Gewerbe

| Что | Кто решает |
|-----|------------|
| Открыть Gewerbe | **CEO в любой момент** (юридически) |
| Когда Genesis **рекомендует** переход стека | Score **80+** + Approve Business Launch |
| Зоны 0–39 / 40–79 / 80–100 | Внутренний мониторинг Genesis |

Пример после открытия Gewerbe, но без клиентов:

```text
Payment Provider: Stripe (test)
Business Readiness: 0 / 100  🟢 Experiment
Recommendation: Continue testing market.
```

После первого live € и второго клиента Score растёт → **Preparing** → Genesis напоминает про live keys, Impressum, JC — **CEO жмёт Approve** → только тогда env меняется.

**Score не запрещает Gewerbe.** Он запрещает Genesis **самому** переключать платежи.

---

## Platform Launch Gate (отдельно от Business Launch Gate)

| Gate | Когда | Что открывает |
|------|-------|----------------|
| **Business Launch Gate** | Устойчивые услуги, score, CEO Approve | Stripe live, реквизиты, legal pages |
| **Platform Launch Gate** | EL3+ · повторяющиеся клиенты · dogfood Desktop | Публикация Client, подписки, Marketplace |

До Platform Launch Gate: Cursor **продолжает** Desktop, mobile scaffold, Brain spec — **без** публичных тарифов платформы.

---

## Практический следующий шаг CEO (эта неделя)

1. ⬜ **Jobcenter** — звонок/визит (этап 3, не ждать 25 контактов)
2. ⬜ Записать ответ JC → закрыть «?» в таблице выше
3. ⬜ 5 лидов через Acquisition Studio (параллельно)
4. ⬜ 0 live € до ясности JC **или** Gewerbe → Stripe live при первом реальном заказе
5. ⬜ Не добавлять Lemon в код без CEO Approve

---

## Правило для Cursor

> **Продолжай строить Platform каждый день.**  
> **Публикация, подписки, платные тарифы, запуск для клиентов — за Platform Launch Gate.**  
> **Mission 1 остаётся главным приоритетом до первого независимого клиента (EL3).**

---

**См. также:** `Genesis_Business_Launch_Gate_v1.md` · `First_Customer_Plan_v1.md` · `Mission_1_5_Business_Acquisition_Studio.md`
