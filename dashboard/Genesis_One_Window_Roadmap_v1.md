# Genesis One Window — Roadmap v1

**Date:** 2026-07-04  
**Vision:** Работать в **одном месте** — Genesis — а инструменты (Cursor, Unity, Git, deploy) работают как исполнители.  
**Input:** **текст и голос** — один и тот же pipeline.  
**Dogfood project:** Perfect Pallet  
**AI layer:** `Genesis_AI_Hub_Architecture_v1.md`

---

## Почему это сильная идея

Соответствует **One Window** и **Dogfood First**.

CEO не прыгает между:

- Cursor · Unity · GitHub · Railway · Vercel · браузер · документация

Один интерфейс. Естественный язык. Plan → Approve → Act.

---

## Stage 1 — Cursor как двигатель (скоро)

**Цель:** Для CEO выглядит так, будто работаешь **только в Genesis**. Cursor — скрытый исполнитель.

### Сценарий (голос или текст)

> «Добавь систему инвентаря в Perfect Pallet.»

### Pipeline

```
1. Genesis принимает utterance (STT или текст)
2. Анализирует проект (repo map, docs, North Star)
3. Составляет план (файлы, шаги, риски)
4. Показывает план CEO
5. CEO Approve
6. Genesis формирует handoff → запускает Cursor
7. Принимает результат (git diff / task complete)
8. Verify (pytest, build checks)
9. Отчёт в Genesis UI
```

### Build targets

| Item | Status |
|------|--------|
| Web cursor handoff R0.5 | ⚠️ exists |
| Plan card + approve gate | ❌ |
| Desktop AI Hub entry (text) | ❌ |
| Voice → text (STT) | ❌ |
| Project context for Perfect Pallet | ❌ |
| Unified task registry | ⚠️ partial |

**Не делать:** встроенный редактор, замена Cursor UI.

---

## Stage 2 — Мульти-провайдерный Hub

**Цель:** Genesis сам выбирает инструменты по capability.

Пример routing (внутренний, не показывать CEO брендами):

| Task slice | Typical capability |
|------------|-------------------|
| Архитектура | `chat` + long context |
| Большие документы | `document` |
| Код | `code` → Tool: Cursor |
| Дизайн / images | `image` |
| Перевод | `chat` + locale |
| Тесты | `code` + verify tool |

CEO говорит:

> «Сделай мультиплеер.»

Hub декомпозирует → chain of providers → один отчёт.

### Build targets

- `AiHubRouter` implementation  
- Provider registry + health  
- Owner API keys (Settings, encrypted, CEO-only)  
- Cost / usage logging (no billing until gate)

---

## Stage 3 — Genesis Development Studio

**Цель:** IDE-поверхность **внутри** Genesis.

| Module | Function |
|--------|----------|
| Code editor | Monaco + LSP |
| File manager | Workspace tree |
| Git | status · diff · commit (approve) |
| Terminal | sandboxed |
| Project analysis | context for Hub |
| AI chat | Hub-powered |
| Tasks | handoff queue |
| Build | npm · pytest · custom |
| Deploy | gated (Railway etc.) |

Studio **не дублирует** Cursor — использует Hub + tools.

---

## Stage 4 — Perfect Pallet в Genesis Desktop

**Цель:** Игровой проект как first-class citizen в CEO shell.

```
Genesis Desktop

🏠 Главная
💬 AI
🎮 Perfect Pallet
📁 Assets
💻 Development Studio
🧠 Brain
📊 Executive
📦 Factory
⚙ Settings
```

### Сценарий

> «Добавь новый склад Aldi.»

1. Анализ архитектуры (сцены, скрипты, ScriptableObjects)  
2. План изменений  
3. CEO Approve  
4. Изменения (via Cursor / agents)  
5. **Unity build** (tool provider)  
6. Preview / diff report  

### Сценарий (широкий)

> «Добавь категорию молочные продукты. Паллеты только в холодной зоне. Обнови задания, UI и документацию.»

1. Найти связанные файлы across code + docs  
2. План с группами: gameplay · UI · docs  
3. Approve  
4. Execute chain  
5. Build game  
6. Changelog для CEO  

---

## Stage 5 — Genesis главное приложение

**Цель:** Cursor открывается редко или в фоне.

| Signal | Meaning |
|--------|---------|
| 2+ weeks daily work in Genesis | dogfood criterion |
| Stage 3 Studio covers 80% tasks | parity check |
| Cursor optional in settings | background tool |

**Не удалять** Cursor bridge заранее — только deprecate после факта.

---

## Cursor Replacement — сводная оценка

```
One Window / Cursor Replacement

Текущее состояние:  10 %

Stage 1  Cursor engine behind Genesis     → target ~25 %
Stage 2  Multi-provider Hub               → target ~40 %
Stage 3  Development Studio               → target ~65 %
Stage 4  Perfect Pallet in one window     → target ~85 %
Stage 5  Genesis primary app              → target ~95 %
```

---

## Perfect Pallet — почему первый

- Реальный проект CEO (dogfood)  
- Unity + code + docs + gameplay — stress-test One Window  
- Опыт → Consumer AI Hub и Factory  

Не abstract demo — **рабочая смена** в Genesis.

---

## Законы и gates

| Rule | Application |
|------|-------------|
| Law №1 | Каждый plan → **Approve** перед act |
| Dogfood First | Stages 1–4 на Perfect Pallet + Genesis repo |
| Platform Launch Gate | Consumer tiers · stores · live billing |
| CEO Approve | Live provider keys · paid API spend |

---

## Связанные документы

- `Genesis_AI_Hub_Architecture_v1.md`  
- `Genesis_Development_Studio_Audit_v1.md`  
- `Genesis_Consumer_Platform_Foundation_v1.md`  
- `client/docs/Genesis_OS_Architecture_v1.md` §7.1

---

*One Window Roadmap v1 · поэтапно, без попытки сразу заменить Cursor*
