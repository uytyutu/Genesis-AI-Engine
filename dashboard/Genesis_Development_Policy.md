# Genesis — Политика непрерывной разработки

**Версия:** 1.0 · 2026-07-04

---

## Принцип

> **Genesis развивается непрерывно.**
>
> Пока CEO решает внешние вопросы (Gewerbe, Stripe, юридические формальности), Cursor **не ждёт**, а строит фундамент следующих компонентов по приоритету.
>
> Новые возможности **не публикуются как готовые**, пока не завершены и не проверены. Они **не должны ухудшать** стабильность Mission 1.

**Не:** «Отложить до EL3.»  
**Да:** «Разрабатывать поэтапно, не отвлекаясь от качества текущего релиза.»

---

## Параллельные треки

| Трек | Фокус | Публикуется когда |
|------|--------|-------------------|
| **A — Company** | Mission 1, услуги, Acquisition Studio, RC | Первый клиент EL3 |
| **B — Platform** | Desktop, Windows, mobile, Brain, Executive | **Platform Launch Gate** (после устойчивой A) |
| **C — Horizon** | Marketplace, подписки платформы, Digital Employees | После Platform Launch Gate |

**Две линии:** Company зарабатывает · Platform строится. См. `Mission1_Payment_and_Launch_Strategy_v1.md`.

---

## Цикл каждого модуля

```
1. Спроектировать
2. Создать основу
3. Довести до качества
4. Следующий модуль
```

Не десятки тысяч строк сразу — **один фундамент за раз**.

---

## Gate на рынок (CEO)

```
Jobcenter (ясность) → Studio + Platform build → первый клиент → Gewerbe → Stripe Live → Approve Business Launch
```

Разработка Platform **не останавливается**. На рынок выходит только **проверенное** (услуги — Mission 1; SaaS — Platform Launch Gate).

---

## Правило Cursor (Mission 1 era)

> **Максимально подготовить Genesis к первому публичному запуску** — реализуя всё, что можно **качественно проверить без реальных пользователей**.  
> **Не:** «ждать Invoice #0001 для всего подряд.»  
> **Да:** Reality over Features — не тратить время на то, что невозможно проверить до реальной эксплуатации.

### Три типа функций (CEO · 2026-07-05)

| | Когда | Примеры |
|---|--------|---------|
| 🟢 **Тип 1 — сейчас** | Не зависят от реальных пользователей; не замедляют Mission 1 | UI/UX, `/site`, AI Concierge (rule-based), `/order`, Mission Control, тесты, perf, i18n, безопасные рефакторинги, стабильность, dogfooding |
| 🟡 **Тип 2 — после первых пользователей** | Нужны реальные диалоги, конверсия, поведение | Sales AI self-learning, Algorithm Intelligence, Media learning, динамическое ценообразование, рекомендации по конверсии |
| 🔴 **Тип 3 — после бизнеса** | Нужны клиенты, деньги, юридическая база | Stripe automation, налоги, мультивалюта, Voice AI, корп. тарифы, авто-счета, полная бухгалтерия |

**Продолжай реализовывать**, если функция:

- повышает качество первого публичного релиза;
- не требует недоступных production-данных;
- проверяется локально (тесты, dogfooding);
- не замедляет Mission 1;
- не нарушает архитектуру (Garage → Validation → Production).

**CEO не согласовывает каждое безопасное улучшение.** Garage + тесты + quality gates; в Production — только прошедшее проверки и реально улучшающее продукт.

**Выключено до CEO Approve:** live pay · подписки · Stripe Live · вывод · SaaS launch.  
**Mission 1** — приоритет до EL3 · **Platform** строится каждый день.

**Readiness ≈ 8.8/10** — `Genesis_Readiness_Scorecard_v1.md`

**Priorities:** 🔴 A (first €) → 🟠 B (Company) → 🔵 C (Platform). Filter + Weekly: `Genesis_Development_Priorities_v1.md`

**Reality First (CEO APPROVED):** `Genesis_CEO_Mandate_Reality_First_v1.md` — done = visible to CEO · USER CAN VERIFY in reports · Reality Audit after major stages · Launcher path until Tauri primary.

**Pre-launch implementation (CEO · 2026-07-05):** три типа функций — см. § «Три типа функций» выше. Цель: законченный продукт к запуску, не MVP с дырами; обучение на выдуманных данных — после реальных клиентов.

**Strategic Review v2:** `Genesis_Strategic_Review_Report_v2.md`

---

## Очередь фундаментов (после RC2)

1. Genesis Client Foundation (Windows-first)
2. Executive Foundation
3. Marketplace Foundation
4. Digital Employees Foundation
5. Business Units Foundation

Каждый — отдельная миссия с чеклистом и audit, без полного продукта до gate.
