# Earn Connector Specification v0

**Status:** Specification only — **no implementation**.  
**Locked with:** `docs/MISSION_BOARD.md` · Mission 3 — Earn Connectors  
**Rule:** Do not scaffold code until **one** legal Earn candidate passes Legal Review.

---

## Purpose

Define a **platform-agnostic** contract for Farm Earn (second income stream), so Virtus Core can later plug in any **officially supported** earn channel without redesigning CEO money truth (REAL / SPENT / ROI).

This document is **not** a promise that such a channel exists today. Discovery of the first candidate is a **prerequisite** to coding.

---

## Order of work (binding)

```
Research
  → 1 confirmed Earn candidate (facts: API + payout + ToS)
  → Legal Review PASS
  → Scaffold against that real contract
  → Prototype
  → One CONFIRMED payout (REAL)
  → Go / No-Go
```

**Forbidden now:** Earn Layer scaffold, Toloka Performer, “enable Live to get €”.

---

## Out of scope

- Spend Connectors (Toloka/Scale requester)
- Path A / B2B Stripe (company revenue)
- Client-facing UI
- Circumventing platform ToS / botting human-judgment markets

---

## 1. Earn Connector Interface (logical)

A connector is an adapter that speaks **one** platform dialect and exposes this contract to the Earn Orchestrator.

### Required capabilities (declare in `capabilities()`)

| Flag | Meaning |
|------|---------|
| `discover` | Can list available paid work |
| `claim` | Can reserve a unit of work (optional per platform) |
| `submit` | Can return results via official API |
| `payout_status` | Can read approval/paid state |
| `balance_read` | Can read earn wallet balance |
| `payout_history` | Can list paid events with external ids |
| `webhook` | Platform pushes events (optional) |
| `withdraw_api` | Official programmatic withdraw (rare; usually false) |
| `tos_automation` | `allowed` \| `restricted` \| `forbidden` \| `unknown` |

### Logical methods

| Method | Intent | Notes |
|--------|--------|-------|
| `capabilities()` | What this connector supports | Must be honest; drives orchestrator |
| `health()` | Key valid, role = earn, API up | Fail closed if role is spend/customer |
| `discover_work(limit, filters)` | List payable work units | Official API only |
| `claim(work_ref)` | Reserve work | **Optional** — skip if platform has no claim |
| `execute(job, context)` | Produce result | Only modes allowed by ToS (human / API / hybrid) |
| `submit(job_ref, result)` | Deliver result | Platform contract |
| `payout_status(job_ref \| batch_ref)` | pending / approved / rejected / paid | |
| `read_balance()` | Earn balance if API exists | Else `unsupported` |
| `list_payouts(since)` | Paid events | Must yield external payout ids when possible |
| `normalize_payout(raw)` | Map to `ConfirmedPayout` | Single ledger shape |
| `withdraw_hint()` | Human steps for official withdraw | Never auto-bypass |
| `supports_destination(kind)` | card / bank / stripe / wallet / other | From platform docs |

### Contract flexibility

Platforms differ. The orchestrator **must** tolerate:

- no `claim` (direct submit or assign-by-webhook);
- webhook-first flows (`discover` may be empty; jobs arrive via webhook);
- payout only via dashboard (connector reports `paid` after poll or CEO confirm);
- currencies other than EUR (store native + optional FX note).

**v0 rule:** interface methods are **logical**; first scaffold maps 1:1 to the **chosen** candidate’s real API, then generalizes.

---

## 2. Job state machine

```
DISCOVERED
  → CLAIMED            (if claim exists; else skip)
  → EXECUTING
  → SUBMITTED
  → PENDING_REVIEW
  → APPROVED | REJECTED
  → PAID_EXTERNAL      (platform paid into its wallet)
  → CONFIRMED_REAL     (Virtus ledger has CONFIRMED payout)
  → WITHDRAW_REQUESTED (optional, manual or official API)
  → WITHDRAWN_EXTERNAL (optional, CEO/platform confirmed)
```

### Terminal meanings

| State | Money truth |
|-------|-------------|
| `REJECTED` | No REAL; may still incur SPENT (LLM/infra) |
| `PAID_EXTERNAL` | Money on platform; not yet Virtus REAL until normalized |
| `CONFIRMED_REAL` | Counts toward Farm **REAL** |
| `WITHDRAWN_EXTERNAL` | Off-platform (card/bank/Stripe); still Farm history |

---

## 3. Payout model

### `ConfirmedPayout` (minimum fields)

| Field | Required | Description |
|-------|----------|-------------|
| `connector_id` | yes | e.g. future `clickworker_v1` |
| `external_job_id` | preferred | Platform job/HIT id |
| `external_payout_id` | yes for REAL | Idempotent payout / transfer id |
| `amount` | yes | Decimal |
| `currency` | yes | ISO code |
| `paid_at` | yes | ISO timestamp |
| `confidence` | yes | Must be `CONFIRMED` for REAL |
| `raw_ref` | yes | Pointer to stored raw API payload |

### Confidence ladder

| Level | Use |
|-------|-----|
| `SIMULATED` | Dry-run / internal estimate — never REAL |
| `ESTIMATED` | Expected pay before platform approval |
| `CONFIRMED` | Platform (or CEO-attested official statement) proves paid |

**REAL +=** only `CONFIRMED` Earn payouts.  
Path A Stripe settlements stay in **Business REAL**, not Farm REAL.

---

## 4. Ledger & money truth (Farm)

| Bucket | Definition |
|--------|------------|
| **REAL** | Σ CONFIRMED Earn payouts |
| **SPENT** | Attributable costs of Earn jobs (LLM, API, infra, fees) |
| **PREDICTION** | Model from measured L3 stats — not cash |
| **ROI** | `(REAL − SPENT) / SPENT` if SPENT > 0 else `—` |

### Ledger requirements

- Append-only event log (job transitions + payouts).
- Idempotent ingest on `external_payout_id`.
- Never mark local swarm `estimate_eur` as REAL.
- Never mix Spend (requester billing) into Earn REAL.

### Withdraw

- Virtus does **not** invent card/SEPA rails.
- Withdraw = official platform path → card / bank / Stripe / Payoneer / etc.
- Earn Layer records hint + optional `WITHDRAWN_EXTERNAL` after evidence.
- “Any card / any currency” is **not** a Virtus guarantee; it is whatever the **connector’s platform** supports (`supports_destination`).

---

## 5. Orchestrator requirements (logical)

- Respect `tos_automation`; refuse auto-execute if `forbidden`.
- Rate limits / circuit breaker (reuse existing farm patterns conceptually).
- Persist job state across restarts.
- Emit VRE L1 event when first CONFIRMED_REAL appears.
- CEO-only surface; never expose to clients.

---

## 6. Legal Review gate (before any scaffold)

For a candidate platform, document:

1. Allowed work model (human / API worker / hybrid).
2. Explicit ToS stance on automation.
3. Official payout methods and minimums.
4. Whether an API (or supported integration) exists for discover/submit/payout.
5. Account type required (worker vs customer).
6. Go / No-Go.

**No scaffold without Legal Review PASS.**

---

## 7. Reuse vs new (when coding starts — not now)

| Reuse later | Build later |
|-------------|-------------|
| Channel board Earn/Spend/B2B | `EarnConnector` protocol + registry |
| Finance ledger `payout_id` ideas | Job state machine persistence |
| Worker Research Lab catalog | Orchestrator wired to real API |
| VRE L1–L4 checklist | Farm REAL separate from Path A |
| Money Monitor truth UI | Withdraw advisor (hints only) |

---

## 8. Acceptance of this spec

Spec v0 is **done** when:

- [x] Interface, states, payout, ledger, requirements written
- [ ] First Earn candidate named with evidence
- [ ] Legal Review PASS
- [ ] Then (and only then) code scaffold against that contract

---

## 9. Explicit non-goals of v0

- Choosing Toloka / Scale / MTurk / etc. as “the” Earn channel
- Implementing adapters
- Promising 50–100 €/day or “200–300 €”
- Auto-withdraw to arbitrary cards

**North star after Mission 1:** find **one** legal Earn channel → confirm payout → then turn this spec into code.
