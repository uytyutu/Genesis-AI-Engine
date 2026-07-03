# Brain Roadmap — design only, not implemented

**Status:** PLANNING — do not implement until Kernel gate passes.

Brain sits **on top of** Kernel. Brain calls `GenesisKernel.submit()`. Kernel code does not change.

---

## Brain v0.1 — queue + log

**Goal:** Run multiple tasks through Kernel without manual scripts.

| Feature | Description |
|---------|-------------|
| Task queue | FIFO list of tasks waiting to run |
| Brain.submit() | Add task to queue |
| Brain.run_next() | Pull one task, call Kernel, store result |
| File audit log | Append kernel audit + results to `memory/audit.jsonl` |

**Proof:** 3 tasks queued → 3 results stored → audit file readable.

**Not in v0.1:** scheduling, policy, UI.

---

## Brain v0.2 — schedule + policy

| Feature | Description |
|---------|-------------|
| Time-based trigger | Run queue every N minutes (simple loop, no cron service) |
| Policy Tier 0 | Auto-run safe tasks |
| Policy Tier 1 | Run + notify owner (log flag) |
| Policy Tier 2 | Hold until owner approves (in-memory approve list) |

**Proof:** Tier 2 task stays queued until `brain.approve(task_id)`.

---

## Brain v1.0 — Command Center ready

| Feature | Description |
|---------|-------------|
| Daily summary API | Return last 24h: tasks run, successes, failures, total duration |
| Pending approvals list | Tasks waiting for owner |
| Stable Brain API | Command Center can call Brain without touching Kernel |

**Proof:** JSON summary matches audit file.

---

## Architecture sketch

```
Command Center (future)
        │
        ▼
    Brain API
   queue · policy · log
        │
        ▼
  GenesisKernel.submit()
        │
        ▼
     Agents
```

---

## Owner approval required before

- [ ] Kernel gate passed (11 tests green)
- [ ] Owner approves Brain v0.1 design
- [ ] Implementation of Brain v0.1 only (not v0.2 + v1.0 at once)
