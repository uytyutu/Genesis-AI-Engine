# Command Center Architecture v0.1

**Status:** DESIGN + MOCK SCAFFOLD — not connected to Brain yet.  
**Name:** Command Center (never "admin panel")  
**Date:** 2026-07-03

---

## 1. Purpose

**Command Center** is where the owner spends time managing Genesis — the control room of an autonomous company, not a website admin page.

v0.1 goal: **foundation UI + API shape** with mock data. Real Brain integration comes in v0.2 after owner approves the shell.

---

## 2. Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Backend API | **Python + FastAPI** | Same language as Kernel/Brain |
| Frontend | **Next.js + React + Tailwind CSS** | Modern UI, browser + mobile later, tabs without rewrite |
| Data (v0.1) | Mock JSON in API | No Brain wiring yet |
| Data (v0.2+) | FastAPI reads Brain state | Single integration point |

**Not used:** CLI dashboard, single static HTML file, terminal UI.

---

## 3. Architecture diagram (v0.2 — Integration Layer)

```
Browser
   │
   ▼
Next.js (dashboard/frontend)
   │
   ▼
FastAPI routes
   │
   ▼
Integration Layer                    ← v0.2
   ├── BrainAdapter
   ├── HealthService
   ├── TaskService
   └── ModuleStatusService
   │
   ▼
Brain → Kernel (Frozen)
```

**Rule:** Frontend never imports Python. Backend never renders HTML. Clean boundary.

---

## 4. v0.1 screens (one page)

```
┌──────────────────────────────────────────────┐
│               GENESIS ABOS                   │
│            Command Center                    │
├──────────────────────────────────────────────┤
│ Modules (Health Monitor)                     │
│  🟢 Kernel   🟢 Brain   ⚪ Factory  ...      │
├──────────────────────────────────────────────┤
│ Queue                                        │
│  Pending · Running · Completed · Failed      │
├──────────────────────────────────────────────┤
│ Activity (recent events)                     │
├──────────────────────────────────────────────┤
│  [ Pause ]  [ Resume ]  [ Stop ]             │
└──────────────────────────────────────────────┘
```

Future tabs (add without rewrite):

`Overview · Tasks · Agents · Products · Revenue · Factories · Logs · Settings · AI`

---

## 5. API contract (v0.1 mock)

### `GET /api/status`

System summary for header.

```json
{
  "name": "Genesis ABOS",
  "version": "0.1.0",
  "phase": "Command Center v0.1 (mock)",
  "paused": false
}
```

### `GET /api/modules`

```json
{
  "modules": [
    {"id": "kernel", "label": "Kernel", "status": "online"},
    {"id": "brain", "label": "Brain", "status": "online"},
    {"id": "factory", "label": "Factory", "status": "offline"}
  ]
}
```

Status values: `online` | `offline` | `degraded`

### `GET /api/queue`

```json
{
  "pending": 4,
  "running": 1,
  "completed": 27,
  "failed": 0
}
```

### `GET /api/activity?limit=20`

```json
{
  "events": [
    {"at": "13:42", "message": "Task queued", "task_id": "9d2b..."}
  ]
}
```

### `POST /api/control/pause` | `resume` | `stop`

v0.1: return `{"ok": true, "action": "pause"}` — stubs only.

v0.2: call `brain.pause()`, `brain.resume()`, future `brain.stop()`.

---

## 6. File structure

```
dashboard/
├── README.md
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI app, CORS, routes
│       ├── schemas.py       # Pydantic models
│       └── mock_data.py     # v0.1 fake data
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── postcss.config.mjs
    ├── tsconfig.json
    └── app/
        ├── layout.tsx
        ├── globals.css
        └── page.tsx         # Command Center UI
```

---

## 7. Future: Brain adapter (v0.2 — not built)

```python
# dashboard/backend/app/brain_adapter.py  (future)

def get_queue_stats(brain: Brain) -> QueueStats: ...
def get_activity(audit: AuditStorage, limit: int) -> list[ActivityEvent]: ...
```

Command Center backend imports Brain — Brain and Kernel stay unchanged.

---

## 8. Out of scope v0.1

- Real Brain / Kernel connection
- Factory, Revenue, CEO AI UI
- WebSockets (polling OK for v0.1)
- Authentication (local dev only — add before public deploy)
- Charts and graphs (layout reserved)

---

## 9. Setup (owner)

**Requires Node.js 20+** (not yet on dev machine) and Python 3.11+.

```powershell
# Backend
cd dashboard/backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal, after Node install)
cd dashboard/frontend
npm install
npm run dev
```

Open http://localhost:3000

---

## 10. Approval checklist

- [x] FastAPI + Next.js stack approved
- [x] Mock-only v0.1 (no Brain wire)
- [ ] Owner installs Node.js and verifies UI
- [ ] v0.2: connect Brain adapter after UI approved

---

*Command Center — not an admin panel. The owner's operating console.*
