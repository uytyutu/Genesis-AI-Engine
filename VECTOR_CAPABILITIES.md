# Vector — RC1 (Release Candidate 1)

**Разработка на паузе.** Главная задача — подтвердить, что способности работают для обычного пользователя на `/site`.

Ценность = **завершённые workflow**, не архитектура и не «умный чат».

## Правило RC1 (жёсткое)

> **Любая новая идея автоматически отклоняется до завершения RC1**, если она не исправляет один из пяти Gate.

---

## RC1 — пять Gate (пользовательский опыт)

| Gate | Сценарий | PASS критерий | Статус |
|------|----------|---------------|--------|
| **1 — Documents** | `Создай README` | Настоящий файл в workspace | ✅ PASS |
| **2 — Sites** | `Создай сайт стоматологии` | Workspace + файлы + Preview | ✅ PASS |
| **3 — Analysis** | PDF бизнес-плана → анализ | Executive Summary + Report + `document_structure.json`; кнопки артефактов, не простыня в чате | 🔄 ждёт CEO (UX fix shipped) |
| **4 — Reuse** | После анализа: только `Создай сайт` | Использует артефакты анализа; Explain Reuse (что взято, что не спрашивал) | 🔄 ждёт CEO |
| **5 — Zero Context** | Закрыть браузер → снова `Создай сайт` | Тот же workspace, reuse без повторных вопросов (Rule №6) | 🔄 ждёт CEO |

### RC1 complete = Workflow Completion = 1

> Все пять Gate пройдены CEO на [beta `/site`](https://beta.genesis-ai-engine.com/site) без терминала и Owner API.

**До WC=1:** ни новых услуг (SR), ни архитектуры — только Gates 1–5.

**После WC=1:** выпуск по **Service Releases** — см. `docs/VIRTUS_CORE_SERVICE_CONTRACTS.md`.

**Исключение — Critical UX (Level A):** исправления восприятия без новых capability и без смены архитектуры. Разрешено параллельно с RC1:

| # | Critical UX | Статус |
|---|-------------|--------|
| 1 | Пустой экран → приветствие + starters | ✅ CEO PASS |
| 2 | Убрать дубли «На главную» | ✅ CEO PASS |
| 3 | Composer внутри карточки, не плавающий | ✅ CEO PASS |
| 4 | Однозначная навигация (☰ · VECTOR · +) | ✅ CEO PASS |
| 5 | «Что умеешь?» → Capability Registry | ✅ CEO PASS |
| 6 | Workspace placeholder «Пока пусто» | ✅ CEO PASS |

**Level A закрыт (2026-07-10).** Gate 3–5 RC1 — отдельно, только после реальной проверки на beta.

**Execution UX (Gate 3 Product Truth, 2026-07-10):** PDF → execution layer (артефакты + кнопки), не Brain essay. Brain expert review отключён при analyzable attachments.

**Level B (после WC=1) — north star:** Workspace как главный экран, не чат.

```text
Workspace → Артефакты → Задачи → Прогресс → Чат (справа)
```

Целевой экран: «Последняя работа» с цепочкой (PDF ✓ → Site ✓ → Presentation …) и Vector как панель, не как приложение-чат.

---

## Процесс разработки

### RC1 (до WC=1)

```
1. Исправляем Gate 1–5 на beta
2. Human Gate CEO
3. WC=1
```

### После WC=1 — Service First (Rule №9)

```
1. Утверждаем услугу (Service Contract)
2. WOW Gate (Rule №10)
3. Service Release — один merge
4. Human Gate на beta
5. Следующая услуга
```

**Порядок услуг:** RC1 → SR-18 Workspace OS → SR-1 Business Plan Pro → SR-2 Website Pro → SR-5 Presentation Pro

**Вопрос планирования (не «какую capability добавить»):**
> *Какую работу теперь сможет выполнить Virtus Core для клиента, которую вчера выполнить не мог?*

---

## Правила (компакт)

1. Одна способность = законченная ценность  
2. Пирамида ценности  
3. Capability Graph (Produces / Consumes)  
4. Reuse — артефакты workspace  
5. **Explain Reuse** — показать что использовано  
6. **Zero Context** — переживает закрытие браузера  
7. **Trust Before Automation** — подтверждение перед изменениями *(внутри Business Plan Pro и др.)*  
8. **Product Truth** — только `/site`  
9. **Service First** — любой новый код только ради законченной услуги, за которую платят  
10. **WOW Gate** — перед READY: новичок скажет «Вау», не «ну, прикольно»  

### Rule №9 — Service First (CEO 2026-07-10)

> **Любой новый код существует только ради законченной услуги.**

Не ради: executor, planner, bridge, capability, routing, Brain.

**Язык планирования:**
| ❌ Было | ✅ Стало |
|--------|---------|
| Commit 4 | **Business Plan Pro** |
| generate_site executor | **Website Pro** |
| document_intelligence | Document Intelligence Engine *(внутри Business Plan Pro)* |

Технические имена — внутри кода. Наружу — **название услуги**.

### Rule №10 — WOW Gate (CEO 2026-07-10)

Перед READY услуги:

> **Если показать человеку, который никогда не видел Virtus Core — скажет ли он «Вау»?**

«Ну… вроде прикольно» = **не выпускать**.

**Business Plan Pro WOW:** переписал → v2 PDF + DOCX → список изменений → готовность → следующие шаги.  
**Website Pro WOW:** preview открыт → mobile → SEO → ZIP → редактор → (позже) публикация.

Критерии PASS/FAIL — в `docs/VIRTUS_CORE_SERVICE_CONTRACTS.md`.

## Позиционирование (CEO 2026-07-10)

**Virtus Core — не AI Assistant, не Chat AI, не Copilot.**

**Virtus Core — Digital Company.**

Клиент «нанимает» команду: консультант, разработчик, дизайнер, аналитик, маркетолог, редактор, PM — одно лицо **Vector**.  

## KPI

| KPI | Вопрос |
|-----|--------|
| Hours Saved | Сколько часов снято? |
| Reuse Score | Сколько capability переиспользовано? |
| **Workflow Completion** | Сколько цепочек end-to-end без копирования? |

---

## Истории для пользователя (не архитектура)

Пользователю не нужны «Executive Brain», «Planner», «Capability Graph».

Ему нужны истории:

1. **«Загрузил бизнес-план → получил анализ → создал сайт.»** ← RC1 Gate 3–5  
2. «Открыл проект → Vector нашёл ошибку → diff → подтвердил → исправление.» ← внутри **Business Plan Pro** (Trust)  
3. «Попросил презентацию → получил файл.» ← horizon  

---

## Capability Graph (внутренний, для команды)

`dashboard/backend/app/execution/capability_graph.py`  
Owner: `GET /api/owner/execution/capabilities` → `capability_graph`

```text
📄 PDF → 📊 report.md + document_structure.json → 🌐 site
```

---

## Способности RC1

| Capability | Commit | Gate | READY |
|------------|--------|------|-------|
| Создавать документы | 1 | Gate 1 | ✅ |
| Создавать сайты | 2 | Gate 2 | ✅ |
| Анализировать бизнес-документы | 3 | Gate 3 | 🔄 |
| Reuse (site ← analysis) | merge | Gate 4–5 | 🔄 |

---

## CEO checklist — RC1 verification

### Gate 3
- [ ] Открыть beta `/site`  
- [ ] Загрузить **реальный** PDF бизнес-плана  
- [ ] «Проанализируй мой бизнес-план»  
- [ ] Открыть **Отчёт** и **Executive Summary**  
- [ ] Убедиться: формулировки из **вашего** файла, не шаблон  

### Gate 4
- [ ] В том же чате/workspace: только «Создай сайт»  
- [ ] Сайт отражает данные анализа  
- [ ] В ответе: Explain Reuse (файлы + «не спрашивал услуги/аудиторию/рынок»)  

### Gate 5
- [ ] Закрыть браузер полностью  
- [ ] Снова открыть beta `/site`  
- [ ] Только «Создай сайт»  
- [ ] Reuse снова работает, вопросов о бизнесе нет  

## CEO отчёт — только факты (шаблон)

После проверки на beta — ответ в таком формате:

### Gate 3 — Analysis
```
PASS | FAIL
Загрузил PDF: …
Получил report.md / executive_summary: да/нет
Соответствует документу: …
Цитаты реальные: да/нет
Замечания: …
```

### Gate 4 — Reuse
```
PASS | FAIL
После анализа: «Создай сайт»
НЕ спросил нишу / аудиторию / услуги: да/нет
Explain Reuse в ответе: да/нет
Использовал артефакты: …
```

### Gate 5 — Zero Context
```
PASS | FAIL
Закрыл браузер → открыл снова → «Создай сайт»
Reuse сохранился: да/нет
Workspace потерялся: да/нет
```

**Workflow Completion = 1** — когда Gate 3, 4, 5 = PASS.

---

## После RC1 (не сейчас)

### UX Release — первый приоритет после WC=1

Не новые capability. Не логика. **Только интерфейс** — чтобы `/site` отражал платформу, а не «пустой чат».

**Проблемы (CEO, 2026-07-10):**
1. Пустота welcome — ощущение «здесь ничего нет»
2. Верхняя панель — дубли «На главную», нет единой системы
3. Чат потерял центр — внимание на пустую область
4. Поле ввода «плавает» — не ощущение дорогого продукта
5. **Workspace невидим** — пользователь не видит артефакты, workflow, reuse

**Цель:** от «есть чат» → «есть рабочее пространство» (чат + артефакты + прогресс + последняя работа).

**Экраны (варианты):**
- Последняя работа: `report.md`, website, `executive_summary`, время
- Workspace: последние файлы (`README.md`, `report.md`, `site_manifest.json`)
- **What Vector Can Do** — READY-способности + примеры фраз

**Routing (post-RC1 или Gate-2 discoverability):** «Ты умеешь делать сайты?» → ответ про capability + примеры (`Создай сайт стоматологии`), не бизнес-идеи.

Делать **после** WC=1 как часть **SR-18 Workspace OS**, **до** **Business Plan Pro**.

---
