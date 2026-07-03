# Guardian — Safety Monitor

**Status:** Architecture approved — **separate module**, not part of Kernel.  
**Code:** not implemented. Brain `pause()` exists today; Guardian will call it.

**Related:** `COMPANY_OS.md` · `KERNEL_GATE.md` (Kernel stays frozen and ignorant)

---

## Why Guardian exists

Genesis must be **predictable**, not just “smart.”

The owner always knows:

- what is happening
- **why**
- how much it costs
- how long it takes
- who stopped the process
- **why it stopped**

Emergency brake, budgets, and API spend **must not** live in Kernel. Kernel only: accept task → plan → run agents → return result.

---

## Placement in stack

```
Brain
  ↓ dispatches
Kernel
  ↓ executes (no knowledge of Guardian)
Guardian          ← observes Brain, Kernel, Skills, spend (sidecar / service)
  ↓ on breach
Emergency Brake   → brain.pause() → Command Center 🔴 EMERGENCY STOP
```

Guardian **observes**. Kernel **does not know** Guardian exists.

---

## Responsibilities

| Guardian watches | Action on breach |
|------------------|------------------|
| Consecutive errors | Pause + alert |
| Queue depth / rate | Throttle or pause |
| Money spent (API, providers) | Pause + alert |
| Token / request count | Pause + alert |
| Skill runtime | Kill job + pause if over budget |
| System uptime / health | Escalate to owner |

### Guardian must block (🔴 / 🟡 without approval)

- Publish without owner confirmation
- Delete projects
- Change licenses or legal terms
- Spend money or API budget over limit
- Wallet or payment actions
- User account changes on behalf of others

Guardian is the **fuse box** — not an “smart AI.” Predictable stops with explainable reasons.

All actions logged with **explainable reason** in audit.

---

## Emergency Brake flow

```
Guardian detects anomaly
        ↓
Guardian.emergency_brake(reason)
        ↓
Brain.pause()          ← already implemented
        ↓
Integration Layer surfaces status
        ↓
Command Center: 🔴 EMERGENCY STOP — {reason}
        ↓
Owner: Resume / Investigate / Fix
```

**🔴 Level 3:** resetting global spend limits or disabling Guardian — owner only.

---

## Resource Budget (per Skill)

Every Skill declares limits. Guardian enforces.

Example — `landing-page-v1`:

```yaml
budget:
  max_duration: 5m
  max_cost_usd: 2.00
  max_api_requests: 300
```

If exceeded mid-job:

```
Guardian → stop job → pause queue → notify owner
"Landing Page exceeded $2.00 budget after 4m 12s (reason: 412 API calls)"
```

Budgets are **Skill metadata**, not Kernel code.

---

## Dry Run (before execution)

Before a job starts, Guardian (or Planner + Guardian preview) shows:

```
Собираюсь создать: Landing Page
Потратить:        ~$0.37
Файлов:           ~24
Время:            ~3 минуты
Лимит Skill:      5 мин / $2 / 300 запросов
```

Owner confirms → job queued. No surprises.

Dry Run is **mandatory** for Level 2+ spend and recommended for all Factory jobs.

---

## Demo Mode alignment

| Demo | Guardian role |
|------|----------------|
| Demo A | All within budget |
| Demo B | Task 3 fails; Guardian logs; queue continues |
| Demo C | 100 tasks; Guardian watches queue depth and health |

---

## Integration Layer (future)

```python
# Future — not built
class GuardianService:
    def preview_job(skill_id, input) -> DryRunEstimate: ...
    def check_budget(skill_id, running_metrics) -> None: ...
    def emergency_brake(reason: str) -> None: ...  # calls brain.pause()
```

Command Center reads Guardian status via Integration Layer — never imports Guardian from UI directly (same rule as Brain).

---

## Kernel freeze rule

**Forbidden in Kernel:**

- Money counters
- API token totals
- Emergency brake logic
- Per-Skill budgets

If any of these appear in Kernel — **reject the change** and move to Guardian.

---

## Build order

1. ✅ Document Guardian (this file)
2. ◯ Demo B — controlled failure (proves Brain continues)
3. ◯ GuardianService stub + tests (no real spend APIs)
4. ◯ Dry Run UI in Command Center (estimates from Skill metadata)
5. ◯ Resource budgets on first Factory Skill
6. ◯ Emergency brake wired to real metrics

---

*Company rhythm: `COMPANY_OS.md` · Kernel rules: `docs/KERNEL_GATE.md`*
