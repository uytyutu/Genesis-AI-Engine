# Genesis AI Hub — Architecture v1

**Date:** 2026-07-04  
**Status:** Vision + provider scaffold — **не продукт, не публикация**  
**Principle:** One Window · Company OS · Plan → Approve → Act (Law №1)  
**Companion:** `Genesis_One_Window_Roadmap_v1.md` (5 stages · Perfect Pallet dogfood)

---

## Суть

Genesis AI Hub — **не один ИИ**.

Это **единая платформа-диспетчер**, которая:

1. Принимает задачу на естественном языке (**текст или голос**)
2. Анализирует контекст (проект, файлы, Brain, история)
3. Выбирает **AI Provider(s)** и внешние инструменты (Cursor, Unity CLI, …)
4. Выполняет цепочку **Plan → Approve → Act**
5. Проверяет результат и показывает отчёт CEO / клиенту

Пользователь **не думает**: ChatGPT? Claude? Gemini? Cursor?

Он пишет или говорит:

> «Сделай мне сайт.»  
> «Добавь систему инвентаря в Perfect Pallet.»

Genesis решает, **кого вызвать**.

---

## Универсальные AI Providers (не бренды в UI)

Genesis **не привязан** к OpenAI / Anthropic / Google как к постоянной части продукта.

Внутри — слой **провайдеров**:

```
┌─────────────────────────────────────────┐
│           Genesis AI Hub (Router)        │
│  intent · routing · limits · approve     │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┐
    ▼             ▼             ▼              ▼
 Provider A   Provider B   Tool: Cursor   Tool: Unity
 (chat/LLM)   (vision/doc)  (code exec)    (game build)
```

| Concept | Meaning |
|---------|---------|
| **Provider** | Любой backend: LLM API, локальная модель, Cursor bridge, image gen |
| **Capability** | `chat` · `code` · `vision` · `document` · `image` · `audio` · `embed` |
| **Router** | Выбирает provider(ы) по задаче, тарифу, cost, availability |
| **Tool** | Внешний исполнитель (Cursor IDE, pytest, Unity) — не обязательно LLM |

Сегодня Provider A может быть OpenAI. Завтра — другая модель. **Архитектура не меняется.**

**Code scaffold:** `client/shared/ai-hub/types.ts` · `dashboard/backend/app/integration/ai_hub/`

---

## Диспетчер (CEO Development flow)

```
Задача (текст / голос)
        ↓
   Genesis Hub
   · parse intent
   · load project context
   · draft plan
        ↓
   CEO Approve  ← Law №1
        ↓
   Provider chain (пример)
   · Provider: analysis (large context)
   · Provider: architecture draft
   · Tool: Cursor (implementation)
        ↓
   Verify (tests · build · lint)
        ↓
   Report → CEO в Genesis (One Window)
```

CEO **не видит** цепочку брендов — только план, approve, прогресс, отчёт.

---

## Два интерфейса — один backend

### Consumer (клиенты мира)

Простой AI Hub. Без внутренних модулей Genesis Company.

```
Genesis

💬 Чат
📁 Файлы
🖼 Изображения
🎙 Голос
📂 Проекты
⚙ Настройки
```

**Чат** — как привычный chat UI:

| Input | Stage |
|-------|-------|
| Текст | ✅ foundation |
| Изображения | 🔜 |
| PDF · Word · Excel | 🔜 |
| Архивы · код | 🔜 |
| Аудио | 🔜 |
| Видео | horizon |

Язык: авто (см. `client/shared/i18n` + `locale_service.py`).

### CEO (Genesis OS)

Полный Company OS:

```
Genesis OS

🏠 Executive
🧠 Company Brain
💻 Development Studio
💬 AI Hub
📂 Projects
🏭 Factory
📊 Analytics
👥 Clients
💰 Finance
⚙ Settings
```

Development Studio **использует** AI Hub внутри — тот же router, другой chrome.

**Сегодня:** Desktop Stage 2.5 (Home · Chat · Projects · Settings) — зачаток CEO shell.

---

## Тарифы (архитектура, лимиты TBD)

> Точные лимиты — **после** анализа cost моделей и реального usage.  
> **Не публиковать** тарифы до Platform Launch Gate + CEO Approve.

| Tier | Назначение | Направление возможностей |
|------|------------|--------------------------|
| **Free** | Знакомство | N сообщений/день · размер файлов · базовые providers · короткий context |
| **Pro** | Power user | Длинный context · больше uploads · лучшие providers · images · projects |
| **Business** | Команды | Shared Brain · automation · API · integrations · seats |

Implementation hook: `TierLimits` в `ai-hub/types.ts` — значения заполняются позже.

---

## Связь с Cursor Replacement (5 stages)

| Stage | AI Hub role |
|-------|-------------|
| **1** | Hub orchestrates **Cursor as engine** — plan · approve · handoff · verify |
| **2** | Hub routes across **multiple providers** by capability |
| **3** | Hub + **Development Studio** UI in one window |
| **4** | Hub drives **Perfect Pallet** (Unity, assets, docs) end-to-end |
| **5** | Hub primary; Cursor **background tool** if needed |

Detail: `Genesis_One_Window_Roadmap_v1.md`

---

## Что уже есть в коде

| Piece | Status | Path |
|-------|--------|------|
| Rule-based assistant | ✅ | `assistant_service.py` |
| Locale-aware replies | ✅ | `locale_service.py` |
| Cursor handoff R0.5 | ⚠️ web | `cursor_handoff_service.py` |
| Provider types (stub) | ✅ | `client/shared/ai-hub/types.ts` |
| Provider registry (stub) | ✅ | `ai_hub/provider_registry.py` |
| LLM routing | ❌ | Stage 2 |
| Voice input | ❌ | Stage 1+ |
| File attachments in chat | ❌ | Consumer horizon |

---

## Gates — не делать сейчас

- Live API keys в production без CEO Approve  
- Публикация Free/Pro/Business  
- Store releases  
- «Заменить Cursor» маркетингом до Stage 5 dogfood  

---

## Следующий код (Stage 1)

1. **AI Hub task API** — `POST /api/ai-hub/tasks` (plan · approve · dispatch)  
2. **Desktop panel** — voice/text → plan card → approve → cursor handoff  
3. **Wire** existing `cursor_handoff_service` as `ToolProvider: cursor`  

Без редактора. Без новых Laws.

---

*Genesis AI Hub Architecture v1 · CEO vision frozen as direction, not product launch*
