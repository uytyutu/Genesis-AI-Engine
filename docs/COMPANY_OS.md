# Genesis Company Operating System

**Status:** Foundational document — how Genesis operates **every day** as a digital company.  
**Not code.** Describes rhythms, handoffs, and owner touchpoints.

**Related:** `LIFECYCLE.md` · `COMPANY_MEMORY.md` · `GUARDIAN.md` · `DIGITAL_COMPANY_VISION.md`

---

## What this is

This is not a feature list. It is the **daily operating system** of Genesis — the loop the company runs whether the owner is awake or not (within 🟢 sandbox rules).

> **Genesis does not “live alone.” Genesis evolves as a digital company using accumulated experience and new Skills.**

---

## Platform stack (Engine vs UI)

**Engine and UI are strictly separated.** Any future interface reuses the same services:

```
Launcher                    ← one-click start (owner)
      ↓
Command Center              ← Web UI today; Desktop / Mobile / Telegram Admin later
      ↓
Integration Layer           ← only entry to engine (BrainAdapter, services)
      ↓
Services                    ← Task, Health, Owner, Assistant, Timeline, (future: Factory, Guardian…)
      ↓
Brain                       ← queue, dispatch, pause/resume, audit
      ↓
Guardian (future)           ← safety, budgets, emergency brake — NOT in Kernel
      ↓
Kernel (frozen)             ← task → plan → agents → result
      ↓
Skills                      ← Website, Telegram, CRM… (sandbox)
      ↓
Sandbox
```

Future clients on the **same Integration Layer**:

- Web Command Center ✅
- Desktop Command Center
- Mobile app
- Telegram admin bot
- REST API (public)
- CLI (dev only)

**Rule:** UI never imports `brain` or `kernel`. Guardian never lives inside Kernel.

---

## Daily company rhythm (24h)

### Night shift (🟢 Level 1 — sandbox only)

```
00:00–06:00  Autonomous work (if enabled)
             ├── Health check loop
             ├── Retry failed sandbox jobs
             ├── Draft new template variants
             ├── Run QA on pending Skills
             ├── Fix known template bugs
             └── Write audit + Company Memory events
```

Owner is **not** disturbed. Nothing publishes. No payments.

### Morning wake-up (06:00)

```
06:00  System wake
         ↓
       Health check (Kernel, Brain, Queue, Audit, Services)
         ↓
       Review queue (pending, running, failed overnight)
         ↓
       Check new / updated Skills (internal or store candidates)
         ↓
       Analyze errors (Guardian metrics when live)
         ↓
       Prepare morning brief for owner
         ↓
       WAIT for owner or client tasks
```

**Morning brief (Command Center):**

> Доброе утро, {owner}. Пока ты спал: N задач, M продуктов в sandbox, K ошибок исправлено, 3 идеи в Ideas. Рекомендация: {why}.

### Business hours — order received

```
Client / owner request
         ↓
Intent understood (Ideas / chat / form)
         ↓
Dry Run shown (cost, time, files) — see GUARDIAN.md
         ↓
Owner / client confirms (🟡 if paid)
         ↓
Planner (Brain + Kernel job)
         ↓
Skill (Factory department)
         ↓
QA
         ↓
Sandbox artifact
         ↓
Preview in Command Center
         ↓
Approve / Revise
         ↓
Payment (Payment Hub) — 🟡
         ↓
Publish — 🟡
         ↓
Analytics event → Company Memory
```

### End of day

```
Aggregate stats (tasks, errors, spend, Skill usage)
         ↓
Self-analysis proposals (“why improve template v7?”) — future Evolution
         ↓
Evening summary in audit + optional owner notification
         ↓
Queue overnight sandbox jobs (🟢)
```

---

## Owner touchpoints (human in the loop)

| Moment | Owner action |
|--------|----------------|
| Morning | Read brief; approve overnight proposals (optional) |
| New order | Approve Dry Run; pay if client-facing |
| Preview | ✔ Approve or ✏ Revise |
| Publish | 🟡 Approve |
| Emergency | 🔴 Guardian stopped system — read why, resume |
| Strategy | Ideas — pick niche → Create |

Owner work should trend toward **approvals and strategy**, not terminals.

---

## Demo Mode (prove predictability)

Demo is **training wheels** for the operating system — not fake marketing.

| Scenario | Purpose | Status |
|----------|---------|--------|
| **Demo A** | 5 tasks, all complete — happy path | ✅ Implemented |
| **Demo B** | Task 3 fails; 4–5 continue — resilience | 📋 Planned |
| **Demo C** | 100 tasks — queue, Brain, Kernel, health under load | 📋 Planned |

Owner must see: Genesis is **predictable** — errors do not silently corrupt the company.

---

## Departments in the daily loop

| Department | Daily role |
|------------|------------|
| CEO Office | Brief, priorities, approve Level 2/3 |
| Research | Feed Ideas (future) |
| Product / Factory | Execute Skills |
| QA | Validator gates |
| Support | Assistant answers owner |
| Finance | Payment Hub (future) |
| Guardian | Watch limits, trigger emergency brake |

---

## What “done” means for Company OS v1

One full cycle works without terminal:

1. Launcher — one click start
2. One Skill — Landing in sandbox
3. Preview in Command Center
4. Revise path exists
5. Ready for publish (stub 🟡 — no live money yet)

Then expand: Demo B/C, Guardian, Company Memory writes, night shift.

---

## Anti-patterns

- Putting money, API limits, or emergency logic **inside Kernel**
- UI calling Brain directly
- Skipping Dry Run before expensive Skills
- Promising autonomous “living” without sandbox and audit

---

*Product lifecycle: `LIFECYCLE.md` · Memory: `COMPANY_MEMORY.md` · Safety: `GUARDIAN.md` · Constitution: `WHY.md`*
