# Virtus Core — Master Specification
## Volume II: Factory, Workspace, UX, решения CEO, Roadmap, оценка

**Версия:** 2026-07-10  
**Том I:** [VIRTUS_CORE_MASTER_SPEC_VOLUME_I.md](./VIRTUS_CORE_MASTER_SPEC_VOLUME_I.md)

---

# Содержание Volume II

11. [Factory](#11-factory)
12. [Workspace](#12-workspace)
13. [UX](#13-ux)
14. [Все решения CEO](#14-все-решения-ceo)
15. [Полный Roadmap](#15-полный-roadmap)
16. [Что уже реализовано](#16-что-уже-реализовано)
17. [Что ещё отсутствует](#17-что-ещё-отсутствует)
18. [Главные ошибки проекта](#18-главные-ошибки-проекта)
19. [Уникальность Virtus Core](#19-что-делает-virtus-core-уникальным)
20. [Финальная оценка](#20-финальная-оценка)

---

# 11. Factory

## 11.1 Что такое Factory в Genesis

**Factory** — подсистема создания **продаваемых лендингов** для Mission 1 (350–1200 €). Отделена от **Execution Layer** (публичный Vector), но использует общий `landing_builder.py`.

## 11.2 Что уже умеет (v0.1 pragmatic)

| Этап | Модуль | Статус |
|------|--------|--------|
| Analyze description | `factory/analyzer.py` | ✅ |
| Generate HTML | `landing_builder.py` | ✅ |
| Validate | `validator.py` | ✅ |
| Improve (patches) | `landing_patcher.py` | ✅ |
| Owner approve | MC UI | ✅ |
| Export ZIP | R1.5 delivery API | ✅ |
| Publisher | sandbox / localhost | ⚠️ partial |

**Skills registry:** `landing-page-v1` — **active**; `telegram-bot-v1` — **stub disabled**.

## 11.3 Что должен уметь (Vision)

По `docs/FACTORY_FRAMEWORK_ARCHITECTURE_v0.1.md` и `SKILLS_PLATFORM.md`:

```text
Builder → Validator → Packager → Publisher
```

Семейства skills (план):
- Websites ✅
- Telegram bots ⏸
- Desktop/Mobile apps
- AI Agents, SaaS, Automations, Dashboards, APIs
- Chrome extensions, WordPress, Shopify, Discord plugins

**Директория `factories/`:** README only — «Phase 2 Telegram Bot Factory first».

## 11.4 Конечный продукт Factory

**Mission 1:** CEO создаёт лендинг за минуты → валидирует → отдаёт клиенту ZIP + message.

**Долгосрочно:** автономная фабрика ищет ниши → создаёт продукты → ставит в очередь CEO approve → публикует после Payment Hub.

**Сегодня:** автономность честно **~25–35%** — не раздувать.

## 11.5 Factory vs Execution — критическое различие

| Вопрос | Factory | Execution |
|--------|---------|-----------|
| Кто пользуется? | CEO (owner) | Public visitor |
| Где UI? | MC `/create` | `/site` |
| Оплата? | `/order` пакеты | free chat + paid packages |
| Workspace? | sandbox product_id | execution workspace_id |

Объединение в один UX — **post-WC=1 UX Release**.

---

# 12. Workspace

## 12.1 Концепция (Vision)

**Co-Creation Workspace** (`VIRTUS_WORKSPACE_ARCHITECTURE_DIRECTIVE.md`):

| Уровень | Содержит |
|---------|----------|
| **Platform** | Virtus Core — не модифицируется AI |
| **Workspace** | Проект пользователя — файлы, артефакты |
| **Project** | Конкретная задача внутри workspace |

AI **никогда** не меняет platform code без owner gate.

## 12.2 Текущая реализация (Execution)

```text
memory/execution/workspaces/{workspace_id}/
  files/           # report.html, index.html, README…
  artifacts/       # doc-*.json, site-*.json, preview/
  logs/
  tasks/           # reserved
  memory/          # reserved
```

**Visitor map:** `visitor_id → workspace_id` для Zero Context (Gate 5).

## 12.3 Как должен выглядеть (Level B, post-WC=1)

```text
┌─────────────────────────────────────────────────────────┐
│  WORKSPACE (главный экран)                              │
│  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ Последняя работа │  │ Артефакты                   │  │
│  │ PDF ✓ → Site ✓   │  │ report.html, index.html   │  │
│  └──────────────────┘  └─────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Прогресс задач                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                              ┌─────────────────────┐   │
│                              │ Vector (панель)     │   │
│                              │ чат справа          │   │
│                              └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Сегодня на `/site`:** placeholder «Пока пусто» — Level A PASS, Level B не начат.

## 12.4 Как пользователь должен работать

**Целевой flow:**
1. Открывает workspace → видит **последнюю работу**
2. Кликает артефакт → профессиональный viewer (не raw md)
3. Выбирает **следующий шаг** из intent-actions
4. Чат — **помощник**, не центр вселенной

---

# 13. UX

## 13.1 Desktop — Public `/site`

| Элемент | Реализовано | Должно быть |
|---------|-------------|-------------|
| Welcome + starters | ✅ Level A | — |
| Navigation ☰ · VECTOR · + | ✅ | — |
| Composer в карточке | ✅ | — |
| ExecutionResultPanel | ✅ groups artifacts/next | — |
| Workspace panel | ⚠️ placeholder | full artifact browser |
| Report viewer | ⚠️ opens HTML in new tab | in-app professional viewer |
| «What Vector Can Do» | ✅ via «Что умеешь?» | dedicated screen post-WC=1 |
| i18n ru/en/de | ✅ | — |

## 13.2 Mobile — Public `/site`

| Элемент | Статус |
|---------|--------|
| Responsive layout | ✅ partial |
| Compact composer | ✅ `minimalMobile` |
| History sidebar | ⚠️ friction logged USER_FRICTION |
| Touch targets on CTAs | ✅ improved in ExecutionResultPanel |
| Workspace-first mobile | ❌ Level B |

**Принцип CEO:** mobile проектируется **отдельно**, не уменьшенная копия ПК — **не выполнено**.

## 13.3 Tablet

Отдельного дизайна нет — наследует responsive web.

## 13.4 Desktop — Mission Control (Owner)

| Surface | Статус |
|---------|--------|
| Launcher → MC | ✅ ~8/10 launch |
| Morning CEO screen | ✅ |
| Factory `/create` | ✅ |
| Acquisition `/acquisition` | ✅ manual |
| `/order` flow | ✅ test Stripe |
| Execution capabilities API | ✅ owner only |
| Dedicated execution UI in MC | ❌ |

**Routes без MC chrome:** `/site`, `/pricing`, `/services`, legal.

## 13.5 Tauri Desktop (`client/desktop/`)

| Stage | Статус |
|-------|--------|
| 2.5 Daily Driver | ⚠️ in progress |
| Home, Chat, Projects, Settings | ✅ |
| Command Palette Ctrl+K | ✅ |
| Dev Studio scaffold | ✅ |
| Monaco, git, terminal | ❌ Stage 3 |
| Release `.exe` primary path | ⬜ CEO gate |
| Perfect Pallet integration | ⚠️ handoff only |

**Приоритет CEO path:** Launcher → MC **первичен**; Tauri secondary.

## 13.6 UX Quality Stack

```text
Engineering (pytest, acceptance 5/5)
  → Human UX Regression
    → Product UX Regression
      → «Версия готова»
```

**Проблема 2026-07-09:** engineering green ≠ owner satisfaction (USER_FRICTION).

---

# 14. Все решения CEO

## 14.1 Genesis Laws v1.1 (FROZEN 2026-07-04)

1. **Plan → Approve → Act**
2. **One Window** — один Genesis для пользователя
3. **Dogfood First**
4. **Evidence Before Automation**
5. **Human Accountability**

## 14.2 Reality First Mandate (2026-07-04)

- Done = **visible** in running app
- USER CAN VERIFY в каждом отчёте агента
- First Client Filter до первого €
- Priority: Mission 1 → Dev Studio → AI Hub → Desktop → Brain → … → Trading (Horizon)

## 14.3 Stability Before Features (2026-07-05)

- No new features until daily green launch
- Launcher owns lifecycle — не Cursor, не Git

## 14.4 Vision Freeze

До первого клиента / €:
- ❌ новые departments, engines, screens
- ✅ только полный цикл к первому клиенту

## 14.5 Vector RC1 Rules (2026-07-10)

| # | Rule |
|---|------|
| 1 | Одна capability = законченная ценность |
| 2 | Пирамида ценности |
| 3 | Capability Graph |
| 4 | Reuse артефактов |
| 5 | Explain Reuse |
| 6 | Zero Context |
| 7 | Trust Before Automation (Commit 4+) |
| 8 | **Product Truth — только `/site`** |

**RC1 freeze:** любая новая идея отклоняется до WC=1, кроме fix Gates 1–5.

## 14.6 Human Gates (Vector)

| Gate | Сценарий | Статус |
|------|----------|--------|
| 1 Documents | README | ✅ PASS |
| 2 Sites | стоматология site | ✅ PASS |
| 3 Analysis | PDF → artifacts | 🔄 CEO |
| 4 Reuse | site ← analysis | 🔄 CEO |
| 5 Zero Context | browser close | 🔄 CEO |

**WC=1** когда Gates 3,4,5 = CEO PASS на beta.

## 14.7 Critical UX

- **Level A:** ✅ closed 2026-07-10
- **Level B:** workspace-first — **после WC=1**

## 14.8 Commercial gates

```
Jobcenter clarity → market test → Gewerbe при реальном заказе → Approve launch
```

- Payment Hub / Stripe Live — **после** первого реального клиента
- `GENESIS_OUTREACH_ENABLED` off до Jobcenter clarity

## 14.9 Brand (2026-07-08 CLOSED)

Virtus Core / Vector — публично. Genesis.exe — внутренне OK.

## 14.10 Governance IDs (referenced, `ceo_decisions.json` отсутствует в repo)

- `dec-2026-07-05-reality-over-features`
- `dec-2026-07-05-no-auto-spend-without-budget`
- `dec-2026-07-05-ceo-strategic-reserve`
- `dec-2026-07-05-media-engine-architecture-freeze`
- `dec-2026-07-05-finance-security-vision-freeze`
- `dec-2026-07-05-algorithm-intelligence-research-freeze`

## 14.11 KPI

| KPI | Вопрос |
|-----|--------|
| Hours Saved | Сколько часов снято? |
| Reuse Score | Сколько capability переиспользовано? |
| **Workflow Completion** | End-to-end без копирования? |
| Opportunities → € | Не vanity counts |

## 14.12 Agent / Cursor rules

- One heavy build per turn
- No push without owner approval (git-workflow)
- Kernel frozen — no Guardian in kernel
- No new .md unless CEO asks (исключение: этот Master Spec)

---

# 15. Полный Roadmap

## 15.1 Жёсткий порядок (`docs/ROADMAP.md`)

```text
1. Genesis opens daily without Cursor     ← ~закрыто
2. Cycle: product → human → feedback
3. First honest €                         ← СЕЙЧАС
4. Roadmap blocks one at a time
```

## 15.2 R-cycle (выборка)

| ID | Задача | Условие старта | Статус |
|----|--------|----------------|--------|
| R0 | Stable green launch | — | ✅ ~ |
| R0.5 | Cursor clipboard | R0 | ✅ |
| **R1** | Owner product cycle | R0 | **NOW** |
| R1.5 | ZIP delivery | R1 | ✅ |
| R2 | Capability Evolution UI | R1.5 | ❌ |
| R3 | Live AI journal | R2 | ❌ |
| R5 | Opportunity Engine | R1 + product | Horizon |
| R7 | CRM | Payment Hub + client | Horizon |
| R8 | Cursor Bridge auto | R1–R3 | Horizon |
| R12+ | Marketing, Executive, Media | milestones | design |

## 15.3 Vector RC1 → WC=1 (сейчас)

```text
Gate 3 PASS → Gate 4 PASS → Gate 5 PASS → WC=1
```

## 15.4 После WC=1 (фиксированный порядок)

```text
1. UX Release (Level B) — workspace visible, NOT new capabilities
2. Commit 4 — Trust Before Automation (diff → confirm → fix)
3. Document revision v2 (CEO product direction)
4. New capabilities по одной: presentation, proposal, financial model…
```

## 15.5 После первого € (Mission 1 commercial)

```text
Payment Hub → Publisher (real hosting) → CRM → AI Sales → Growth Engine
```

## 15.6 Долгосрочно (до «финального Virtus Core»)

| Год+ | Возможности |
|------|-------------|
| EL3 | First client, Gewerbe, live payments |
| EL4 | CRM, repeat clients, case studies |
| EL5 | Subscriptions Pro/Creator/Business |
| EL6 | Multi-tenant, SLA, Enterprise |
| Vision | Full AI Factory, departments, Marketplace, Game Studio, Trading (gated) |

**Не по коммитам — по продуктовым возможностям.**

---

# 16. Что уже реализовано

## 16.1 Честный инвентарь — WORKS

| Область | Доказательство |
|---------|----------------|
| Launcher + MC boot | CEO daily path, auto-fix |
| Public site RC1/RC2 | Release audit PASS |
| Vector chat Brain | beta dialogs, workforce |
| Execution Gates 1–2 | tests + CEO PASS |
| Execution Gate 3 code | PDF→artifacts, beta mechanics PASS |
| Reuse code | tests workflow analyze→site |
| Factory landing | MC create + ZIP |
| `/order` test checkout | Stripe test mode |
| Offline baseline | 5/5 acceptance |
| Level A UX | CEO PASS 6/6 |
| Work-agent UX slice | post_analysis_actions, report.html |
| 37+ execution tests | pytest green |

## 16.2 WORKS PARTIALLY

| Область | Gap |
|---------|-----|
| Gate 3 quality | heuristic reports, not investor-grade LLM |
| Gate 4–5 | code yes, CEO PASS no |
| Publish | localhost only |
| Commerce | test Stripe, no EL3 |
| Mobile UX | sidebar, workspace invisible |
| Tauri daily driver | gate not closed |
| Autonomy | 25–35% honest |
| Multi-model orchestration | only Workforce failover, not specialized pipeline |
| OCR | scanned PDFs fail |

## 16.3 ARCHITECTURE ONLY (код есть, user value нет)

| Item |
|------|
| 20 planned capabilities in catalog |
| TaskPlannerV2 multi-step + deployment step |
| suggest_next_capabilities UI hook |
| AI Hub provider registry entries (planner, embeddings) |
| Learning layer jsonl |
| Planning layer stub |
| capability_graph planned nodes |
| Platform subscription tiers on `/pricing` (display) |
| Digital Employee strategy docs |
| Marketplace vision |

## 16.4 IDEA ONLY (docs)

Trading Studio, Media Engine, full CRM, native mobile apps, Game Studio pipeline, Warehouse dept automation, Consumer Mode, CEO Mode full.

---

# 17. Что ещё отсутствует

## 17.1 Критичное для Mission 1

| # | Отсутствует |
|---|-------------|
| 1 | **Первый реальный платящий клиент (EL3)** |
| 2 | Jobcenter clarity (Bürgergeld + IT Nebengerbe) |
| 3 | Gewerbe + Stripe Live KYC |
| 4 | Gate 3–5 CEO PASS на beta |
| 5 | Live webhook production |
| 6 | Real Publisher (domain/hosting) |

## 17.2 Критичное для продукта Vector

| # | Отсутствует |
|---|-------------|
| 1 | Исправление документа → v2 file |
| 2 | LLM-powered analysis (optional quality tier) |
| 3 | OCR |
| 4 | Workspace-first UI (Level B) |
| 5 | In-app report viewer |
| 6 | Multi-step orchestration visible to user |
| 7 | Presentation, proposal, financial model capabilities |
| 8 | Trust/diff flow (Commit 4) |

## 17.3 Критичное для платформы

| # | Отсутствует |
|---|-------------|
| 1 | Payment Hub |
| 2 | CRM |
| 3 | AI Sales automation |
| 4 | Opportunity Engine live data |
| 5 | Real learning loop (not just jsonl) |
| 6 | Multi-user / teams |
| 7 | SLA / Enterprise |

**Без приукрашивания:** большая часть «энциклопедии услуг» — **Vision**. Реально работают **4 execution capability + Factory landing + Brain chat**.

---

# 18. Главные ошибки проекта

## 18.1 Стратегические

| Ошибка | Урок |
|--------|------|
| Год architecture без EL3 | Vision Freeze, P13, First Client Filter |
| Сотни идей в roadmap без одной цепочки WC=1 | Vector RC1 — 5 Gates only |
| Simulated readiness / autonomy inflation | Honest 25–35%, beta Product Truth |
| Три продукта в голове (Launcher/MC/Tauri) | One Window mandate |

## 18.2 Архитектура опередила продукт

| Симптом | Пример |
|---------|--------|
| 24 capability в каталоге, 4 работают | capabilities.py |
| Brain v3 + 15 layers, user sees chat | Execution bypass underused until Gate 3 |
| Factory Framework doc vs pragmatic v0.1 | DESIGN ≠ shipped |
| TaskPlanner references deployment | executor doesn't exist |
| AI Hub registry without wiring | provider_registry stubs |

## 18.3 Продукт опередил UX

| Симптом | Пример |
|---------|--------|
| Workspace exists, user sees empty placeholder | Level B not shipped |
| Reports as files in new tab | not «бизнес-заключение» feeling until report.html |
| «Создать сайт» as only CTA | fixed 2026-07-10 intent actions |
| Engineering 5/5, owner «что-то не так» | USER_FRICTION acceptance gap |

## 18.4 Нарушения философии (исправленные)

| Было | Стало |
|------|-------|
| PDF → Brain essay | PDF → Execution artifacts |
| UI locale overrides document language | document-first locale |
| Chat-only product surface | ExecutionResultPanel + CTAs (partial) |

## 18.5 Что нужно изменить

1. **Закрыть WC=1** прежде чем любая новая capability
2. **UX Release** сразу после — workspace видим
3. **Commit 4** — document revision как killer feature
4. **Один workflow за раз** — не параллелить Factory expansion + Vector expansion + Tauri
5. **Beta = truth** — local pytest ≠ PASS
6. **Восстановить `ceo_decisions.json`** или единый decision log

---

# 19. Что делает Virtus Core уникальным

*Не маркетинг — только реальные или достижимые отличия.*

## 19.1 vs ChatGPT / Claude / Gemini / Perplexity

| | Они | Virtus Core (реально / цель) |
|---|-----|------------------------------|
| Выход | текст | **файлы в workspace** (✅ partial) |
| Память | thread / account | visitor memory + workspace (✅) |
| Workflow | нет | capability chain PDF→site (✅ code) |
| Бизнес focus | general | landing packages, acquisition (✅) |
| Честность | — | Product Truth, no income promises (✅) |

**Сегодня проигрываем** в качестве анализа и UX polish. **Выигрываем** в наличии execution path + commercial shell (order, packages).

## 19.2 vs Copilot / Cursor

| | Cursor | Virtus Core |
|---|--------|-------------|
| Аудитория | developer | **business owner** |
| IDE | yes | no — concierge + MC |
| Handoff | — | clipboard cursor (✅) |

Не конкурент Cursor в коде — **комplement**: CEO uses both.

## 19.3 vs Lovable / Bolt / Replit Agents

| | Builders | Virtus Core |
|---|----------|-------------|
| Site gen | strong | template landing (weaker) |
| Full stack app | yes | planned only |
| Business plan analysis | no | ✅ unique (heuristic) |
| Owner gating / EU legal | rare | ✅ design center |
| Reuse chain | weak | ✅ graph design |

## 19.4 vs Manus / general agents

| | Agents | Virtus Core |
|---|--------|-------------|
| Autonomous loops | marketing focus | **CEO gates** — less autonomous, more trustworthy |
| Workspace | varies | explicit execution workspace |
| Specialization | general | **narrow Mission 1** focus (landings + docs) |

## 19.5 Реальное УТП (если довести до WC=1 + Commit 4)

> **«Загрузил бизнес-план → получил заключение + сайт + исправленный документ — без копирования между инструментами»**

Этого **ни у кого из списка нет** как одного workflow. Пока **не доказано на beta** — это гипотеза УТП, не факт.

---

# 20. Финальная оценка

*Независимый CTO + Product Director. Честно.*

## 20.1 Сильные стороны

| # | Сила |
|---|------|
| 1 | **Ясная конституция** — WHY.md, freezes, gates |
| 2 | **Execution layer реально работает** — не только слайды |
| 3 | **Capability Graph** — правильная модель reuse |
| 4 | **Brain v3** — зрелая conversational stack |
| 5 | **Commercial shell** — order, packages, acquisition |
| 6 | **CEO discipline** — Product Truth, USER CAN VERIFY |
| 7 | **Honest scoring** — commerce 3–6/10 admitted |
| 8 | **Recent product clarity** — work agent direction |

## 20.2 Слабые стороны

| # | Слабость |
|---|----------|
| 1 | **Нет EL3** — главный risk |
| 2 | **WC≠1** — продукт не закрыт |
| 3 | **UX ≠ architecture** — workspace invisible |
| 4 | **Analysis quality** — heuristic, not pro |
| 5 | **20/24 capabilities fake** — catalog inflation |
| 6 | **Two RC1 meanings** — confusion risk |
| 7 | **Deploy/ephemeral storage** — beta multi-instance |
| 8 | **Mobile neglected** |
| 9 | **ceo_decisions.json missing** |
| 10 | **Orchestration vision >> implementation** |

## 20.3 Оценки (10-балльная шкала, 2026-07-10)

| Измерение | Оценка | Комментарий |
|-----------|--------|-------------|
| Vision clarity | 9/10 | Отличные docs |
| Architecture depth | 8/10 | Много scaffolding |
| **Shipped user value** | **5/10** | 4 caps + chat |
| UX polish | 5/10 | Level A only |
| Commercial readiness | 4/10 | No EL3 |
| Code quality / tests | 8/10 | pytest, acceptance |
| Focus discipline | 7/10 | RC1 freeze helps |
| **World-class potential** | 7/10 | If WC=1+Commit4 |

## 20.4 Что нужно для мирового уровня

### Фаза A — 30 дней (Mission 1)
1. CEO PASS Gates 3–5 на beta
2. WC=1 declared
3. Первый outreach → первый €
4. Jobcenter + Gewerbe path started

### Фаза B — 90 дней (Product)
1. UX Release Level B
2. Commit 4 document revision
3. LLM tier for analysis quality
4. OCR for scanned PDFs
5. In-app workspace viewer

### Фаза C — 12 месяцев (Platform)
1. Payment Hub live
2. 3+ capability chains proven with paying clients
3. CRM + delivery automation
4. Specialized model orchestration (behind Vector)
5. First subscription tier with real billing

### Фаза D — 24+ месяцев (Vision)
1. AI Factory multi-skill
2. Departments (dev, warehouse, marketing)
3. Marketplace
4. Multi-tenant Enterprise

## 20.5 Одно предложение

**Virtus Core — один из немногих проектов с правильной *архитектурой намерения*, но ещё не с правильным *доказательством на рынке*.** Следующий шаг — не больше docs и не больше catalog entries. Следующий шаг — **один человек платит € за завершённый workflow на beta**, и всё остальное строится от этого факта.

---

# Приложения

## A. Карта файлов SSOT

| Тема | Путь |
|------|------|
| Конституция | `WHY.md` |
| Состояние | `PROJECT_STATE.md` |
| Vector RC1 | `VECTOR_CAPABILITIES.md` |
| Roadmap | `docs/ROADMAP.md` |
| Mission 1 ops | `dashboard/Genesis_Progress.md` |
| Vision workspace | `docs/VIRTUS_WORKSPACE_ARCHITECTURE_DIRECTIVE.md` |
| Vision north star | `docs/VIRTUS_CORE_NORTH_STAR_DIRECTIVE.md` |
| Execution code | `dashboard/backend/app/execution/` |
| Brain code | `dashboard/backend/app/integration/genesis_brain/` |
| Factory code | `dashboard/backend/app/factory/` |
| Public UI | `dashboard/frontend/app/components/GenesisConcierge.tsx` |
| Quality audit | `dashboard/backend/scripts/gate31_quality_audit.py` |

## B. Глоссарий

| Термин | Значение |
|--------|----------|
| **Vector** | Публичный AI-агент Virtus Core |
| **Virtus Core** | Публичный бренд платформы |
| **Genesis** | Внутреннее имя OS / exe |
| **WC** | Workflow Completion |
| **EL3** | Первый реальный клиент |
| **Gate** | Human verification checkpoint |
| **Capability** | Атомарная исполняемая способность |
| **Product Truth** | Ценность только на `/site` |
| **Horizon** | Идеи без кода до gate |

## C. Как обновлять этот документ

1. После каждого CEO PASS/FAIL Gate — обновить §14, §16
2. После новой READY capability — §6, §7, §16
3. После EL3 — пересмотреть Vision Freeze, §15
4. Не дублировать — **этот Master Spec = индекс истины**; детали остаются в канонических файлах

---

**Конец Volume II**

*Virtus Core Master Specification — CEO Directive 2026-07-10*  
*Создано Cursor Agent на основе полного сканирования репозитория, канонических docs, кода execution/brain/factory, и истории решений CEO.*
