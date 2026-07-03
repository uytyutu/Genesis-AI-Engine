# Genesis Roles — Vision vs Implementation

**Status:** Vision map — **not** a build list. Code one phase at a time.

**Constitution:** `WHY.md` · **Daily ops:** `COMPANY_OS.md` · **Lifecycle:** `LIFECYCLE.md`

---

## One sentence (why roles exist)

Genesis is a **digital company where AI fills roles** — not a website generator. Each role owns one concern. The **owner** remains CEO in the real world until Coordinator exists (Phase 4).

**Terminology:** In owner UI and copy, roles are **digital employees** in **departments**. In code, they remain Agents and Kernel plugins until refactored.

> **Do not build “CEO AI” that makes all strategic decisions yet.** Start with reliable single-purpose roles.

---

## Organization (vision)

```
Owner (human)
      │
      ▼
Genesis CEO / Coordinator     ← Phase 4 only (future)
      │
 ┌────┼────────┬──────────┐
 ▼    ▼        ▼          ▼
Analyst  Factory  Finance  Support
 │        │        │         │
 ▼        ▼        ▼         ▼
Market   Builder  Payments  Help
Research Validator Revenue  Tickets
         Publisher Analytics
```

| Role | Responsibility | Knows about |
|------|----------------|-------------|
| **Owner** | Strategy, 🔴 money, approve publish | Everything via Command Center |
| **Analyst** | Data, Ideas, “why” proposals | Stats, Memory — not Kernel internals |
| **Factory** | Build products (Skills) | Templates, sandbox — not payments |
| **Validator** | QA, policy, security gate | Artifact — not publish |
| **Publisher** | Deploy after 🟡 approval | Targets — Guardian must allow |
| **Finance** | Revenue, spend, commissions | Payment Hub — 🔴 owner for payouts |
| **Support** | Owner / client assistant | Live status — not code gen |
| **Guardian** | Limits, emergency brake | Observes — **not inside Kernel** |
| **Coordinator / CEO AI** | Route work between roles | Last — when roles are stable |

---

## Vision ✅ vs Implementation 🔨

| | Vision (document now) | Implementation (code later) |
|--|----------------------|------------------------------|
| Purpose | Map the company | Ship one role at a time |
| Risk | Low — paper | High if all at once |
| Rule | Describe all roles | **Build only current phase** |

---

## Implementation phases (strict order)

### Phase 1 — Prove creation (next after Owner Acceptance)

| Role | Deliverable |
|------|-------------|
| **Factory** | One Skill: `landing-page-v1` → sandbox artifact |
| **Validator** | QA gate on that artifact (tests, checklist) |

**Exit criteria:** Landing built → validated → preview in Command Center → revise loop — **no manual coding by owner**.

### Phase 2 — Real users (after Phase 1 stable)

| Role | Deliverable |
|------|-------------|
| **Publisher** | Publish path with 🟡 approval + Guardian allow-list |
| **Finance** | Payment Hub interface + display revenue/spend (owner 🔴 for payouts) |

### Phase 3 — Learn from usage

| Role | Deliverable |
|------|-------------|
| **Analyst** | Ideas feed, basic stats, “why” cards from Company Memory |

### Phase 4 — Coordinate (last)

| Role | Deliverable |
|------|-------------|
| **Coordinator / CEO AI** | Routes jobs between departments — **never** 🔴 actions alone |

**Forbidden now:** autonomous CEO, full Analyst market scan, live Publisher without Guardian.

---

## Growth without rewriting core

| When | Owner says | New piece |
|------|------------|-----------|
| Today | “Make a website” | Factory Skill: Landing |
| +6 months | “Telegram bot” | New Skill — same Kernel |
| +1 year | “CRM” | New Skill |
| +2 years | “Launch SaaS” | New Skill pack |

Kernel / Brain change rarely. **Skills and roles** grow.

---

## Platform client flow (vision)

```
Client
      ▼
Genesis Platform
      │
 ┌────┴─────┐
 ▼          ▼
Factory   Validator
      │
      ▼
Publisher (🟡)
      │
      ▼
Client receives product
      ▼
Platform commission (Finance + Payment Hub)
```

See `docs/ECONOMY.md` · `docs/MARKETPLACE.md`.

---

## Readiness today (honest)

| Component | Status |
|-----------|--------|
| 🟢 Kernel | Mature foundation — frozen |
| 🟢 Brain | Solid dispatcher |
| 🟢 Command Center + Launcher | Becoming owner product |
| 🟡 Factory | Designed — **does not ship real products yet** |
| ⚪ Validator | Concept — ships with Factory Phase 1 |
| ⚪ Publisher | Idea only |
| ⚪ Finance | Concept (`ECONOMY.md`) |
| ⚪ Analyst | Concept |
| ⚪ Coordinator / CEO AI | **Do not build early** |
| 📋 Guardian | Documented — code later |

**Client value appears when Factory + Validator complete Phase 1.**

---

## One practical goal (~1 month after Factory start)

> **Genesis independently assembles a full landing page, validates it, shows it in Command Center, and prepares it for publish — without owner hand-editing code.**

That proves architecture on paper **and** in process. Then scale to bots, CRM, SaaS via new Skills.

---

*Safety: `GUARDIAN.md` · Memory: `COMPANY_MEMORY.md` · Build order: `BUILD_ORDER.md`*
