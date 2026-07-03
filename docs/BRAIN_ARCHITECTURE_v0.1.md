# Brain Architecture v0.1

**Status:** APPROVED with amendments — Step 1 implementation in progress.  
**Date:** 2026-07-02 (amended)  
**Phase:** 1 (Brain v0.1)

**Kernel:** Frozen — no changes without owner approval.

---

## 1. Purpose

**Brain is the dispatcher.** It decides **which task runs next** and **keeps a permanent record**. It does not plan steps, run agents, or execute work — that is Kernel's job.

| Layer | Question it answers |
|-------|---------------------|
| **Kernel** | How do I run this one task? |
| **Brain v0.1** | What task is next? What already ran? What is still waiting? |

---

## 2. Rules (non-negotiable)

1. **Kernel is Frozen.** Brain uses `GenesisKernel.submit()` only.
2. No internet, money, Telegram, Factory, Dashboard UI in v0.1.
3. Single process — no threads, no async, no Redis, no PostgreSQL in v0.1.
4. Storage behind interfaces — swap JSON for SQLite/PostgreSQL later without rewriting Brain.

---

## 3. High-level diagram (amended)

```
Owner / future Command Center
              │
              ▼
        ┌───────────┐
        │   Brain   │
        │           │
        │  enqueue  │──► TaskQueue ──► QueueStorage ──► queue.json (v0.1)
        │  run_next │                              └──► PostgreSQL (future)
        │  emit()   │──► AuditStorage ──► audit.jsonl (v0.1)
        └─────┬─────┘                  └──► SQLite / PostgreSQL (future)
              │ submit(task)
              ▼
        ┌───────────┐
        │  Kernel   │  FROZEN
        └───────────┘
```

**Key amendment:** Brain never writes files directly. It uses `QueueStorage` and `AuditStorage` interfaces.

---

## 4. Task lifecycle (amended)

Every task in Brain has a lifecycle independent of Kernel's `TaskStatus`:

```
NEW
 ↓
QUEUED
 ↓
RUNNING
 ↓
COMPLETED | FAILED | CANCELLED
```

| State | Meaning |
|-------|---------|
| `NEW` | Record created, not yet in queue |
| `QUEUED` | Waiting in FIFO queue |
| `RUNNING` | Kernel is executing |
| `COMPLETED` | Kernel returned success |
| `FAILED` | Kernel returned failure |
| `CANCELLED` | Owner or Brain removed before/during run |

Kernel `TaskStatus` stays internal to Kernel. Brain `TaskLifecycle` is for Dashboard and queue management.

---

## 5. Internal events (amended)

Brain emits events from day one. In v0.1 they are **written to AuditStorage** (same as other log lines). No Event Bus yet — but the shape is ready for Dashboard to subscribe later.

| Event | When |
|-------|------|
| `task.created` | Record created (`NEW`) |
| `task.queued` | Moved to `QUEUED` |
| `task.started` | State → `RUNNING`, before `kernel.submit()` |
| `task.completed` | State → `COMPLETED` |
| `task.failed` | State → `FAILED` |
| `task.cancelled` | State → `CANCELLED` |

Event shape:

```json
{
  "at": "2026-07-02T22:00:00+00:00",
  "event": "task.started",
  "task_id": "abc-123",
  "task_name": "analyze-bots",
  "lifecycle": "running"
}
```

Brain code calls `audit_storage.append_event(event)` — Brain does not know if backend is JSONL or PostgreSQL.

---

## 6. Storage interfaces (amended)

### 6.1 `QueueStorage` (Protocol)

| Method | Purpose |
|--------|---------|
| `load_all() -> list[QueuedTaskRecord]` | Read all task records |
| `save_all(records: list[QueuedTaskRecord]) -> None` | Replace persisted queue state (atomic write) |

**v0.1 implementation:** `JsonQueueStorage` → `memory/queue.json`  
**Future:** `PostgresQueueStorage` — same interface, Brain unchanged.

### 6.2 `AuditStorage` (Protocol)

| Method | Purpose |
|--------|---------|
| `append_event(event: dict) -> None` | Append one event (JSON line in v0.1) |
| `append_events(events: list[dict]) -> None` | Batch append (e.g. copy Kernel audit) |

**v0.1 implementation:** `JsonlAuditStorage` → `memory/audit.jsonl`  
**Future:** `SqliteAuditStorage` / `PostgresAuditStorage` — Brain unchanged.

---

## 7. Module structure

```
brain/
├── __init__.py
├── models.py              # TaskLifecycle, QueuedTaskRecord, BrainEvent helpers
├── brain.py               # Brain facade (Step 3)
├── config.py              # BrainConfig (Step 3)
├── queue.py               # TaskQueue service — FIFO + lifecycle (Step 3)
└── storage/
    ├── __init__.py
    ├── queue_storage.py   # QueueStorage + JsonQueueStorage  ← Step 1
    └── audit_storage.py   # AuditStorage + JsonlAuditStorage  ← Step 2

memory/                     # runtime (gitignored)
tests/
├── test_queue_storage.py   ← Step 1
├── test_audit_storage.py   ← Step 2
└── test_brain.py           ← Step 3

examples/
└── run_brain_demo.py       ← Step 4
```

---

## 8. Classes

### 8.1 `TaskLifecycle` (Enum)

`NEW | QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED`

### 8.2 `QueuedTaskRecord`

| Field | Type |
|-------|------|
| `task_id` | str |
| `task_name` | str |
| `payload` | dict |
| `goal` | serialized dict or null |
| `lifecycle` | TaskLifecycle |
| `created_at` | ISO timestamp |
| `updated_at` | ISO timestamp |

Methods: `from_task(Task) -> QueuedTaskRecord`, `to_task() -> Task`

### 8.3 `Brain` (Step 3 — not built yet)

```python
Brain(kernel, queue_storage, audit_storage, config)
```

| Method | Behaviour |
|--------|-----------|
| `enqueue(task)` | `NEW` → `QUEUED`, emit `task.queued`, save queue |
| `run_next()` | `QUEUED` → `RUNNING` → kernel.submit → `COMPLETED`/`FAILED`, emit events |
| `cancel(task_id)` | → `CANCELLED`, emit `task.cancelled` |
| `run_all()` | Drain queue (tests/demo) |

---

## 9. Sequence — one task (with lifecycle + events)

```
1. brain.enqueue(task)
      lifecycle: NEW → QUEUED
      event: task.created, task.queued
      queue_storage.save_all(...)

2. brain.run_next()
      lifecycle: QUEUED → RUNNING
      event: task.started
      result = kernel.submit(task.to_task())
      lifecycle: RUNNING → COMPLETED | FAILED
      event: task.completed | task.failed
      audit_storage.append_events(kernel.audit_log + brain events)
      queue_storage.save_all(...)

3. Brain restart
      queue_storage.load_all() → QUEUED tasks still waiting
```

---

## 10. Implementation steps (mandatory order)

| Step | Deliverable | Tests |
|------|-------------|-------|
| **1** | `QueueStorage` + `JsonQueueStorage` + `models.py` | `test_queue_storage.py` | ✅ Done |
| **2** | `AuditStorage` + `JsonlAuditStorage` | `test_audit_storage.py` | ✅ Done |
| **3** | `TaskQueue` + `Brain` | `test_brain.py` | ✅ Done |
| **4** | `run_brain_demo.py` | manual | ✅ Done |
| **4** | `run_brain_demo.py` | manual |
| **5** | Kernel integration gate | 11 kernel + N brain tests |

**Do not implement multiple steps in one pass.**

---

## 11. Tests — Step 1 (`test_queue_storage.py`)

| # | Test |
|---|------|
| 1 | Load returns empty list when file missing |
| 2 | Save and load round-trip |
| 3 | FIFO order preserved in file |
| 4 | All `TaskLifecycle` values persist |
| 5 | `Goal` serialization round-trip (all types) |
| 6 | `from_task` / `to_task` round-trip |
| 7 | Atomic write — file always valid JSON after save |

**Gate after Step 1:** Step 1 tests pass + 11 kernel tests still pass.

---

## 12. Tests — Step 2 (`test_audit_storage.py`)

| # | Test |
|---|------|
| 1 | Append creates file |
| 2 | Each line is valid JSON |
| 3 | Events preserve order |
| 4 | `task.started` event shape |

---

## 13. Tests — Step 3 (`test_brain.py`)

| # | Test |
|---|------|
| 1 | enqueue → QUEUED + event in audit |
| 2 | run_next → Kernel called, COMPLETED |
| 3 | FIFO order |
| 4 | Failed task → FAILED lifecycle + task.failed event |
| 5 | cancel → CANCELLED |
| 6 | Queue persists across Brain restart |
| 7 | run_next on empty returns None |

**Final gate:** 11 kernel + ~17 brain storage/brain tests.

---

## 14. Advantages (with amendments)

- Storage swappable — PostgreSQL later without Brain rewrite
- Lifecycle ready for Dashboard
- Events ready for Command Center subscription
- Kernel stays Frozen
- Step-by-step implementation reduces rewrite risk

---

## 15. Risks

| Risk | Mitigation |
|------|------------|
| Over-abstraction in v0.1 | Only two small Protocol interfaces |
| `save_all` rewrites whole queue | Fine for thousands of tasks; batch later if needed |
| RUNNING task on crash | Document; v0.2 can add recovery |
| Scope creep | One step per Cursor session |

---

## 16. Out of scope for v0.1

CEO AI, Opportunity, Revenue, Capital, World Model, Evolution, Factory, Dashboard UI, Event Bus process, PostgreSQL, Redis, Docker, async.

---

## 17. Approval

- [x] Owner + architect conditionally approved (2026-07-02)
- [x] Four amendments incorporated in this document
- [x] Step 1 authorized

---

*Amended per architect review. Kernel Frozen at v0.1.0.*
