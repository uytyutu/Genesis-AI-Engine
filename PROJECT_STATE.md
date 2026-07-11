# Genesis ABOS — Project State

**Version:** 0.4.0 — **Genesis OS** · Business layer (R1)

**Roadmap (стратегия):** [`Docs/ROADMAP.md`](Docs/ROADMAP.md)

**Stage:** **Product Reality** — Memory v1 foundation closed (PASS++++++) · **live use before next architecture**

**Вопрос этапа:** не «что ещё спроектировать?», а **«хочу ли я провести здесь следующий час?»**


**Утро (3 вопроса):** (1) реальные действия за ночь (2) шаг к первому клиенту (3) что лучше, чем вчера

**Readiness (честно):** идея 10/10 · архитектура 9.5/10 · интерфейс 9/10 · **запуск 8/10** (лаунчер + MC стабильны) · **коммерция 3–4/10** (цикл до первого € не пройден)

---

## Genesis OS — закрыт ✅

Launcher · Mission Control · Factory · Finance (display) · утренний CEO-экран · иконка · publish + payment webhook (заготовка)

`py -m pytest tests/ -q` — **91 passed**

---

## Сейчас — Этап R1 (владелец)

**Полный цикл (единственная цель):**

```
Создать → Передать клиенту → Обратная связь → Продать → Первый платёж
```

1. ✅ Запустить Genesis с рабочего стола — **R0 почти закрыт**
2. **Создать продукт** — мастер 4 шага
3. **Factory** — лендинг → превью → ✔
4. **Показать живому человеку** (даже с ноутбука — уже контакт)
5. **R1.5** — когда упрётесь в localhost: публичная ссылка или экспорт

**Известный разрыв:** «Опубликовать» сегодня = localhost. Деньги после **доставки клиенту** (R1.5) и Payment Hub.

**Success:** *«Готов отправить этот сайт первому клиенту»*

**Не делать сейчас:** R5–R14 (Opportunity, Marketing, Executive AI, Investment…) — **дизайн в Roadmap, код после R1**. Полный Cursor Bridge — R8.

**Правило 80/20:** 80% — реализация, 20% — идеи. Roadmap заморожен по объёму.

**Vision Freeze:** новая архитектура **запрещена** до первого клиента или €. Только R1-цикл.

**Доказательство стартапа:** *«Хотя бы один человек готов заплатить за то, что Genesis помог создать.»*

**Owner law:** *Каждый день Genesis полезнее владельцу. До первого € — только то, что ведёт к первому клиенту или улучшает уже созданный продукт.*

**Module law:** *Каждый новый модуль отвечает: «Как он увеличивает стоимость компании?» Нет ответа — не пишем.*

**Payment Hub:** не раньше первого реального клиента — тогда проверяем цепочку целиком.

---

## Genesis Business — дорожная карта

### Сейчас (до первого €)

| Этап | Что | Статус |
|------|-----|--------|
| **1** | Владелец пользуется, собирает фидбек | **СЕЙЧАС** |
| **2** | Первый клиент → первый честный платёж | ждём живого человека |

### После первого реального платежа (порядок фиксирован)

1. **Payment Hub** — реальные платежи, утренний «+49 € на вашем счёте»
2. **Publisher** — публикация на твой хостинг/домен
3. **CRM** — клиенты, сделки, история
4. **AI Sales** — предложения, ответы, сопровождение; крупные сделки → ✔ владелец
5. **Growth Engine** — что реально увеличивает стоимость компании

Не CRM до Payment. Не AI Sales до CRM. Один успешный процесс → масштаб.

| Заготовка сегодня | Статус |
|-------------------|--------|
| Payment Hub UI + webhook | после 1-го клиента |
| Publish (sandbox) | кнопка есть |
| Analyst / Growth UI | сценарии; live после продаж |

---

## Public Vector `/site` — Offline Baseline v1 ✅ (2026-07-09)

| | |
|--|--|
| **Tag** | `offline-baseline-v1` |
| **Acceptance** | `scripts/acceptance_beta_dialogs.py` → **5/5 PASS** on beta |
| **Rule** | Conversation Pipeline changes ship only after **5/5** regression |
| **Next** | Groq A/B — same 5 scenarios; architecture frozen |

**Baseline metrics (offline, beta):** acceptance 5/5 · state errors 0 · D5 no exact repeats · ~290 ms avg turn (sample, `llm_configured=false`)

**Quality gates (порядок):** Engineering (Acceptance 5/5) → Human UX Regression → Product UX Regression → «версия готова».

**Phase 3 — Human & Product UX** (после Groq A/B, не во время freeze): живые фразы, meta/style, сленг — материал в [`USER_FRICTION.md`](USER_FRICTION.md) (только записывать, не чинить сразу).

---

## Product Reality — ACTIVE (2026-07-11, PASS++++++)

| | |
|--|--|
| **Memory v1** | Foundation **closed** — `person_memory/` shipped, no more Memory architecture |
| **Mode** | Architecture → **Product** — changes only if **реальному пользователю станет лучше** |
| **Main test** | *«Хочу ли я провести здесь следующий час?»* — if no, fix product not models |
| **Cycle** | Идея → Реализация → Живое использование → Ощущения → Исправить → Следующий блок |
| **Forbidden** | Reflection v2 · psych profiles · new memory tiers · big new subsystems |
| **North star** | *«Мне удобно работать с Vector»* — not *«надо протестировать»* |

**Сейчас:** CEO живёт с Vector как обычный пользователь (дни). Оцениваем ощущения, не количество функций. Следующий код — только из наблюдений.

---

## Roadmap — порядок этапов (2026-07-11)

| Этап | Статус | Суть |
|------|--------|------|
| **1 Product Reality** | фоном | Vector живой; ощущения; без новых функций |
| **1b Product Definition v1** | **✅ ACCEPTED** | `docs/PRODUCT_DEFINITION_v1.md` — основа M3–M7 |
| **2 Platform Separation M3–M7** | **M3 ACTIVE** | M3.1–M3.3 ✅* · **M3.4 NEXT** |
| **3 Universal Identity** | после M7 | Один аккаунт, все устройства, тот же разговор |
| **4 Commerce layer** | после приложения | CRM · Marketplace · подписки · автоматизация · команды |

### Platform Separation (M3→M7)

- **M3** — разделить Public / Client / CEO
- **M4** — сайт только витрина (услуги, цены, Lite Vector, скачать)
- **M5** — Vector, проекты, голос, документы → в приложение · **CEO UI review каждого экрана**
- **M6** — клиентское API и синхронизация
- **M7** — CEO Workspace внутри приложения, без внешнего браузера

**Психологическая цель:** *«Открыл программу Virtus Core»* — не *«localhost в браузере»*.

**Старт M3:** ACTIVE. **M3.3** ✅ PASS (архитектура) · **окончательный PASS** — после живого просмотра витрины CEO.

**M3.4 NEXT** — Client Workspace Primary (критический этап Migration). Gate: сценарий нового клиента 1→5.

**Playbook:** `docs/M3_PLATFORM_SEPARATION.md`

**Phase 3 backlog (пример):** «Ты чего так общаешься?» → generic fallback; «а чё ты так общаешься» → identity intro — оба мимо вопроса о тоне.

---

## Cycle (единственный — идеальный)

```
Клиент → Диалог → Предложение → Договор → Оплата → Продукт → Публикация → Поддержка → Повтор
```

Сейчас в работе: **Создать → … → Опубликовать → первый клиент → первый €**

---

*Genesis OS закрыт. Начинается Genesis Business.*
