# Genesis Trading Studio — Roadmap v1

**Date:** 2026-07-04  
**Status:** **Horizon — roadmap only. No implementation.**  
**Decision:** Trading Studio **не отменяется** — **переносится в Horizon**  
**Companion:** `Genesis_Trading_Studio_Architecture_v1.md`

---

## CEO decision (2026-07-04)

> Genesis строится как **компания**. Сначала — доказать, что умеет зарабатывать на сайтах, AI-решениях, автоматизации и цифровых услугах. Trading Studio — **будущий цифровой отдел**, не сейчас.

**Причина отложить:** трейдинг отнимет месяцы и **не приблизит первого клиента**.

---

## Приоритеты Genesis (зафиксировано)

| # | Направление | Статус |
|---|-------------|--------|
| 1 | **Mission 1** — первые клиенты | 🔴 NOW |
| 2 | Development Studio | 🔄 build |
| 3 | AI Hub | 🔄 build |
| 4 | Desktop Daily Driver | 🔄 build |
| 5 | Company Brain | 🔄 facts only |
| 6 | Executive | 🔄 foundation |
| 7 | Consumer Platform | 🔒 после dogfood |
| 8 | **Trading Studio** | 🔒 **Horizon** |

**Фильтр:** если задача не помогает первому клиенту или качеству продукта как Company OS → **Horizon**.

---

## Что есть vs чего нет (честно)

### ✅ Уже есть (экосистема, не трейдинг)

- Архитектурные документы Company OS
- AI Hub (каркас)
- Development Studio (начало)
- Mission Control · Company OS
- Acquisition Studio (продажа услуг)
- Desktop Foundation

### ❌ Нет (Trading Studio)

- Биржи и брокеры
- Real-time market data
- Market analysis engine (код)
- Backtesting engine (код)
- Risk manager (код)
- Order execution
- Trade journal (продукт)
- Portfolio view
- PnL monitoring

**Итог:** идея + архитектура v1. **Не рабочая функция.**

---

## Gates (когда начинать строить)

Trading Studio **не стартует в коде**, пока не выполнены **все**:

| # | Условие | Статус |
|---|---------|--------|
| G1 | Gewerbe / legal clarity | ⬜ |
| G2 | Продажи услуг идут (не ноль pipeline) | ⬜ |
| G3 | Genesis используется CEO **ежедневно** (6–8 h dogfood) | ⬜ |
| G4 | Company Brain на **фактах** (не пустой) | ⬜ |
| G5 | Executive Dashboard **работает** | ⬜ |
| G6 | **CEO Approve** — открыть Trading Studio build | ⬜ |

До G6 — только документы и дизайн (этот roadmap + architecture).

---

## Sub-gates (внутри Trading Studio)

### Paper Trading Gate

Разрешает **после G6 + CEO Approve:**

- UI Trading Studio (read-only + paper)
- Исторические данные (не live keys)
- Backtesting offline
- Trade journal (paper trades)
- Risk calculator

**Запрещено:** live keys · real money · auto-execution

### Trading Live Gate

Разрешает **только после Paper Gate + отдельный CEO Approve:**

- Подключение бирж / брокера (read + trade API)
- Live market data
- Исполнение **после** CEO Approve на каждую сделку
- PnL monitoring

**Запрещено навсегда без явного изменения Laws:**

- Полностью автономная торговля
- Обещания прибыли в UI
- Торговля деньгами компании без лимитов и audit

---

## Roadmap phases (после gates — не сейчас)

### Phase 0 — Design (разрешено сейчас)

- [x] Architecture v1
- [x] Roadmap v1
- [ ] UI mockups (Figma / docs)
- [ ] Risk policy document
- [ ] API contract freeze (draft)

**Запрещено:** код, зависимости бирж, env keys

### Phase 1 — Paper Studio (после G6)

- Trading Studio shell в Genesis (One Window)
- Market Scanner (historical / delayed data)
- Backtesting v0
- Risk Manager (rules engine, no orders)
- Trade Journal (paper)
- CEO Approval queue

### Phase 2 — AI Analyst (после Paper stable)

- Trade Proposals через AI Hub
- Evidence pack per proposal
- Integration с Company Brain (lessons)

### Phase 3 — Live (после Trading Live Gate)

- Exchange/broker adapters (one at a time)
- Live portfolio + PnL
- Per-trade CEO Approve → order
- Emergency stop + daily limits

### Phase 4 — Maturity (horizon+)

- Multi-strategy portfolio
- Correlation risk
- Automated **scanning** only (never auto-trade)

---

## Разрешено проектировать сейчас

| Область | Пример |
|---------|--------|
| Архитектура | `Genesis_Trading_Studio_Architecture_v1.md` |
| Roadmap | этот документ |
| Интерфейс | wireframes, nav placement |
| Модули | Scanner, Journal, Risk — spec |
| API-контракты | draft `/api/trading/*` |
| Риск-менеджмент | policy text |
| Математика | position sizing formulas (docs) |
| Backtesting | strategy DSL spec |
| Portfolio | data model spec |
| Paper Trading | user flow |

## Запрещено до gate

| Область | |
|---------|--|
| Реальные сделки | ❌ |
| Подключение бирж | ❌ |
| Автоторговля | ❌ |
| Деньги компании | ❌ |
| Код исполнения ордеров | ❌ |

---

## Trading flow (неизменный)

```
Market Analysis
        ↓
Evidence
        ↓
Probability
        ↓
Risk Manager
        ↓
CEO Approve
        ↓
Trade
```

Genesis Laws применяются **полностью**. Trading Studio — не исключение.

---

## Связь с доходами Genesis

**Главные источники дохода (сейчас):**

1. Продажа сайтов
2. Продажа AI-ботов
3. Разработка программ
4. Perfect Pallet
5. Genesis Platform (услуги)

Trading Studio **не заменяет** ни один пункт до подтверждения Company на рынке.

---

## Cursor rule

> Trading Studio **не забирает время у Mission 1**.  
> Документы v1 — OK. Код — только после G6 + CEO Approve.  
> Если сомнение — **Horizon**.

> **Ни один новый цифровой отдел** (включая Trading Studio, Marketplace, Executive, Digital Employees) **не должен замедлять Mission 1 или Development Studio.**

**Два фильтра** (обязательны до любой новой функции):

1. Приближает первого клиента или улучшает Genesis?
2. Не замедлит Mission 1 или Development Studio?

Оба «да» — можно. Иначе → Horizon.

См. `Genesis_CEO_Mandate_Reality_First_v1.md`.

*Horizon · roadmap only · первые клиенты и реальная выручка — приоритет #1*

---

## CEO Review — APPROVED (2026-07-04)

Reality Audit принят. Mandate: `Genesis_CEO_Mandate_Reality_First_v1.md`.

**Следующий Reality Audit** — после следующего крупного этапа (Dev Studio daily-use · Tauri build · Mission 1 milestone).
