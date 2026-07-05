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

> **Непрерывная разработка** всего, что не требует реальных денег или коммерческой публикации.  
> **Выключено до CEO Approve:** live pay · подписки · Stripe Live · вывод · SaaS launch.  
> **Mission 1** — приоритет до EL3 · **Platform** строится каждый день.

**Readiness ≈ 8.8/10** — `Genesis_Readiness_Scorecard_v1.md`

**Priorities:** 🔴 A (first €) → 🟠 B (Company) → 🔵 C (Platform). Filter + Weekly: `Genesis_Development_Priorities_v1.md`

**Reality First (CEO APPROVED):** `Genesis_CEO_Mandate_Reality_First_v1.md` — done = visible to CEO · USER CAN VERIFY in reports · Reality Audit after major stages · Launcher path until Tauri primary.

**Strategic Review v2:** `Genesis_Strategic_Review_Report_v2.md`

---

## Очередь фундаментов (после RC2)

1. Genesis Client Foundation (Windows-first)
2. Executive Foundation
3. Marketplace Foundation
4. Digital Employees Foundation
5. Business Units Foundation

Каждый — отдельная миссия с чеклистом и audit, без полного продукта до gate.
