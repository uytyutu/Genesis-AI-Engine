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

## Mission VRE — Verified Revenue Engine (Toloka)

**Goal:** measure labeling-channel economics (not B2B sales).

**Success:**
- one controlled live run;
- cost known;
- duration known;
- quality known;
- decision: develop further or keep as experiment.

## Freeze until Mission 1 is closed

Do **not** enable:

- `FARM_LIVE_MODE=live`
- `TOLOKA_AUTO_SUBMIT=1`
- `FARM_AUTO_PREPARE_OUTREACH=1`

## Sequence

1. Observe VPS 1–2 days (laptop may be off).
2. Stage 4: DNS → Stripe webhook → one real payment → **Mission 1 PASS**.
3. Stability observation → **Mission 2**.
4. Separate day → **Mission VRE**.

## Decision filter

> Does this bring the first paying client closer?

- Yes → Mission 1 / 2.
- No → Mission VRE or Horizon.
