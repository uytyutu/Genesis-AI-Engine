# Virtus Core — Service Matrix & Service Roadmap

**Дата:** 2026-07-10  
**Единица разработки:** **Услуга (Service)**, не capability и не commit  
**Основа:** Master Spec, Audit 2026-07-10, VECTOR_CAPABILITIES, код execution/factory/brain  
**Правило:** пользователь видит «Создание сайта», не `generate_site`

---

# Часть A — Ответ на главный вопрос (80%)

## «Какие 80% функций можно реализовать на существующей архитектуре, не изобретая ничего нового?»

### Честный ответ CTO

**Да — фундамент богаче UX примерно в 3–5 раз.** Большинство задуманных услуг Mission 1 **не требуют** новых слоёв (Brain v4, orchestration bus, new departments). Они требуют:

1. **Объединения** уже существующих модулей в один user-facing Service Release  
2. **Доведения UI** до того, чтобы артефакты были видны (Level B)  
3. **1–3 новых executor'ов** там, где gap реальный (revise, export, publish) — внутри уже существующего ExecutionManager  
4. **Подключения Brain LLM** к execution там, где сейчас rule-based (quality tier) — без новой архитектуры, через существующий Workforce  

### Что УЖЕ есть в фундаменте (не нужно изобретать)

| Компонент | Где | Что даёт услугам |
|-----------|-----|------------------|
| ExecutionManager + Plan + Verify | `execution/manager.py` | Любая multi-step услуга в одном run |
| Workspace + artifacts + visitor map | `execution/workspace.py` | Persistence, Zero Context, проекты |
| Bridge routing | `execution/bridge.py` | Intent → execution из чата |
| Capability Graph produces/consumes | `capability_graph.py` | Цепочки услуг без копирования |
| document_intelligence | rule-based analysis | Ядро «Бизнес-план» |
| report_render HTML | `report_render.py` | Профессиональное заключение |
| post_analysis_actions | intent CTAs | Следующие шаги по типу документа |
| workspace_reuse | analysis → site | Сквозная услуга |
| landing_builder + analyzer | `factory/` | Сайты по нише |
| factory validator + patcher | quality + improve | Редактирование HTML |
| preview serve | `preview.py` | Preview + file download |
| Brain + Workforce | `genesis_brain/` | Rewrite, consult, quality LLM tier |
| Knowledge intake PDF | 5 pages brain path | Контекст (legacy, не main path) |
| Factory ZIP export | R1.5 delivery | Экспорт пакета |
| `/order` + Stripe test | commercial shell | Продажа услуги |
| GenesisConcierge + ExecutionResultPanel | frontend | Точка входа |
| TTS | `genesis_tts/` | Voice в услугах |
| Acquisition site audit | internal | Аудит сайта (не public service) |

### 80% услуг Mission 1 = wiring, не architecture

| Категория | % на существующем фундаменте | Что реально нового нужно |
|-----------|------------------------------|--------------------------|
| Документы (анализ + заключение + export) | **~75%** | revise executor, docx/pdf writer, optional LLM pass |
| Сайты (создание + preview + export + reuse) | **~70%** | images/SEO/forms — контент в builder; publish = env config |
| Сайты (редактирование) | **~60%** | UI editor + factory patcher уже есть |
| Консультация / чат | **~95%** | polish only |
| Коммерческая доставка лендинга | **~80%** | live publish после Payment Hub |
| Презентация из отчёта | **~50%** | один executor + template |
| Proposal PDF | **~50%** | один executor + template |
| Приложение full-stack | **~15%** | почти всё новое — **не Mission 1** |
| CRM / Marketplace / Games | **~5%** | новые подсистемы — **Horizon** |

### Вывод 80%

> **~12–15 услуг Mission 1** можно довести до «полноценной услуги» **одним Service Release каждая**, используя Execution + Workspace + Factory + Brain + существующий frontend — **без** orchestration bus, без новых departments, без 20 новых capability в каталоге.

**Переломной рывок:** не новый код, а **Service Release = merge wiring + UI + 1–2 executors + Human Gate на beta**.

---

# Часть B — Полный каталог услуг (Service Matrix)

**Легенда статуса «Реализовано»:**
- ✅ работает end-to-end на beta/owner path  
- ⚠️ частично (код есть, UX/quality/gate не закрыты)  
- 🏗️ компоненты есть, услуга не собрана  
- ❌ отсутствует  

**Легенда Service Release:**
- 🟢 можно одним SR без новой архитектуры  
- 🟡 SR возможен, но нужен внешний gate (Payment, Gewerbe)  
- 🔴 новая подсистема — не SR в ближайшие месяцы  

---

## SERVICE 1 — Анализ бизнес-документа (Бизнес-план)

**Пользователь видит:** «Анализ бизнес-плана» / «Проверь мой документ»

| Что получает пользователь | Реализовано | Не хватает |
|---------------------------|-------------|------------|
| Загрузка PDF/txt | ✅ upload + intake | DOCX, OCR для scan |
| Анализ содержания | ⚠️ rule-based SWOT, readiness | LLM quality tier |
| Язык = язык документа | ✅ document-first locale | — |
| Executive Summary | ✅ executive_summary.md | in-app viewer |
| Профессиональное заключение | ⚠️ report.html | investor-grade текст |
| Готовность бизнеса (score) | ✅ readiness 0–100 | калибровка на реальных планах |
| Финансовые риски | ⚠️ heuristics | structured financial block |
| Инвестиционная привлекательность | ⚠️ launch_probability | — |
| Список приоритетов | ✅ priority_actions | — |
| Следующий шаг (intent actions) | ✅ post_analysis_actions | disabled items честно «скоро» |
| Исправление документа | ❌ | revise pipeline |
| v2 PDF / v2 DOCX | ❌ | export executors |
| Список изменений (track changes) | ❌ | diff manifest |
| Сравнение v1 vs v2 | ❌ | — |
| AI rewrite | 🏗️ Brain LLM exists | не wired к file output |
| Экспорт пакета | 🏗️ ZIP в Factory path | unified export из workspace |

**Существующие capability объединить:**
`analyze_business_document` + `filesystem_write` + Brain Workforce (rewrite pass) + `report_render` + `post_analysis_actions` + preview serve

**Один Service Release?** 🟢 **SR-1 «Бизнес-план Pro»**

**Состав SR-1 (один merge, одна Human Gate):**
1. LLM quality pass поверх document_intelligence (Workforce, не новый слой)  
2. `revise_document` executor → v2.md → export PDF/DOCX (pypdf + python-docx или pandoc)  
3. `changes.json` manifest — что исправлено  
4. In-app report viewer (frontend, не новая вкладка)  
5. Export ZIP: summary + report + v2 + structure  
6. Human Gate: CEO PDF на beta — PASS/FAIL  

**Ценность:** killer differentiation vs ChatGPT — **файл на выходе, не essay**  
**Экономия пользователя:** 4–8 ч  
**Зависимости:** Gate 3 quality baseline (можно в том же SR)  

---

## SERVICE 2 — Создание сайта

**Пользователь видит:** «Создание сайта»

| Что получает | Реализовано | Не хватает |
|--------------|-------------|------------|
| Анализ ниши из текста | ⚠️ factory/analyzer + reuse | deep niche research |
| Структура страницы | ✅ landing_builder sections | multi-page |
| Тексты | ✅ template copy by niche | LLM custom copy tier |
| Дизайн HTML/CSS | ✅ | visual editor |
| Изображения | ❌ | stock/placeholder gen |
| SEO meta | ⚠️ basic in templates | full SEO pass |
| Мобильная версия | ⚠️ responsive CSS | dedicated mobile QA |
| Preview | ✅ preview/ artifacts | in-app iframe |
| Публикация live | ❌ | Publisher + hosting |
| ZIP экспорт | ✅ owner Factory path | public workspace export |
| Редактирование | 🏗️ landing_patcher (owner) | public «измени заголовок» |
| Повторное открытие проекта | ⚠️ visitor workspace | visible project list UI |
| Reuse из анализа | ⚠️ workspace_reuse code | Gate 4 CEO PASS |

**Объединить:**
`generate_site` + `workspace_reuse` + `landing_builder` + `landing_patcher` + factory `validator` + preview + optional `analyze_business_document` upstream

**Один Service Release?** 🟢 **SR-2 «Создание сайта»** (часть 1) + 🟡 часть 2 (publish)

**SR-2a (без Payment Hub):**
1. Gate 4–5 CEO PASS (reuse + zero context) — **закрытие RC1, не новая архитектура**  
2. Workspace UI: последний сайт + preview in-app  
3. LLM copy tier для текстов (Workforce → brief.md input)  
4. SEO block в manifest  
5. Placeholder images (static assets, не gen AI)  
6. Public ZIP export из workspace  
7. Chat: «измени секцию X» → patcher path  

**SR-2b (после EL3):** live publish через Publisher  

**Ценность:** sellable 350–1200 € package end-to-end  
**Экономия:** 6–12 ч vs freelancer  

---

## SERVICE 3 — Консультация Vector (Чат-партнёр)

**Пользователь видит:** «Спросить Vector»

| Что получает | Реализовано | Не хватает |
|--------------|-------------|------------|
| Умный диалог | ✅ Brain v3 + Workforce | meta/slang edge cases |
| Память | ✅ visitor memory | cross-device account |
| Голос | ✅ TTS/STT partial | mobile polish |
| «Что умеешь?» | ✅ capability discovery | dedicated screen |
| Переход к работе | ⚠️ execution on intent | auto-suggest услуг |

**Объединить:** Brain stack only — уже собрано

**Service Release?** 🟢 **SR-0** (уже live) — только polish, не расширять

**Ценность:** acquisition funnel → платные услуги  
**Не раздувать** — чат не должен съедать фокус  

---

## SERVICE 4 — Коммерческий заказ лендинга

**Пользователь видит:** «Заказать сайт» на `/order`

| Что получает | Реализовано | Не хватает |
|--------------|-------------|------------|
| Выбор пакета | ✅ 350/650/1200 | — |
| Оплата | ⚠️ test Stripe | live KYC |
| Статус заказа | ✅ | email automation |
| Доставка | ⚠️ manual ZIP CEO | self-service portal |
| Связь с Factory | 🏗️ separate paths | order → factory job |

**Объединить:** `sales_order_service` + Factory export + email Resend

**Service Release?** 🟡 **SR-COM** после EL3 + Gewerbe

---

## SERVICE 5 — Презентация для инвестора

**Пользователь видит:** «Создай презентацию»

| Что получает | Реализовано | Не хватает |
|--------------|-------------|------------|
| Слайды из отчёта | ❌ | executor |
| Шаблон pitch deck | 🏗️ graph node planned | template engine |
| Export PDF/PPTX | ❌ | — |

**Объединить:** `report.md` + `document_structure.json` + `filesystem_write` + Brain outline + template

**Service Release?** 🟢 **SR-5** — один executor + markdown slides + PDF export  
**Зависит от:** SR-1 quality reports  
**Ценность:** high for business plan users  

---

## SERVICE 6 — Коммерческое предложение (Proposal)

| Реализовано | Не хватает |
|-------------|------------|
| 🏗️ graph node | executor, PDF |

**SR-6** 🟢 после SR-1 + optional SR-2 — template + report inputs  

---

## SERVICE 7 — Финансовая модель

| Реализовано | Не хватает |
|-------------|------------|
| ⚠️ finance_notes in analysis | Excel generation |

**Объединить:** analysis structure + `generate_excel` (planned) OR export CSV via filesystem_write

**SR-7** 🟢 средний приоритет — CSV/XLSX из structure.json без new architecture  

---

## SERVICE 8 — Перевод документа

| Реализовано | Не хватает |
|-------------|------------|
| ✅ locale detection | translate executor |

**SR-8** 🟢 Brain LLM translate → filesystem_write — **no new layer**  

---

## SERVICE 9 — Версия для банка

| Реализовано | Не хватает |
|-------------|------------|
| ⚠️ partial in report | bank template + export |

**SR-9** 🟢 template variant of SR-1 output  

---

## SERVICE 10 — Аудит существующего сайта

| Реализовано | Не хватает |
|-------------|------------|
| ✅ Acquisition internal | public service, URL fetch |

**SR-10** 🟡 needs `browser_navigation` or httpx fetch — executor mostly new, **but** fits execution pattern  

---

## SERVICE 11 — Создание README / технического документа

| Реализовано | Не хватает |
|-------------|------------|
| ✅ Gate 1 filesystem_write | templates, multi-file |

**SR-11** 🟢 minor — template packs  

---

## SERVICE 12 — Разработка приложения

| Реализовано | Не хватает |
|-------------|------------|
| 🏗️ catalog only | almost everything |

**SR-12** 🔴 **NOT Mission 1** — requires generate_app, docker, deploy executors — months  

---

## SERVICE 13 — Telegram / WhatsApp бот

| Реализовано | Не хватает |
|-------------|------------|
| stub skill | entire pipeline |

**SR-13** 🔴 Horizon  

---

## SERVICE 14 — CRM / клиенты

| Реализовано | Не хватает |
|-------------|------------|
| 💡 docs | entire subsystem |

**SR-14** 🔴 after Payment Hub  

---

## SERVICE 15 — Маркетинг / Growth

| Реализовано | Не хватает |
|-------------|------------|
| 💡 R12 docs | engine |

**SR-15** 🔴 Horizon  

---

## SERVICE 16 — Игры / Perfect Pallet

| Реализовано | Не хватает |
|-------------|------------|
| handoff prompt | integration |

**SR-16** 🔴 separate product  

---

## SERVICE 17 — Юридическая проверка договора

| Реализовано | Не хватает |
|-------------|------------|
| ⚠️ contract doc_type | legal LLM prompt + report |

**SR-17** 🟢 variant of SR-1 with legal template + disclaimer — **no new architecture**  

---

## SERVICE 18 — Workspace / Мои проекты

| Реализовано | Не хватает |
|-------------|------------|
| 🏗️ disk + visitor map | full UI Level B |

**SR-18** 🟢 **frontend-only Service Release** — максимальный UX ROI  

---

## SERVICE 19 — Voice-ассистент

| Реализовано | Не хватает |
|-------------|------------|
| ✅ TTS/STT | mobile UX |

**SR-19** 🟢 polish pass  

---

## SERVICE 20 — Подписка Virtus Core Pro

| Реализовано | Не хватает |
|-------------|------------|
| display pricing | billing, entitlements |

**SR-20** 🔴 after EL3  

---

# Часть C — Объединение capability → Услуга (mapping)

| Техническое (скрыто) | Пользовательская услуга |
|----------------------|-------------------------|
| analyze_business_document + report_render + post_analysis | **Анализ бизнес-плана** |
| + revise + export pdf/docx | **Бизнес-план Pro** (SR-1) |
| generate_site + landing_builder + preview | **Создание сайта** |
| + workspace_reuse + patcher | **Создание сайта из плана** |
| filesystem_write | **Создание документа** |
| Brain + Memory | **Консультация** |
| Factory + validator + ZIP | **Производство лендинга (CEO)** |
| order + stripe | **Заказ сайта** |

**Принцип:** capability остаются внутри; **marketing + UI + Human Gate** на уровне Service.

---

# Часть D — Roadmap по услугам (не по коммитам)

## Фаза 0 — Закрыть правду (2–4 недели, без новых услуг)

| # | Действие | Тип |
|---|----------|-----|
| 0.1 | CEO PASS Gates 3–5 на beta | Human Gate |
| 0.2 | WC=1 declared | Milestone |
| 0.3 | Скрыть catalog inflation в UI | polish |

**Результат:** текущие услуги честно «работают» или «не работают».

---

## Фаза 1 — Service Releases с максимальной ценностью (после WC=1)

**CEO утверждено 2026-07-10:** порядок фиксирован. RC1 завершается до любого SR.

| Приоритет | Service Release | Почему этот порядок |
|-----------|-----------------|---------------------|
| **RC1** | Gates 3–5 → WC=1 | Закрыть правду: механика работает на beta |
| **#1** | **SR-18 Workspace OS** | Фундамент есть, пользователь видит чат — не ОС. Workspace главный экран, Vector помощник |
| **#2** | **SR-1 Business Plan Pro** | Killer vs ChatGPT: v2 PDF/DOCX, не essay. На базе видимого workspace |
| **#3** | **SR-2 Website Pro** | Сайт из проекта в workspace: план → сайт → edit → ZIP → preview |
| **#4** | **SR-5 Presentation Pro** | Upsell из workspace: report → deck file |

**Не параллелить SR** — одна услуга → один merge → один Human Gate по `VIRTUS_CORE_SERVICE_CONTRACTS.md`.

**Снято с приоритета #1:** SR-18 после RC1, не вместо Gate 3–5.

---

## Фаза 2 — Расширение услуг (месяцы 4–6, после EL3 или parallel if EL3 early)

| SR | Услуга | Условие |
|----|--------|---------|
| SR-COM | Заказ + доставка | Gewerbe + live Stripe |
| SR-6 | Proposal | SR-1 stable |
| SR-7 | Финансовая модель | SR-1 structure.json |
| SR-8 | Перевод | SR-1 |
| SR-2b | Публикация сайта | Payment Hub |
| SR-17 | Проверка договора | SR-1 template variant |

---

## Фаза 3 — Horizon (не обещать даты)

SR-12 App · SR-13 Bot · SR-14 CRM · SR-15 Marketing · SR-16 Games · SR-20 Subscriptions

---

# Часть E — Матрица «один Service Release = один merge»

| SR | Услуга | Уже есть (≥%) | Добавить в merge | Новая архитектура? | Human Gate |
|----|--------|---------------|------------------|-------------------|------------|
| SR-18 | Мои проекты | 90% | UI list + artifact viewer | ❌ | beta walk |
| SR-1 | Бизнес-план Pro | 75% | revise, export, LLM pass, viewer | ❌ | PDF real |
| SR-2a | Создание сайта | 70% | Gate4-5, copy, ZIP, chat edit | ❌ | site from plan |
| SR-5 | Презентация | 50% | 1 executor + template | ❌ | slides from report |
| SR-6 | Proposal | 50% | 1 executor | ❌ | — |
| SR-7 | Fin model | 40% | XLSX export | ❌ | — |
| SR-8 | Перевод | 60% | translate executor | ❌ | — |
| SR-2b | Publish | 30% | hosting integration | ⚠️ env | live URL |
| SR-12 | App | 15% | almost all | ✅ | — |

---

# Часть F — Что НЕ делать (CEO alignment)

1. ❌ Не выпускать SR с 50 задачами — max **1 услуга = 1 merge = 1 beta gate**  
2. ❌ Не начинать SR-12 App пока SR-1 и SR-2 не дают €  
3. ❌ Не добавлять capability в каталог без Service wrapper  
4. ❌ Не путать SR с RC1 Gate fix — Gate fix может быть частью SR-2a  
5. ❌ Не строить orchestration diagram — Workforce + ExecutionManager достаточно  

---

# Часть G — Резюме для CEO (Рамиш)

| Вопрос | Ответ |
|--------|-------|
| Единица работы | **Service Release**, не commit |
| Сколько SR до «продукт ощущается» | **3–4** (Workspace + Бизнес-план Pro + Сайт + Презентация) |
| 80% на старой архитектуре? | **Да** для Mission 1 docs + sites |
| Первый SR | **SR-18 Workspace UI** — быстрый win, zero backend risk |
| Killer SR | **SR-1 Бизнес-план Pro** — v2 file на выходе |
| Деньги | **SR-2a + SR-COM** — после WC=1 и EL3 |
| Годы по одной кнопке? | Нет — **4 SR за квартал** реалистично |
| Огромный коммит? | Нет — **1 SR = 1 merge = 1 CEO verify** |

---

*Документ для решений CEO. Следующий шаг: утвердить порядок SR-18 → SR-1 → SR-2a и критерии Human Gate для каждой услуги.*
