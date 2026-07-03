# Product Lifecycle

**Status:** Foundational — every product in Genesis follows this pipeline.  
**Factory code** implements stages 4–7 first (sandbox); payment/publish later.

**Related:** `COMPANY_OS.md` · `GUARDIAN.md` · `docs/ECONOMY.md`

---

## Universal lifecycle

Every digital product — website, bot, app, API — passes the **same stages**:

```
1.  Idea              ← Research / Ideas / client request
2.  Research          ← demand, competition, “why?” (future)
3.  Plan              ← Brain + Kernel job graph
4.  Create            ← Skill executes in sandbox
5.  Verify            ← QA / Validator
6.  Sandbox           ← isolated artifact, no public internet
7.  Preview           ← owner / client reviews
8.  Revise            ← loop back to Create if rejected
9.  Payment           ← Payment Hub (🟡) — optional for internal tests
10. Publish           ← 🟡 owner / client approval
11. Support           ← tickets, fixes, Skill updates
12. Statistics        ← usage, sales, conversion
13. Improve           ← Evolution proposes changes with “why”
14. New version       ← Skill/template vN+1 → back to Verify
```

**No stage may be skipped** for customer-facing delivery. Internal experiments may stop at Preview.

---

## Stage owners (departments)

| Stage | Primary owner |
|-------|----------------|
| Idea, Research | Research Department |
| Plan | Brain + Planner agents |
| Create | Product / Factory Skill |
| Verify, Sandbox | QA + SandboxGuard |
| Preview, Revise | Command Center + owner |
| Payment | Finance / Payment Hub |
| Publish | 🟡 owner approval |
| Support | Support Department |
| Statistics | Analytics |
| Improve, New version | Evolution + Company Memory |

---

## State machine (simplified)

```
IDEA → RESEARCHED → PLANNED → BUILDING → IN_QA → IN_SANDBOX
  → PREVIEW_READY → [REVISING ↔ BUILDING]
  → AWAITING_PAYMENT → PAID → AWAITING_PUBLISH → LIVE
  → SUPPORTED → MEASURED → IMPROVEMENT_PROPOSED → VERSION_BUMP
```

Failed QA or Guardian budget exceeded → `BLOCKED` with explainable reason.

---

## Dry Run (before Create)

Before stage 4, owner sees (`GUARDIAN.md`):

```
Собираюсь создать: Landing Page
Ориентировочно: 3 мин · $0.37 · 24 файла
Skill budget: max 5 min / $2 / 300 requests
```

Owner confirms → job enters queue.

---

## Sandbox vs Live

| | Sandbox | Live |
|--|---------|------|
| Internet publish | No | Yes (after 🟡) |
| Client money | No | Yes (Payment Hub) |
| Guardian limits | Yes | Yes |
| Audit logged | Yes | Yes |
| Company Memory | Yes | Yes |

---

## First product to prove lifecycle

**Skill:** `landing-page-v1`

Minimum proof (Owner Acceptance + Factory v0.1):

```
Idea (demo) → Plan → Create → QA → Sandbox → Preview → Revise (optional)
```

Payment and Publish = **stubs** until Payment Hub and legal sign-off.

---

## Lifecycle events → audit

Each transition writes to **audit log** (today: `audit.jsonl` via Brain).  
Future: commerce and memory events use the same pattern.

---

*Daily rhythm: `COMPANY_OS.md` · Institutional learning: `COMPANY_MEMORY.md`*
