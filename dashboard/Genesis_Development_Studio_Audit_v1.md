# Genesis Development Studio — Audit v1

**Date:** 2026-07-04  
**Scope:** Genesis Desktop (`client/desktop/`) + web Mission Control dev surfaces  
**Mission:** Consumer Platform Foundation · §1

---

## 1. Есть ли собственный движок разработки?

**Нет.** Development Studio — **архитектура и roadmap**, не реализация.

| Layer | Status | Location |
|-------|--------|----------|
| Development Studio UI | ❌ | Planned Stage 4 — `client/docs/Genesis_OS_Architecture_v1.md` §7.1 |
| Code editor (Monaco/LSP) | ❌ | — |
| Terminal / PTY | ❌ | — |
| Repo file tree | ❌ | — |
| AI agent / multi-file edits | ❌ | — |
| Git / build / test in-app | ❌ | Web verify after external Cursor only |
| Cursor handoff (R0.5) | ⚠️ Web only | `dashboard/frontend/app/cursor/` |
| Rule-based assistant | ✅ | Desktop + API — business ops, not coding |

**Что есть сегодня:** Genesis Desktop Stage 2.5 — **Daily Driver** для владельца: Home, Chat, Projects (read-only Factory), Settings, Command Palette (Ctrl+K).

---

## 2. Что уже умеет vs Cursor?

| Capability | Cursor | Genesis today |
|------------|--------|-----------------|
| Code editor + LSP | ✅ | ❌ |
| Workspace / file tree | ✅ | ❌ (Factory preview links only) |
| Integrated terminal | ✅ | ❌ |
| AI chat with codebase | ✅ | ❌ (rule-based company assistant) |
| Agent / apply patches | ✅ | ❌ |
| Git UI | ✅ | ❌ |
| Build / test in IDE | ✅ | ⚠️ pytest verify via web handoff |
| Business dashboard | ❌ | ✅ Desktop + Mission Control |
| Factory product viewer | ❌ | ✅ |
| Owner approve gates | ❌ | ✅ (web MC, Laws) |
| Cursor task handoff | N/A | ⚠️ semi-auto clipboard (web) |

Genesis **не конкурирует с Cursor как IDE** (`WHY.md`). Цель Studio — **собственный слой Genesis** поверх Plan → Approve → Act, не клон VS Code.

---

## 3. Чего не хватает для работы полностью внутри Genesis?

### Must-have (Cursor Replacement Stage 3–4)

1. **Code Workspace** — editor + file tree на локальный repo  
2. **AI Planner / Reviewer** — контекст проекта, diff, approve gate  
3. **Build & Test** — запуск pytest/npm в sandbox, вывод в UI  
4. **Git integration** — status, commit, branch (с CEO approve)  
5. **Development Studio nav** — Brain · Dev · Executive в Desktop  
6. **Cursor Bridge в Desktop** — handoff из одного окна (сейчас только web)  
7. **LLM provider abstraction** — выбор модели (Stage 2 плана замены)

### Already sufficient for non-coding CEO work (~70–80% browser)

- Подключение к API, dashboard, модули, уведомления  
- Чат-помощник (статус, следующие шаги)  
- Просмотр Factory-продуктов  
- Command palette, тема, **i18n ru/en/de** (v1 foundation)

---

## 4. Что перенести из Cursor в Genesis?

| From Cursor | Into Genesis | Priority |
|-------------|--------------|----------|
| Task context (repo, files, goal) | Dev Studio workspace + handoff API | P1 |
| AI coding session | Genesis agent with approve gates | P2 |
| Terminal output | Embedded terminal panel | P2 |
| File search / tree | Project workspace browser | P1 |
| Multi-model choice | Provider abstraction (Stage 2) | P2 |
| Rules / skills | Genesis Laws + project rules store | P3 |

**Не переносить:** полный fork редактора — интегрировать Monaco/CodeMirror + LSP, не клонировать Cursor UI.

---

## 5. Cursor Replacement — оценка

```
Cursor Replacement

Текущее состояние:

10 %

Что осталось реализовать:

Stage 1 (текущий) — Genesis вызывает Cursor как внешний инструмент
  • Web handoff R0.5 (clipboard + open repo)                    ✅ частично
  • Handoff из Desktop                                          ❌
  • Единый task registry Cursor ↔ Genesis                       ⚠️ базовый API

Stage 2 — Разные AI-модели
  • Provider abstraction (OpenAI, Anthropic, local)             ❌
  • Model picker в Settings                                     ❌
  • API keys / owner-only config                                ❌

Stage 3 — Development Studio как основная среда
  • Code editor + file tree                                     ❌
  • Terminal / build / test                                     ❌
  • AI planner → patch → CEO approve → apply                    ❌
  • Git status / commit UI                                      ❌

Stage 4 — Perfect Pallet полностью в Genesis Desktop
  • Project nav (Perfect Pallet · Assets)                      ❌
  • Unity build tool provider                                  ❌
  • End-to-end voice/text scenario                             ❌

Stage 5 — Genesis primary app; Cursor в фоне
  • 2+ weeks dogfood                                           ❌
  • Cursor optional / background only                          ❌
```

**Roadmap:** `Genesis_One_Window_Roadmap_v1.md` · **AI Hub:** `Genesis_AI_Hub_Architecture_v1.md`

### Детализация по весам

| Area | Weight | Score |
|------|--------|-------|
| Editor + LSP | 25% | 0% |
| Workspace / files | 15% | 0% |
| Terminal | 10% | 0% |
| AI agent + codebase | 25% | ~2% |
| Git / build / test | 15% | ~3% |
| Orchestration / handoff | 10% | ~40% (web only) |

**Итого: ~10%** — Genesis снимает потребность в **браузере** для CEO-операций, но **не в Cursor** для разработки.

---

## 6. Рекомендуемый следующий шаг (код) — Stage 1

1. **AI Hub task API** — plan · approve · dispatch (wire `cursor_handoff_service`)  
2. **Desktop** — text entry → plan card → approve (voice STT later)  
3. **Perfect Pallet** — project context in handoff prompt  

Не начинать: Store, подписки, редактор, multi-LLM keys без CEO Approve.

---

## Связанные документы

- `Genesis_AI_Hub_Architecture_v1.md`  
- `Genesis_One_Window_Roadmap_v1.md`  
- `Genesis_Consumer_Platform_Foundation_v1.md`

---

*Audit v1 · Genesis Consumer Platform Foundation*
