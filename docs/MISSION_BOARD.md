# Virtus Core — Mission Board (operational lock)

**Locked:** 2026-08-01 · Updated: Farm = orchestrator of connector **roles** (Earn / Execution / Spend / Acquisition).  
**Rule:** Commerce ≠ R&D. Do not mix Path A sales with VRE / Farm Earn experiments.  
**Farm north star:** universal orchestration — **tools execute work; Earn channels collect money; ROI is on the whole operation**, not “how much did Toloka pay us.”

---

## Connector model (canonical vocabulary)

VRE is **not** an exchange and **not** “Toloka”.  
VRE / Farm is the **orchestrator** that plugs external services into roles and compares economics.

```
Farm / VRE
 ├── Earn Connectors         ← money into Virtus (Stripe, Own API, RapidAPI, …)
 ├── Execution Connectors     ← help perform paid work (Toloka, LLM, OCR, browser, …)
 ├── Spend Connectors         ← billed cost of using a tool (often same adapter as Execution)
 ├── Acquisition Connectors  ← find / reach clients (Places, Resend, Country Desk, …)
 └── Payout Manager          ← where REAL sits · official withdraw paths · payout status
```

| Role | Job | Money direction | Example |
|------|-----|-----------------|---------|
| **Earn** | Collect payment for completed work | → Virtus / owner | Path A Stripe · Own API + Stripe · RapidAPI Provider |
| **Execution** | Perform or assist commercial work | usually cost only | Toloka (labeling) · LLM · OCR · browser automation · Scale |
| **Spend** | Accounting view of Execution cost | Virtus → tool | Toloka top-up · OpenAI · Places · VPS |
| **Acquisition** | Bring demand | cost → later Earn | Google Places · outreach / Resend |
| **Payout** | Lifecycle of **already received** funds | Earn balance → bank / PayPal / SEPA | Payout Manager (not an earner) |

One service can wear **two hats** (e.g. Toloka = Execution + Spend). It is **not** required to be an Earn source.

**Canon rule:** Farm evaluates profit on the **completed operation**, not on each tool. A Connector that only executes work is never treated as its own income source.

**Payout rule:** Farm never invents a withdraw method. It records confirmed Revenue and shows **only official** payout options per Earn source.

```
Earn → REAL → Payout Manager → Bank / Stripe / PayPal / Payoneer / SEPA (per platform)
```

### Farm economics (binding KPI)

```
Revenue (confirmed Earn)
− Execution Cost (Toloka, LLM, OCR, browser, …)
− Infrastructure Cost (VPS, domains, Places, Resend, …)
= REAL PROFIT
```

**Wrong KPI:** “How much did Toloka earn?”  
**Right KPI:** “How much profit did the operation make in which Toloka participated?”

| Instrument | Role | Cost | Revenue it helped unlock | ROI read |
|------------|------|------|--------------------------|----------|
| Toloka | Execution + Spend | $20 | €320 (client / Own API) | High if attributed |
| OpenAI | Execution + Spend | €15 | €210 | High |
| Places | Acquisition + Spend | €8 | €180 | High |
| Toloka → Toloka only | — | $20 → $18 | — | **Bad** — reject |

Toloka is like OpenAI: you do **not** wait for it to pay you; you pay it so the farm can deliver paid work cheaper/faster/better.

### Example board (conceptual)

```
Earn
  ● Path A / Stripe           Commercial (Mission 1)
  ○ Own API + Stripe / MPP    Research Rank 1
  ○ RapidAPI Provider         Research Rank 2
Execution / Spend
  ● Toloka Requester          tool (not Earn)
  ● Scale / LLM / OCR         tools
Acquisition
  ● Places / Country Desk     Mission 1
```

Do **not** center strategy on one brand name. Prefer roles: *Earn / Execution / Spend / Acquisition*.
---

## Mission 1 — First Customer (Path A)

**Goal:** first real paying client.

```
Places → Email → Stripe → First €
```

**Success:**
- real payment via Stripe;
- order completes the full path;
- client receives the result.

---

## Mission 2 — Stable Commercial Platform

**Goal:** commercial stack runs 24/7 without the owner laptop.

```
VPS → DNS → Webhook → Monitoring
```

**Success:**
- VPS serves clients 24/7;
- DNS pointed at VPS;
- Stripe webhook on VPS;
- repeatable payments without manual rescue;
- Railway/Vercel retired after observation window.

---

## Mission 3 — Earn Connectors

**Goal:** deliver **at least one working Earn Connector** (legal + confirmed payout) — the unfinished branch of the original Farm design.

**Not the goal:** “make Toloka pay.” Toloka Requester stays **Execution + Spend**. Earn is a separate role (Rank 1–2 unchanged: Own API/Stripe → RapidAPI).

**Status today:** all Earn Connectors = Research (no adapters yet).

```
Research
  → Legal Review          ← mandatory before any adapter
  → Choose Connector      ← exactly one first candidate
  → Prototype (small)
  → One confirmed payout  ← CONFIRMED payout_id / REAL
  → Go / No-Go
```

**Catalog (research, no code):** `docs/EARN_CONNECTOR_RESEARCH_CATALOG_v0.md` — multi-category (B2B API · Data/Labeling · Automation markets · AI Agent markets · HITL). Goal = first legal Earn with best ROI, not Toloka. Shortlist seed: own Stripe/MPP API → RapidAPI Provider → automation templates.

**Spec (no code):** `docs/EARN_CONNECTOR_SPEC_v0.md` — interface · state machine · payout · ledger · requirements. Scaffold only after Legal Review PASS on a real candidate.

**Why Legal Review before code:** many platforms forbid automated performer work. An adapter without ToS green-light is wasted engineering.

**Success (Mission 3):**
- catalog of Earn candidates with honest ToS/API notes;
- Legal Review PASS for the chosen platform;
- one prototype Earn Connector;
- **one confirmed payout** recorded in Farm/VRE truth (REAL);
- explicit Go / No-Go to scale that connector.

**Not Mission 3:** enabling `FARM_LIVE_MODE` for Toloka Spend, auto-submit, or Spend→Country Desk bridge.

---

## VRE product shape (after Mission 1–2)

VRE is a **CEO-only** surface. Clients never see it. Staff only with explicit rights.

### Money truth (UI)

| Field | Meaning |
|-------|---------|
| **REAL** | Confirmed money received (Earn / B2B) |
| **SPENT** | Confirmed tool / experiment cost (Execution billed as Spend) |
| **PREDICTION** | Model estimate — not cash |
| **Execution Cost** | Cost attributed to tools on a job |
| **Infrastructure Cost** | VPS, domains, Places, Resend, … |
| **Revenue Source** | Which Earn channel paid |
| **Payout** | Where REAL sits · official withdraw · status (`/payout`) |
| **ROI / REAL PROFIT** | Revenue − Execution − Infrastructure — per **operation**, not “income from Toloka” |

### VRE measurement levels

| Level | Success criteria |
|-------|------------------|
| **L1** | One controlled job cycle with known cost → verified |
| **L2** | Job history: Revenue Source + Execution Cost + REAL PROFIT |
| **L3** | Avg cost / time / error rate from N jobs |
| **L4** | Compare Connectors by **role** → recommend best ROI per instrument and per Earn channel |

Long-term north star (vision, not a build ticket now):

> Virtus Core orchestrates Earn / Execution / Spend / Acquisition connectors, attributes cost to revenue, and compares ROI of tools and channels.
Farm / VRE **may** become a major income stream later — only after Mission 1 proves Path A and Mission 3 clears Legal Review for Earn.

### CEO Dashboard placement (target)

```
CEO
 ├── Path A / Business
 ├── Finance
 ├── Acquisition / Country Desk
 ├── Factory
 ├── VRE (Experimental)   ← owner only · Connectors board
├── Labs
└── System / Infrastructure
```

---

## Freeze until Mission 1 is closed

Do **not** enable:

- `FARM_LIVE_MODE=live`
- `TOLOKA_AUTO_SUBMIT=1`
- `FARM_AUTO_PREPARE_OUTREACH=1`

Do **not** start Earn connector adapters or Mission 3 engineering until Mission 1 PASS (and preferably Mission 2 underway).

Money Monitor honesty (REAL / SPENT / PREDICTION + Earn OFF) may already be shipped — that is terminology/truth, not Earn live.

---

## Sequence

1. Observe VPS 1–2 days (laptop may be off).
2. Stage 4: DNS → Stripe webhook → one real payment → **Mission 1 PASS**.
3. Stability → **Mission 2**.
4. **Mission 3 — Earn Connectors:** Research → Legal Review → Choose one → Prototype → **One confirmed payout** → Go/No-Go.
5. Only then: scale that Earn Connector (or park it).

## Decision filter

> Does this bring the first paying client closer?

- Yes → Mission 1 / 2.
- No → Mission 3 (Earn Connectors) or Horizon — **no Earn adapter code until Mission 1 PASS + Legal Review**.

> Does this finish a legal Earn channel (money in)?

- Yes → Mission 3.
- “Make Toloka pay us” → **wrong question** — Toloka is Execution + Spend.
- “Does Toloka raise REAL PROFIT on a paid job?” → valid Execution ROI question (after Mission 1).

---

## Architecture note — intent vs wired reality

| Layer | Reality |
|-------|---------|
| Early narrative | Exchange earnings, Withdraw → Stripe |
| Clarified intent | Farm = orchestrator; tools execute; Earn collects; ROI on the **operation** |
| Shipped wiring | Execution/Spend (Toloka requester, LLM, …) + Acquisition (Places) + B2B Earn (Stripe Path A) |
| Earn Connectors (extra channels) | **Research** — Rank 1 Own API/Stripe · Rank 2 RapidAPI |

Automated money **into** Virtus today: **Earn via Path A Stripe** only.
