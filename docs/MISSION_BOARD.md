# Virtus Core — Mission Board (operational lock)

**Locked:** 2026-08-01 · Commerce ≠ R&D. Do not mix Path A sales with Farm/Toloka.

## Mission 1 — First Customer

**Goal:** first real paying client.

**Success:**
- real payment via Stripe;
- order completes the full path;
- client receives the result.

## Mission 2 — Stable Commercial Platform

**Goal:** commercial stack runs stably without the owner laptop.

**Success:**
- VPS serves clients 24/7;
- DNS pointed at VPS;
- Stripe webhook on VPS;
- repeatable payments without manual rescue;
- Railway/Vercel retired after observation window.

## Mission VRE — Verified Revenue Engine

**Goal:** verify economics of new income/spend channels — **not** a client-facing product.

VRE is a **CEO-only** surface (owner). Clients see orders / products / payment only. Staff do not see VRE unless explicitly granted.

### Money truth (UI contract)

Replace “50 nodes = 298 €” style forecasts on the main commercial UI with:

| Field | Meaning |
|-------|---------|
| **REAL** | Confirmed money received (e.g. Stripe) |
| **SPENT** | Confirmed experiment spend (e.g. Toloka requester billing) |
| **PREDICTION** | Model estimate — never presented as cash on hand |
| **ROI** | Only after REAL and SPENT exist for the same channel |

### VRE levels

| Level | Success criteria |
|-------|------------------|
| **L1** | 1 dataset → 1 run → completed → known spend → verified |
| **L2** | Job history with balance before/after (spent fact) |
| **L3** | Avg cost / time / error rate from N jobs |
| **L4** | Compare channels (Toloka / Scale / Appen / Path A / custom) → Go/No-Go |

### Channel roles (architecture)

| Role | Examples | Money direction |
|------|----------|-----------------|
| Spend (labeling) | Toloka Pipeline requester, Scale customer | Virtus → platform |
| Earn (work platforms) | performer/HIT accounts — **not wired today** | platform → owner wallet (manual) |
| Commercial services | Path A Stripe | client → Virtus |

**Original intent vs wired reality:** early Farm/VRE narrative hoped for exchange earnings; the code that shipped is **requester submit + CEO wallet checklist**. Performer payout into Virtus Core was **never implemented**. The only automated money-in path is **Stripe Path A**. See section below.

### CEO Dashboard placement (target)

```
CEO
 ├── Path A / Business
├── Finance
├── Acquisition / Country Desk
├── Factory
├── VRE (Experimental)   ← owner only
├── Labs
└── System / Infrastructure
```

## Freeze until Mission 1 is closed

Do **not** enable:

- `FARM_LIVE_MODE=live`
- `TOLOKA_AUTO_SUBMIT=1`
- `FARM_AUTO_PREPARE_OUTREACH=1`

Do **not** build the VRE CEO tab or remove main-page prediction UI until Mission 1 PASS (unless CEO opens a scoped ticket).

## Sequence

1. Observe VPS 1–2 days (laptop may be off).
2. Stage 4: DNS → Stripe webhook → one real payment → **Mission 1 PASS**.
3. Stability observation → **Mission 2**.
4. Separate day → **Mission VRE L1** (one controlled spend verification).

## Decision filter

> Does this bring the first paying client closer?

- Yes → Mission 1 / 2.
- No → Mission VRE or Horizon.

---

## Architecture note — Was VRE meant to earn?

**Short answer:** Ambition = earn + measure; **shipped wiring** = spend (requester) + manual wallet check. No automated “tasks done → money into Virtus Core” except Stripe.

| Intent layer | What existed |
|--------------|--------------|
| Narrative / UI hints | “выплаты на кошелёк”, VRE steps `wallet_toloka` / `withdraw_path`, forecasts like nodes → € |
| Honest registry | Toloka = requester; “performer wallet = separate account”; Scale = no performer earnings in code |
| Unit economics | Toloka/Scale gross = 0 in this integration; Stripe = real B2B |
| Money back into Virtus | **Only Path A Stripe** is an automated inbound path |

So: VRE should evolve as a **multi-channel verification engine** (spend channels + future earn channels + Path A), not as “Toloka will pay Virtus.”
