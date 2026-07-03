# Integration Layer v0.1

**Status:** Implemented — Command Center uses this layer only.

---

## Rule

```
Launcher
      ↓
Command Center (UI + FastAPI)
      ↓
Integration Layer (services only)
      ↓
Brain → Kernel (Frozen)
      ↓
Skills / Sandbox

Guardian (future) — observes Brain/Skills; calls brain.pause(); NOT inside Kernel
```

UI **never** imports `brain` or `kernel`.  
FastAPI routes **never** call `Brain` directly — only services below.

Full stack: `docs/COMPANY_OS.md`

---

## Components

| Service | Role |
|---------|------|
| `BrainAdapter` | Wraps Brain + Kernel bootstrap (Echo agent for v0.1) |
| `HealthService` | Live checks: kernel, brain, queue, audit |
| `ModuleStatusService` | Health → module list for UI |
| `TaskService` | Create, list, run, cancel tasks; queue stats; activity |

Future adapters (not built): `FactoryAdapter`, `RevenueAdapter`, etc.

---

## API (live)

| Method | Path | Action |
|--------|------|--------|
| GET | `/api/tasks` | List all tasks (UUID, status, timing) |
| POST | `/api/tasks` | Create task |
| POST | `/api/tasks/run-next` | Run one queued task |
| POST | `/api/tasks/{id}/cancel` | Cancel queued task |
| POST | `/api/control/pause` | `brain.pause()` |
| POST | `/api/control/resume` | `brain.resume()` |

---

## Tests

`tests/test_integration_layer.py` — 6 integration tests  
Full suite: **53 passed**

---

## Owner workflow

1. Start backend (`dashboard/README.md`)
2. Start frontend (Node.js required)
3. Open **Tasks** — create, run, cancel, see UUID and results
4. **Overview** — live health, queue counts, activity

Factory **not started** until this workflow is verified in browser.
