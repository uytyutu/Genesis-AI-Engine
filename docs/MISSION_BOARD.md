# Virtus Core — Mission Board (operational lock)

**Locked:** 2026-08-01 · Updated: Mission 3 renamed to **Earn Connectors**.  
**Rule:** Commerce ≠ R&D. Do not mix Path A sales with VRE / Farm Earn experiments.  
**Farm north star:** finish the **Earn branch** — not “make Toloka pay.”

---

## Connector model (canonical vocabulary)

VRE is **not** an exchange and **not** “Toloka”.  
VRE is the **engine that evaluates and compares external connectors**.

```
VRE
 ├── Earn Connectors      ← platforms pay Virtus / owner (Research)
 ├── Spend Connectors     ← Virtus pays for labeling / work
 └── B2B Connectors       ← clients pay Virtus (Path A)
```

| Connector class | Money direction | Status today |
|-----------------|-----------------|--------------|
| **Earn Connectors** | Platform → Virtus / owner wallet | **Research** — none wired as performer payout |
| **Spend Connectors** | Virtus → platform | Wired as requester (e.g. Toloka Pipeline, Scale customer) |
| **B2B Connectors** | Client → Virtus (Stripe) | **Live path** — Mission 1 frontline |

Example board (conceptual):

```
Earn
  ○ Channel A          Research
  ○ Channel B          Research
Spend
  ● Toloka Requester   Spend connector
  ● Scale Labeling     Spend connector
B2B
  ● Path A / Stripe    Commercial
```

Do **not** center strategy on one brand name. Prefer: *Earn / Spend / B2B Connectors*.

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

## Mission 3 — VRE Research (Earn Connectors)

**Goal:** find **legal, automatable Earn Connectors** and decide Go / No-Go — **before** writing performer adapters.

**Status of all Earn Connectors:** Research (not build).

```
Research
  → Choose Earn Connector candidate(s)
  → Legal Review          ← mandatory gate
  → Prototype (small)
  → One real payout
  → Decision (develop / park / reject)
```

**Why Legal Review before code:** many platforms forbid automated performer work. Building an adapter first risks an unusable integration.

**Success (Mission 3):**
- shortlist of candidate Earn Connectors with ToS/API stance documented;
- Legal Review done for the chosen candidate;
- optional: one controlled prototype + one real payout fact;
- explicit Go / No-Go for further engineering.

**Not Mission 3:** enabling `FARM_LIVE_MODE`, Toloka auto-submit, or Spend→Country Desk bridge.

---

## VRE product shape (after Mission 1–2)

VRE is a **CEO-only** surface. Clients never see it. Staff only with explicit rights.

### Money truth (UI)

| Field | Meaning |
|-------|---------|
| **REAL** | Confirmed money received |
| **SPENT** | Confirmed experiment / API spend |
| **PREDICTION** | Model estimate — not cash |
| **ROI** | Only when REAL and SPENT exist |

### VRE measurement levels

| Level | Success criteria |
|-------|------------------|
| **L1** | One controlled job cycle with known cost (Spend or Earn) → verified |
| **L2** | Job history with balance before/after |
| **L3** | Avg cost / time / error rate from N jobs |
| **L4** | Compare Connectors → recommend best ROI |

Long-term north star (vision, not a build ticket now):

> Virtus Core connects external Earn / Spend / B2B connectors, measures their economics, and compares ROI.

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
4. **Mission 3:** Research → Choose → **Legal Review** → Prototype → One payout → Decision.
5. Only then: Earn connector engineering if Go.

## Decision filter

> Does this bring the first paying client closer?

- Yes → Mission 1 / 2.
- No → Mission 3 (Research) or Horizon — **not** code on Earn adapters yet.

---

## Architecture note — intent vs wired reality

| Layer | Reality |
|-------|---------|
| Early narrative | Exchange earnings, Withdraw → Stripe |
| Shipped wiring | Spend Connectors (requester) + B2B Stripe |
| Earn Connectors | **Research** — no performer payout adapter in Virtus |

Automated money **into** Virtus today: **B2B Connector (Stripe Path A)** only.
