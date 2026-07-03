# Brain Flow — v0.1

Understand Brain in one minute. No code required.

---

## Diagram

```
Task (UUID task_id)
        │
        ▼
   ┌─────────┐
   │  Brain  │  dispatcher only — no AI, no strategy
   └────┬────┘
        │
        ├──────────────────┐
        ▼                  ▼
 QueueStorage        AuditStorage
        │                  │
        ▼                  ▼
   queue.json         audit.jsonl
        │
        │ run_next() picks first QUEUED
        ▼
   ┌─────────┐
   │ Kernel  │  FROZEN — submit(task)
   └────┬────┘
        │
        ▼
     Agents
        │
        ▼
     Result → lifecycle COMPLETED or FAILED
              → events in AuditStorage
```

---

## One task lifecycle

```
enqueue(task)
   NEW → QUEUED
   events: task.created, task.queued
   saved to QueueStorage

run_next()
   QUEUED → RUNNING
   event: task.started
   Kernel.submit(task)
   RUNNING → COMPLETED | FAILED
   event: task.completed | task.failed
   kernel audit copied to AuditStorage

cancel(task_id)
   QUEUED → CANCELLED
   event: task.cancelled
```

---

## What Brain does NOT do (v0.1)

- Decide strategy
- Analyze market
- Internet / Telegram / payments
- Create products (Factory)
- AI planning

---

## UUID

Every task has `task_id` = UUID (from Kernel `Task.id`).  
Example: `9d2b5d2f-a1c4-4e7b-9f3a-1b2c3d4e5f6a`

Never use sequential numbers like "Task #17".

---

## Pause / Resume (reserved)

```python
brain.pause()   # run_next() returns None while paused
brain.resume()  # normal operation
```

Dashboard will use this later. v0.1: simple in-memory flag.

---

## Integration proof

```
Queue → Brain → Kernel → Audit
```

See `tests/test_brain.py` — all must pass before Command Center.
