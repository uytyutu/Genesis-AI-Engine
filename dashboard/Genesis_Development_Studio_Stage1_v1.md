# Genesis Development Studio — Stage 1

**Date:** 2026-07-04  
**Status:** Implemented (CEO Desktop)  
**Goal:** Genesis Desktop as primary dev workplace — Cursor as engine behind the UI

---

## Delivered

### 1. Cursor Handoff Panel (Desktop)

**Nav:** Development Studio → **Cursor Handoff**

| Feature | Status |
|---------|--------|
| Active / history AI Hub tasks | ✅ |
| Change plan + approve gate | ✅ |
| Cursor task steps + verify | ✅ |
| Handoff history | ✅ |
| Perfect Pallet / Genesis project picker | ✅ |

**Not in browser** — `client/desktop/src/components/CursorHandoffPanel.tsx`

### 2. AI Hub API

| Endpoint | Purpose |
|----------|---------|
| `POST /api/ai-hub/tasks` | Create plan from text |
| `POST /api/ai-hub/tasks/{id}/approve` | Approve → Cursor dispatch |
| `POST /api/ai-hub/tasks/{id}/verify` | pytest + report |
| `GET /api/ai-hub/tasks` | History |
| `GET /api/ai-hub/providers` | Provider registry |

**Service:** `ai_hub/ai_hub_service.py` · Plan → Approve → Act (Law №1)

### 3. Development Workspace (scaffold)

**Tab:** Workspace

| Module | Status |
|--------|--------|
| Projects (Genesis + Perfect Pallet) | ✅ |
| File list (read-only, capped) | ✅ |
| Build history (cursor + hub tasks) | ✅ |
| AI Suggestions | ✅ |
| Docs list API | ✅ backend |

### 4. Consumer Chat attachments (architecture)

`client/shared/chat/attachments.ts` — classify PDF, Word, Excel, code, audio, …  
Desktop Chat: attach + drag-drop chips (upload API = Stage 2)

### 5. Voice architecture

`client/shared/voice/types.ts` — STT providers scaffold (Stage 1b)

### 6. Dogfood First rule

> **Любая новая возможность сначала в CEO Workspace.**

Added to `.cursor/rules/genesis-development.mdc`

---

## CEO flow (today)

1. Open **Development Studio** in Desktop  
2. Enter task: *«Добавь систему инвентаря в Perfect Pallet»*  
3. Review **plan** → **Утвердить**  
4. Cursor opens (semi-auto) — paste prompt  
5. **Проверить результат** in Genesis  
6. See history — never open browser `/cursor`

---

## Perfect Pallet path

Set on API host:

```bash
GENESIS_PERFECT_PALLET_PATH=D:\Games\Perfect Pallet
```

---

## Next (Stage 1b)

- Voice input (Web Speech / native STT)  
- Attachment upload API  
- LLM plan generation (provider router Stage 2)  
- Auto-refresh verify when Cursor completes  

---

## Related

- `Genesis_AI_Hub_Architecture_v1.md`  
- `Genesis_One_Window_Roadmap_v1.md`  
- `Genesis_Hybrid_AI_Strategy_v1.md`
