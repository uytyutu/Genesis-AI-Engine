# Genesis Trading Studio — Architecture v1

**Date:** 2026-07-04  
**Status:** **Horizon — architecture only. No implementation.**  
**Principle:** Company OS department · Plan → Approve → Act (Law №1) · **not a casino**  
**Companion:** `Genesis_Trading_Studio_Roadmap_v1.md`

---

## Executive truth (2026-07-04)

| Есть сейчас | Нет сейчас |
|-------------|------------|
| Идея и этот документ | Подключения к биржам (Binance, Bybit, IBKR, …) |
| Место в дереве Company OS | Рыночные данные в реальном времени |
| Законы Genesis применимы к будущему отделу | Движок анализа рынка |
| | Бэктестинг (код) |
| | Риск-менеджер (код) |
| | Исполнение сделок |
| | Торговый журнал (продукт) |
| | Портфель |
| | PnL-мониторинг |

> Trading Studio — **будущий цифровой отдел Genesis**, не отдельная программа и не текущая функция.

---

## Позиция в Company OS

Trading Studio — **один из Studios**, наравне с Development Studio и Acquisition Studio:

```
Genesis Company OS

├── Company
├── Development Studio
├── AI Hub
├── Sales Studio          (Acquisition Studio сегодня)
├── Marketing Studio
├── Executive
├── Finance
│
└── Trading Studio        ← Horizon
      ├── Market Scanner
      ├── Backtesting
      ├── Risk Manager
      ├── Portfolio
      ├── Trade Journal
      ├── AI Analyst
      └── CEO Approvals
```

**Не** standalone trading app. CEO открывает **одно окно Genesis** — Trading Studio как вкладка/отдел.

---

## Философия: не казино

Genesis **никогда** не обещает прибыль и **не торгует сам**.

| Запрещено | Обязательно |
|-----------|-------------|
| Автономные сделки | Объяснение каждой идеи сделки |
| «Бот сам заработает» | Evidence + вероятность |
| Использование денег компании без gate | Расчёт риска до approve |
| Скрытые ордера | Audit log + emergency stop |

**Единственный допустимый поток:**

```
Market Analysis
        ↓
Evidence
        ↓
Probability
        ↓
Risk Manager
        ↓
CEO Approve          ← Law №1
        ↓
Trade (paper → live только после отдельного gate)
```

Никаких самостоятельных сделок. Genesis **предлагает** сделку и **объясняет**, почему считает её обоснованной.

---

## Модули (спецификация, без кода)

### 1. Market Scanner

- Watchlists · секторы · сигналы (volume, trend, news tags)
- **Output:** кандидаты на анализ, не ордера
- Источники данных — **только после Trading Live Gate** (см. Roadmap)

### 2. AI Analyst

- Читает рынок + Brain (прошлые сделки, уроки CEO)
- Формирует **Trade Proposal**: тезис, evidence, counter-arguments
- Использует **AI Hub** routing — не отдельный «торговый ИИ»

### 3. Backtesting

- Стратегия как **декларативный план** (правила входа/выхода)
- Исторические данные · метрики: win rate, max drawdown, Sharpe (опционально)
- **Paper mode по умолчанию** — live только после CEO + gate

### 4. Risk Manager

- Max loss per trade · max daily loss · position size · correlation caps
- **Блокирует** approve, если лимиты нарушены
- Всегда показывает: *«При таком размере позиции максимальный убыток = X»*

### 5. Portfolio

- Позиции · аллокация · exposure по классам активов
- Read-only до live gate; paper portfolio для обучения

### 6. Trade Journal

- Каждая сделка: thesis · evidence · approve timestamp · outcome · lesson
- Питает **Company Brain** — только факты, не фантазии

### 7. CEO Approvals

- Очередь Trade Proposals (как Acquisition approval queue)
- Кнопки: Approve · Reject · Defer · Request more evidence
- Полный audit trail

---

## API contracts (design-only)

Префикс будущего API: `/api/trading/*` — **не регистрировать до gate**.

| Endpoint (draft) | Method | Назначение |
|------------------|--------|------------|
| `/api/trading/status` | GET | Studio version, mode: `design` \| `paper` \| `live` |
| `/api/trading/scanner/watchlists` | GET/POST | Watchlists (paper) |
| `/api/trading/proposals` | GET | Очередь предложений |
| `/api/trading/proposals` | POST | Создать proposal (AI Analyst) |
| `/api/trading/proposals/{id}/approve` | POST | CEO approve → paper/live per gate |
| `/api/trading/backtests` | POST | Запуск бэктеста |
| `/api/trading/portfolio` | GET | Позиции |
| `/api/trading/journal` | GET | Журнал сделок |
| `/api/trading/risk/limits` | GET/PUT | Лимиты (CEO only) |

**Mode flag обязателен:** `TRADING_MODE=off|paper|live` — default `off`.

---

## Интеграции (заблокированы до gate)

| Провайдер | Тип | Gate |
|-----------|-----|------|
| Binance / Bybit / … | Crypto spot/futures | Trading Live Gate |
| Interactive Brokers | Equities/options | Trading Live Gate |
| Market data feeds | Real-time quotes | Paper Gate (read-only historical first) |

**Сейчас:** никаких API keys, SDK, websocket в репозитории.

---

## Связь с Genesis Laws

| Law | Trading Studio |
|-----|----------------|
| №1 Plan → Approve → Act | Каждая сделка — proposal → CEO |
| №2 One Window | Отдел внутри Genesis, не отдельный терминал |
| №3 Evidence | Журнал + метрики бэктеста как доказательства |
| №4 Company learns | Уроки из сделок → Brain (facts only) |
| №5 Owner capital safe | Деньги на счетах CEO; лимиты; emergency stop |

---

## UI (wireframe-level, не реализация)

```
┌─────────────────────────────────────────────────────────┐
│ Trading Studio                    Mode: OFF (Horizon)   │
├──────────────┬──────────────────────────────────────────┤
│ Market       │  Trade Proposal #42                      │
│ Scanner      │  BTC/USDT · Long · 4h                    │
│              │  Thesis: …                                 │
│ Backtests    │  Evidence: …  P(win): 58%                │
│              │  Risk: max loss €120 (2% portfolio)      │
│ Portfolio    │  [Approve] [Reject] [More evidence]      │
│              │                                          │
│ Journal      │                                          │
│ Risk         │                                          │
└──────────────┴──────────────────────────────────────────┘
```

---

## Что разрешено проектировать сейчас

- Этот документ и Roadmap
- API-контракты (draft)
- Математические модели (в документах)
- UI/UX спецификации
- Risk policy (текст)
- Paper trading flow (на бумаге)

## Что запрещено до отдельного gate

- Реальные сделки
- Подключение бирж
- Автоторговля
- Использование денег компании
- Любой код, отправляющий ордер

**Trading Live Gate** — отдельное CEO Approve после: Gewerbe · продажи услуг · daily Genesis · Company Brain · Executive Dashboard.

---

*Horizon · architecture only · Mission 1 и первые клиенты — приоритет #1*
