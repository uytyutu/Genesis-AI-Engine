# Virtus Core — Master Specification
## Volume I: История, философия, услуги, сценарии, архитектура ядра

**Версия документа:** 2026-07-10  
**Статус:** Single Source of Truth (SSOT) — CEO Directive  
**Аудитория:** новая команда, CEO, архитекторы, продукт  
**Связанные тома:** [Volume II](./VIRTUS_CORE_MASTER_SPEC_VOLUME_II.md) (Factory, UX, Roadmap, оценка)

> **Цель:** если завтра исчезнет вся команда, по этому документу можно восстановить полную картину Virtus Core — от замысла до текущего кода.

**Канонические первоисточники (живые):**
- `WHY.md` — конституция
- `PROJECT_STATE.md` — текущее состояние
- `VECTOR_CAPABILITIES.md` — RC1 Vector
- `docs/ROADMAP.md` — R-цикл
- `dashboard/Genesis_Progress.md` — Mission 1 ops
- `docs/VIRTUS_*_DIRECTIVE.md` — замороженное видение

---

# Содержание Volume I

1. [История проекта](#1-история-проекта)
2. [Полная философия](#2-полная-философия)
3. [Все идеи за всё время](#3-все-идеи-за-всё-время)
4. [Полный каталог услуг](#4-полный-каталог-услуг)
5. [Все пользовательские сценарии](#5-все-пользовательские-сценарии)
6. [Все Capability](#6-все-capability)
7. [Capability Graph](#7-capability-graph)
8. [Все модели ИИ](#8-все-модели-ии)
9. [Brain](#9-brain)
10. [Execution Layer](#10-execution-layer)

---

# 1. История проекта

## 1.1 Зачем создавался Virtus Core

**Genesis / Virtus Core** — не «ещё один чат-бот» и не «конкурент ChatGPT». Это попытка построить **операционную систему цифровой компании**: штаб, который управляет продуктами, клиентами, AI-командой и автоматизацией — при постоянном контроле владельца (CEO).

**North Star (конституция, `WHY.md`):**
> Постоянно искать законные способы создавать ценность, за которую люди готовы платить.

**Практическая формулировка Mission 1 (2026):**
> Каждый день Genesis полезнее владельцу — и ближе к первому реальному платежу.

**Genesis does not exist to write code.** Genesis exists to help the owner create value for clients and scale the business.

Проект родился из пересечения:
- личной потребности владельца (цифровой бизнес, Jobcenter/Bürgergeld контекст в Германии);
- амбиции «фабрики цифровых продуктов»;
- осознания, что один человек не может держать в голове десятки направлений (сайты, игры, склад, CRM, маркетинг) без **системы**, которая **выполняет работу**, а не только советует.

## 1.2 Genesis → Virtus Core

| Этап | Название | Смысл |
|------|----------|-------|
| Ранний | Genesis AI Engine | Репозиторий, backend, «мозг», launcher |
| 2026-07-04 | Genesis OS v0.4 | Launcher + Mission Control + Factory + Finance display |
| 2026-07-08 | **Virtus Core / Vector** | Публичная идентичность: launcher, MC, `/site`, Tauri UI |
| Внутреннее | Genesis.exe, genesis-* | Допустимы в коде; пользователь видит Virtus Core / Vector |

**Ребрендинг CLOSED (2026-07-08):** новые branding-проходы запрещены без запроса CEO. Иконки: `scripts/generate_virtus_brand_assets.py` через `launcher/build.ps1`.

## 1.3 Основные этапы развития

### Фаза 0 — Идея и архитектурный взрыв (до 2026-07-04)
- Множество vision-документов: Brain, Factory, Marketplace, Studios, Trading, Media Engine
- Риск: **архитектура опережала продукт** — год идей без первого €
- Реакция: **Foundation closed**, **Vision Freeze**, **Principle 13** (evolution through evidence)

### Фаза 1 — Foundation closed (2026-07-04)
- 13 принципов достаточны; новые принципы = нарушение P13
- **Genesis Laws v1.1 FROZEN:** Plan→Approve→Act, One Window, Dogfood First, Evidence Before Automation, Human Accountability
- **CEO Mandate Reality First:** Done = visible; USER CAN VERIFY обязателен
- Chief Architect covenant: до EL3 — только путь к первому платящему партнёру

### Фаза 2 — Stability Before Features (2026-07-05)
- Заморозка фич до стабильного `Genesis.exe → Backend → Frontend → MC HTTP 200`
- Recurring P0: backend жив / frontend мёртв
- **Reality over Features** — validated outcomes, не счётчик модулей

### Фаза 3 — Public site RC1/RC2 (2026-07-04)
- `/site`, `/order`, `/services`, `/pricing`, legal pages
- Stripe test mode, Resend email
- RC1 audit: сначала FAIL (legal 404), после deploy **PASS**
- RC2 **PASS** (`3b49f34`)

### Фаза 4 — Conversation Pipeline Offline Baseline (2026-07-09)
- Tag `offline-baseline-v1`, commit `315ac16`
- Acceptance **5/5 PASS** на beta — обязателен для любых изменений pipeline

### Фаза 5 — Vector RC1 + Virtus Core product truth (2026-07-10)
- **Vector RC1 FREEZE:** разработка capability на паузе до Workflow Completion = 1
- Critical UX Level A — **CEO PASS** (6 пунктов)
- Gate 3 mechanics PASS на beta; quality + Gates 4–5 — CEO verify
- Product direction: Vector = **рабочий агент**, не чат

## 1.4 Evidence Levels (EL)

| EL | Значение | Genesis сегодня |
|----|----------|-----------------|
| EL0 | Идея | Много horizon-идей |
| EL1 | Purpose/Vision | ✅ |
| EL2 | Mission 1 tech | ✅ (~8.8/10 code) |
| EL3 | **Первый реальный клиент / €** | ⬜ **цель Mission 1** |
| EL4+ | Масштаб, CRM, подписки | Horizon |

**Переход EL2→EL3** = неизвестный человек платит реальные деньги (не test Stripe).

## 1.5 Долгосрочная цель

**Virtus Core мирового уровня** — платформа, где:
- пользователь **получает готовую работу** (документы, сайты, отчёты, исправления), а не советы;
- **Workspace** — главное рабочее пространство;
- **Vector** — единый агент, внутри — оркестрация специализированных моделей (невидимо для пользователя);
- **Capability Graph** связывает артефакты в цепочки без копирования;
- владелец сохраняет **gates** на деньги, публикацию, юридические риски.

**Не цель:** обогнать ChatGPT в болтовне. **Цель:** выполнять бизнес-работу end-to-end.

---

# 2. Полная философия

## 2.1 Что такое Virtus Core

**Virtus Core** — операционная система цифровой компании + публичный AI-агент **Vector** для клиентов на `/site`.

Три слоя восприятия:

| Слой | Для кого | Что видят |
|------|----------|-----------|
| **Public** | Клиент, тестировщик | Vector на beta `/site` — чат + артефакты + кнопки |
| **Owner** | CEO | Genesis.exe → Mission Control — Factory, Acquisition, Finance |
| **Internal** | Разработка | Brain, Execution, Capability Graph, Workforce |

## 2.2 Что Virtus Core НЕ должен быть

- ❌ Гарант дохода без реальных покупателей
- ❌ «Деньги из воздуха» / поиск лазеек
- ❌ Автономные контракты, публикация, траты без CEO gates
- ❌ Симуляция активности вместо реальной работы
- ❌ Ещё один ChatGPT с другим скином
- ❌ Генератор Markdown-простыней вместо **бизнес-заключений и файлов**
- ❌ Архитектурный музей — 100 модулей без одного завершённого workflow

## 2.3 Что Virtus Core ДОЛЖЕН быть

- ✅ **Director of universal AIs** — дирижёр, не один LLM
- ✅ **Work agent:** «Я выполнил работу» > «Вот отчёт»
- ✅ **Co-Creation Workspace** — «Мы построили это вместе», не «AI сгенерировал»
- ✅ **Evidence before automation** — сначала ручной proof, потом автоматизация
- ✅ **Product Truth** — ценность доказывается на `/site`, не в dev-only API
- ✅ **Законная ценность** — GDPR, Impressum, Jobcenter-совместимость, без спама

## 2.4 Место Vector

**Vector** — публичное лицо Virtus Core:
- ассистент на `/site`;
- точка входа в Execution Layer (документы, анализ, сайты);
- в будущем — панель рядом с Workspace, не «приложение-чат».

Vector **не показывает** отдельные модели (OCR, Legal, Financial). Пользователь видит **одного агента**.

## 2.5 Как продукт должен ощущаться

**Целевое ощущение (CEO, 2026-07-10):**
> «Я получил профессиональное бизнес-заключение» — не «я получил Markdown».

**Эмоциональная цель (`VIRTUS_CORE_NORTH_STAR_DIRECTIVE.md`):**
> «We built this together» — не «AI generated it».

**Ежедневный путь CEO:**
```
Genesis.exe → Запустить → 🟢 готов → Mission Control
```
Владелец **никогда** не обязан открывать PowerShell для daily work.

---

# 3. Все идеи за всё время

Классификация: **Implemented** | **Planned** | **Vision** | **Frozen** | **Rejected**

## 3.1 Implemented (реально в коде + проверяемо)

| Идея | Где | Примечание |
|------|-----|------------|
| Launcher zero-friction | `launcher/`, `Genesis.exe` | npm/.next/ports auto-fix |
| Mission Control web | `dashboard/frontend` | Owner dashboard |
| Public `/site` Vector chat | `GenesisConcierge.tsx` | ru/en/de, voice |
| Brain v3 pipeline | `genesis_brain/` | Think→Decide→LLM→Calibrate |
| Workforce Director | `workforce_director.py` | Groq→Gemini→… failover |
| Factory landing v1 | `factory/landing_builder.py` | 350–1200 € packages |
| Execution: filesystem_write | Gate 1 | README в workspace |
| Execution: generate_site | Gate 2 | HTML/CSS + preview |
| Execution: analyze_business_document | Gate 3 | PDF→reports (heuristic) |
| Workspace reuse | Gate 4–5 code | analysis→site |
| R1.5 ZIP delivery | export API | client handoff |
| Acquisition Studio UI | `/acquisition` | manual segments |
| `/order` + test Stripe | sales_order_service | не live KYC |
| Offline conversation baseline | acceptance 5/5 | frozen tag |
| Critical UX Level A | VECTOR_CAPABILITIES | CEO PASS |
| Work-agent UX (3.1+) | post_analysis_actions | intent CTAs |
| Brand Virtus Core | launcher, site, Tauri | CLOSED |
| Cursor clipboard handoff | `/cursor` | R0.5 |
| TTS multi-provider | `genesis_tts/` | OpenAI, ElevenLabs, etc. |

## 3.2 Planned (в roadmap / каталоге, не READY)

| Идея | Слот | Блокер |
|------|------|--------|
| Gate 3–5 CEO PASS | RC1 | beta verify |
| UX Release Level B | post-WC=1 | workspace-first UI |
| Commit 4 Trust | diff→confirm→fix | после WC=1 |
| generate_presentation | capability_graph | нет executor |
| generate_proposal / PDF | capability_graph | нет executor |
| revise_document → v2 PDF | product direction | Commit 4+ |
| filesystem_read via chat | executor есть | нет routing |
| TaskPlanner multi-step | planner.py | deployment stub |
| DOCX / Vision / Audio intake | feature_registry | нет wiring |
| OCR для scanned PDF | — | не начато |
| CRM | R7 | после Payment Hub |
| Payment Hub live | post-first-€ | Gewerbe, KYC |
| Publisher real hosting | post-Payment Hub | localhost gap |
| Opportunity Engine R5 | roadmap | после R1 |
| Cursor Bridge R8 | roadmap | после daily use |
| R2 Capability Evolution UI | roadmap | не начато |
| Telegram bot factory | skills_registry stub | disabled |
| Dev Studio IDE | Tauri Stage 3 | Monaco, git, terminal |
| Platform subscriptions | `/pricing` display | не billing |

## 3.3 Vision (документы, без кода)

| Идея | Документ |
|------|----------|
| Co-Creation Workspace полный | VIRTUS_WORKSPACE_ARCHITECTURE |
| Commerce & Delivery lifecycle | VIRTUS_COMMERCE_DELIVERY |
| Multi-model orchestration pipeline | CEO product direction 2026-07-10 |
| Genesis HQ multi-project | ROADMAP § HQ |
| Digital Employee departments | DIGITAL_EMPLOYEE_STRATEGY |
| Marketplace / Store | MARKETPLACE.md |
| Game Studio Unity pipeline | roadmap |
| Trading Studio | Horizon |
| Executive AI | Horizon |
| Marketing Engine R12 | Horizon |
| Media Engine | frozen directive |
| Finance Engine | frozen directive |
| Algorithm Intelligence research | frozen |
| Consumer subscriptions tiers | pricing hypothesis |
| Android/iOS native apps | capability map slots only |
| AI Factory полный | SKILLS_PLATFORM |

## 3.4 Frozen (не трогать до gate)

| Freeze | До когда | Что запрещено |
|--------|----------|---------------|
| **Vision Freeze** | первый клиент / € | новые departments, engines, screens |
| **Vector RC1** | WC=1 | новые capability, Commit 4, архитектура |
| **Foundation** | EL3 | новые принципы, thinking-layer docs |
| **Brand** | CEO ask | rebranding passes |
| **Offline baseline** | новый acceptance | pipeline changes без 5/5 |
| **Media/Finance/Algorithm** | revenue milestones | код |
| **Payment Hub / Gewerbe** | реальный заказ | live Stripe |
| **Kernel** | всегда | Guardian/money logic в kernel |

## 3.5 Rejected / отложено навсегда (пока нет EL3)

| Идея | Причина |
|------|---------|
| «Sites + Android + Marketplace + Video AI» одновременно | P13 — слишком много сразу |
| Simulated KPIs / fake portfolio | Roadmap law |
| Auto-spend без бюджета | CEO decision 2026-07-05 |
| Real investments без CEO | CEO decision |
| Brain essay для PDF анализа | Product Truth fix 2026-07-10 |
| Три отдельных продукта (Launcher/MC/Tauri) | Reality First — один Genesis |
| Cursor запускает uvicorn/npm | Launch Architecture v2 |

---

# 4. Полный каталог услуг

## 4.1 Документы

| Услуга | Что делает | Для кого | Результат | Capability |
|--------|------------|----------|-----------|------------|
| Создать файл (README) | Пишет файл в workspace | Founder, тест RC1 | `README.md` открывается | `filesystem_write` ✅ |
| Анализ бизнес-плана | PDF/txt → SWOT, readiness, отчёты | Предприниматель | Executive Summary, бизнес-заключение HTML, JSON | `analyze_business_document` ✅ |
| Исправить документ v2 | Правки → новый PDF/DOCX | Предприниматель | BUSINESS PLAN v2 | `revise_document` ⏸ |
| Перевод документа | Язык → язык | Экспорт | Переведённый файл | `translate_document` ⏸ |
| Версия для банка | Формат под кредит | SME | Bank package | `bank_package` ⏸ |
| Презентация | Слайды из отчёта | Investor pitch | `presentation.md` | `generate_presentation` ⏸ |
| Proposal | Коммерческое предложение | B2B sales | `proposal.pdf` | `generate_proposal` ⏸ |

## 4.2 Бизнес

| Услуга | Статус | Capability / модуль |
|--------|--------|---------------------|
| Бизнес-консультация (чат) | ✅ Brain | Workforce LLM |
| Финансовая модель Excel | ⏸ | `generate_excel` |
| Investment readiness check | ⏸ частично в отчёте | heuristic readiness score |
| Site audit (внутренний) | ✅ Acquisition | `acquisition_studio_service` |
| Opportunity scoring | Vision R5 | — |

## 4.3 Маркетинг

| Услуга | Статус |
|--------|--------|
| Landing 350/650/1200 € | ✅ Factory + `/order` |
| SEO drafts | Vision |
| Paid ads | 🟡 CEO gate always |
| Growth Engine R12 | Horizon |
| Email outreach | Acquisition manual |

## 4.4 Разработка

| Услуга | Статус | Capability |
|--------|--------|------------|
| Сайт-лендинг (execution) | ✅ | `generate_site` |
| Сайт (owner factory) | ✅ | `factory_service` |
| Generate App/API/DB | ⏸ catalog | planned |
| Dev project / diff / tests | ⏸ graph node | `dev_project` |
| Cursor handoff | ✅ clipboard | — |
| Docker build/run | ⏸ | planned |
| Terminal in sandbox | ⏸ | planned |
| Deployment live | ⏸ | `deployment` stub |

## 4.5 Web / Mobile

| Услуга | Статус |
|--------|--------|
| Public `/site` | ✅ |
| Responsive mobile web | ⚠️ partial (sidebar friction) |
| Tauri desktop | ⚠️ dev works, daily driver gate open |
| Native Android/iOS | Vision (icons only) |

## 4.6 Игры / 3D / Unity

| Услуга | Статус |
|--------|--------|
| Perfect Pallet Studio | Отдельный repo; Genesis metadata + handoff |
| Game test builds | Vision post R4–R6 |
| 3D / Warehouse viz | Vision Digital Warehouse dept |

## 4.7 AI Factory / Automation

| Услуга | Статус |
|--------|--------|
| landing-page-v1 skill | ✅ active |
| telegram-bot-v1 | stub disabled |
| Skills platform families | planned in SKILLS_PLATFORM |
| Task queue async | ⏸ `task_queue` |

## 4.8 CRM / Finance / Voice / Media

| Направление | Статус |
|-------------|--------|
| CRM | Horizon R7 |
| Payment Hub | post-first-€ |
| Finance display MC | ✅ honest zeros |
| Voice TTS | ✅ |
| Voice STT in chat | partial / planned |
| Media Engine | Frozen |

## 4.9 Warehouse / Perfect Pallet

**Digital Warehouse Department** (strategy doc): inventory, logistics, reports — **Vision**, post-EL3.

**Perfect Pallet:** отдельная игра; Genesis orchestrates test-build gate, не непрерывный auto-merge.

---

# 5. Все пользовательские сценарии

## 5.1 RC1 — «Загрузил бизнес-план → анализ → сайт»

```
Пользователь: открывает beta.genesis-ai-engine.com/site
↓
Загружает PDF бизнес-плана
↓
«Проанализируй мой бизнес-план»
↓
Vector (Execution, не Brain):
  • pypdf извлекает текст (до 50 стр.)
  • document_intelligence: классификация, SWOT, readiness (rule-based, без LLM)
  • workspace: executive_summary.md, report.md, report.html, document_structure.json
↓
Чат: work-agent сообщение + кнопки:
  • Результат: Summary, Бизнес-заключение
  • Следующие шаги: по типу документа (сайт — опция, не единственная)
↓
«Создай сайт» (Gate 4)
↓
generate_site + workspace_reuse(analysis artifacts)
↓
Explain Reuse в ответе
↓
Preview index.html
```

**Модели:** Execution path — **без LLM**. Brain не вызывается при PDF+analyze.

## 5.2 «Хочу открыть кофейню»

**Сегодня (Brain path):**
```
Пользователь: «Хочу открыть кофейню в Берлине»
↓
GenesisAIService → Brain (нет execution match)
↓
ThinkingEngine → ExecutiveBrain → Workforce Director
↓
LLM (Groq/Gemini/…) + Memory + Knowledge + Personality
↓
Консультация, вопросы, факты в memory
↓
НЕ создаётся автоматически: бизнес-план, сайт (нужны явные команды)
```

**Целевое (Vision):**
```
Тот же запрос
↓
Vector определяет intent: new_business_cafe
↓
Цепочка: brief → financial model → site → presentation
↓
Workspace показывает прогресс
↓
Пользователь получает пакет файлов
```
**Разрыв:** orchestration и большинство capability — Planned.

## 5.3 «Создай сайт стоматологии» (Gate 2)

```
Пользователь: «Создай сайт стоматологии»
↓
bridge._parse_site_request → generate_site
↓
landing_builder: niche dental → HTML/CSS
↓
workspace/files + artifacts/preview/
↓
CTA: открыть preview
```

## 5.4 Owner: Factory cycle

```
CEO: Genesis.exe → MC → /create
↓
Описание бизнеса → Factory analyze → HTML
↓
Validator → Improve (patches)
↓
CEO Approve → Export ZIP (R1.5)
↓
Publish = sandbox/localhost (gap)
```

## 5.5 First client commercial

```
Клиент: /site → консультация → /order
↓
Выбор пакета 350–1200 €
↓
Test Stripe checkout
↓
/status order page
↓
CEO manual delivery (ZIP, message)
```
**EL3 блокер:** нет live €, Gewerbe, Jobcenter clarity.

## 5.6 Zero Context (Gate 5)

```
Сессия 1: анализ + workspace_id в visitor_workspaces.json
↓
Закрыть браузер
↓
Сессия 2: тот же visitor_id → тот же workspace
↓
«Создай сайт» → reuse без повторных вопросов
```

---

# 6. Все Capability

**Источник:** `dashboard/backend/app/execution/capabilities.py`  
**READY** = `availability: available` + executor registered.

## 6.1 READY (4)

| ID | Назначение | Produces | Consumes | Gate |
|----|------------|----------|----------|------|
| `filesystem_write` | Запись файла | `files/{path}` | user.goal | 1 |
| `filesystem_read` | Чтение файла | content | path | — (no chat route) |
| `analyze_business_document` | Анализ PDF/txt | report, summary, structure JSON | upload, goal | 3 |
| `generate_site` | Лендинг | HTML, CSS, preview, manifest | goal, optional analysis | 2,4 |

## 6.2 PLANNED (20 в каталоге, без executor)

`analyze_pdf`, `analyze_docx`, `analyze_image`, `analyze_audio`, `generate_app`, `generate_api`, `generate_database`, `generate_presentation`, `generate_excel`, `browser_search`, `browser_navigation`, `git_commit`, `git_branch`, `docker_build`, `docker_run`, `terminal_command`, `deployment`, `email_send`, `calendar`, `task_queue`

**При попытке run:** ExecutionManager → `blocked`.

## 6.3 IN PROGRESS

| Capability | Состояние |
|------------|-----------|
| analyze quality (3.1) | heuristic reports, HTML conclusion |
| post_analysis_actions | intent CTAs, horizon stubs |
| workspace reuse | code + tests, CEO Gate 4–5 |

## 6.4 VISION (graph nodes без executor)

`generate_proposal`, `generate_presentation` (graph), `dev_project`

---

# 7. Capability Graph

**Файл:** `capability_graph.py`

## 7.1 Ready chain

```text
user.goal ──► filesystem_write ──► files/*

uploads/* + goal ──► analyze_business_document ──►
    document_structure.json
    executive_summary.md
    report.md / report.html
    artifacts/doc-*.json
         │
         ▼ (optional reuse)
goal + analysis ──► generate_site ──►
    brief.md, index.html, style.css
    preview/, site_manifest.json
```

## 7.2 Planned chain (reference)

```text
analyze ──► generate_site ──► generate_presentation ──► generate_proposal
```

`workflow_chain_open_clinic` — эталонная цепочка для клиники.

## 7.3 Building blocks

| Artifact | Версия | Назначение |
|----------|--------|------------|
| `document_structure.json` | v2 | reuse для site, future proposal |
| `site_manifest.json` | v1 | reuse для presentation |
| `report.md` / `report.html` | — | human consumption |
| `executive_summary.md` | — | 30-sec decision |

## 7.4 suggest_next_capabilities

Реализовано в коде, **не подключено к UI** (TaskPlannerV3).

---

# 8. Все модели ИИ

## 8.1 Подключённые LLM (Workforce)

| Employee | Model | Endpoint | Tier |
|----------|-------|----------|------|
| groq | llama-3.3-70b-versatile | api.groq.com | Free-first |
| gemini | gemini-2.0-flash | Google OpenAI-compat | Free-first |
| openrouter | gemini-2.0-flash-001 | openrouter.ai | Free-first |
| ollama | llama3.2 | localhost:11434 | Local |
| openai | gpt-4o-mini | api.openai.com | Premium |
| anthropic | claude-3.5-haiku | via OpenRouter | Premium |
| deepseek | deepseek-chat | api.deepseek.com | Premium |
| genesis-local | brief_speech | rule-based | Always on |

**Failover:** groq → gemini → openrouter → ollama → genesis-local

**Premium:** только при `GENESIS_PREMIUM_LLM=1` или hard task heuristics.

## 8.2 Специализированные (план / частично)

| Роль | Технология | Статус |
|------|------------|--------|
| OCR | — | ❌ не реализован |
| PDF text | pypdf | ✅ Brain 5pp, Execution 50pp |
| Document intelligence | rule-based NLP | ✅ Execution only |
| Reasoning | GoalAnalysis + ExecutiveBrain | ✅ pre-LLM |
| Financial analysis | heuristics in document_intelligence | ⚠️ не LLM |
| Legal check | — | Vision |
| Writing/Editor | LLM via Workforce | ✅ Brain path |
| Coding | Workforce task=code | ✅ |
| Voice TTS | OpenAI, ElevenLabs, Google, Azure | ✅ отдельный модуль |
| Voice STT | — | Planned |
| Vision | feature_registry | Planned |
| Planning | GenesisPlanningLayer | stub |
| QA | factory/validator | ✅ owner path |
| Deployment | capability stub | ❌ |

## 8.3 Целевая оркестрация (CEO Vision, не реализована)

```text
OCR → Structure → Classify → Financial → Legal → Editor → QA → New Document → Verify → User
```
Пользователь видит только **Vector**.

---

# 9. Brain

**Версия:** genesis-mind-v3.0

## 9.1 Pipeline

```text
Think → Decide → LLM (+ Personality, Knowledge, Memory) → Calibrate → Critique
```

Thinking Brief — **internal only**, никогда в API.

## 9.2 Слои (активные)

| Слой | Функция |
|------|---------|
| ThinkingEngine | ThinkingBrief |
| ExecutiveBrain | action: answer/advise/explore/… |
| GoalAnalysisLayer | real_goal classification |
| ReasoningLayer | intent, role, strategy |
| PlanningLayer | **stub** — site/launch hints |
| EmotionalIntelligence | mood hints |
| ConversationState | facts: country, budget, niche |
| MemoryLayer | long-term visitor JSON |
| KnowledgeLayer | catalog, pricing, tone |
| PersonalityLayer | constitution, vendor scrub |
| WorkforceManager + Director | LLM routing |
| HumanCalibration | anti-template |
| SelfCritique | polish offline path |
| AI Jury | optional second opinion |
| LearningLayer | **stub** — jsonl logs |

## 9.3 Memory

| Store | Path |
|-------|------|
| User memory | `genesis_brain/users/{visitor_id}.json` |
| Chat sessions | ChatSessionStore |
| Workforce quotas | `workforce/quotas.json` |
| Execution workspace map | `execution/visitor_workspaces.json` |

## 9.4 Brain vs Execution

| | Brain | Execution |
|---|-------|-----------|
| Триггер | default chat | regex + attachments |
| Выход | текст в чате | workspace artifacts |
| LLM | да | нет (analysis) |
| provider | groq, etc. | `execution` |

**Invariant:** PDF analyze → Execution, не Brain essay (2026-07-10).

---

# 10. Execution Layer

## 10.1 Компоненты

| Компонент | Файл | Роль |
|-----------|------|------|
| Capability Registry | capabilities.py | каталог 24 capability |
| Capability Graph | capability_graph.py | produces/consumes |
| ExecutionManager | manager.py | plan → permissions → steps → verify |
| ExecutionWorkspaceStore | workspace.py | files/logs/artifacts |
| ExecutionLogStore | log_store.py | jsonl |
| Bridge | bridge.py | /site chat wiring |
| TaskPlannerV2 | planner.py | owner preview only |
| Permissions | permissions.py | read/write/filesystem/… |
| Verifier | verifier.py | required_output_keys |
| post_analysis_actions | post_analysis_actions.py | intent CTAs |
| report_render | report_render.py | HTML conclusion |
| document_intelligence | document_intelligence.py | rule analysis |
| preview | preview.py | serve workspace files |

## 10.2 Workspace layout

```text
execution/workspaces/{id}/
  files/          # user artifacts
  logs/
  tasks/
  artifacts/      # manifests, preview/
  memory/
```

## 10.3 Bridge routing

| Pattern | Capability |
|---------|------------|
| «Что умеешь?» | capability_registry |
| «Создай README» | filesystem_write |
| «Создай сайт» | generate_site |
| PDF + analyze | analyze_business_document |
| PDF only attach | → analyze (block Brain) |

## 10.4 Два пути Factory vs Execution

| | Owner Factory | Vector Execution |
|---|---------------|------------------|
| Entry | MC `/create` | `/site` chat |
| Storage | sandbox/{product_id} | execution/workspaces |
| Site builder | landing_builder | landing_builder (shared lib) |
| Audience | CEO | Public visitor |

## 10.5 API

- `GET /api/public/execution/workspace/{id}/files/{path}`
- `GET /api/public/execution/preview/{id}/`
- `GET /api/owner/execution/capabilities`

---

**Конец Volume I** → продолжение в [Volume II](./VIRTUS_CORE_MASTER_SPEC_VOLUME_II.md)

*Документ сгенерирован Cursor Agent по CEO Directive 2026-07-10. При расхождении с кодом приоритет у beta Product Truth и `VECTOR_CAPABILITIES.md`.*
