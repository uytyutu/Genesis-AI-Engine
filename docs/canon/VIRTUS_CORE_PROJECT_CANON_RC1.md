# Virtus Core — Project Canon (RC1)

**Document ID:** `VIRTUS_CORE_PROJECT_CANON`  
**Version:** RC1 / v1.1  
**Date:** 2026-07-23  
**Audience:** Owner · future CTO · investor (30-minute read)  
**Living rule:** After each major stage (G3.x, service lifecycle PASS), bump version (v1.1, v1.2) and regenerate PDF.  
**Source of truth:** this file + stamped facts in `docs/COMMERCIAL_VALIDATION.md` · `docs/RC1_PRODUCTION_RELEASE_NOTES.md`

---

## 0. Product Decision Log

| ID | Date | Decision | Why | Status |
|----|------|----------|-----|--------|
| **PD-E1** | 2026-07-23 | Outreach allocation uses **`per_market`**; regional hard limit is **500**. **`shared_global` is not the RC1 operating mode** (config fallback only until a separate decision). **Single-mailbox** (≤1 From address): regional `GENESIS_OUTREACH_DAILY_CAP` does **not** stack on global + per-market quotas — intentional for Mission 1 one-domain setup. | Match live v6 market config + scalable hard max; fix tests to canon; document bypass so it is never mistaken for a bug. | **Accepted** (Category E Decision #1 / Option C) |
| **PD-E2** | 2026-07-23 | **Withdraw balance is ledger-backed.** `finance_settlements.jsonl` is the source of truth; `finance_snapshot.json` is derived via `_sync_settlement_snapshot`. Hand-written snapshot balances are not withdrawable. Tests must fund via settlement/`record_payment` (or equivalent), not raw snapshot fields. | Align withdraw tests with intentional Finance Layer (no unverified earned sums). | **Accepted** (Category E Decision #2) |

---

## 1. Executive Summary

### What it is

**Virtus Core** is a digital company operating system for small businesses: a public storefront of digital services, checkout, client workspace, and **Vector** — an AI business consultant — under Owner control.

It is **not** a chat toy. AI is a tool inside the ecosystem.

### Mission

> We do not sell websites. We help businesses solve digital problems.

Website · AI assistant · automation · analysis are instruments. The goal is the right outcome for the client **and** sustainable revenue for Virtus Core.

### Vision

A client opens Virtus Core to continue work with **their** digital company — products, orders, Vector, improvements — not to “try another chatbot”.

### Permanent principles (non-negotiable)

| Principle | Meaning |
|-----------|---------|
| **Solve Digital Problems** | Recommend repair when honest; new site when better for the client |
| **Don't sell unfinished products** | Coming Soon ≠ Buy |
| **AI may recommend. Only the Owner approves** | Evolution / platform changes |
| **Auto Apply = false** | No silent code changes |
| **Reality over Features** | Ship what can be verified on the CEO path |
| **One slice = one commit** | Independently revertible |

### Audience

- DE/EU SMB owners (Path A: landing websites first)  
- Owner / CEO (Mission Control, Business Health, Evolution)  
- Future operators / CTO / investors reading this Canon

### RC1 status (honest)

```text
🟡 RC1 — TECHNICAL PASS / RELEASE HOLD
```

Stages through **G3.1** are CEO-stamped. **Push held** until: clean working tree + full pytest green + Release Approved.  
**S0 Storefront First** committed (`fc40e44`). **Website Analysis v1** — Scope Freeze in progress (may be uncommitted at PDF build time).

---

## 2. Product Philosophy

```text
Storefront sells products
        ↓
Vector helps choose (consultant)
        ↓
Checkout only for finished delivery paths
        ↓
Client Workspace continues the project
        ↓
Evolution improves the platform from confirmed experience
```

**Wrong framing:** “We have AI — let’s talk.”  
**Right framing:** “Here are digital solutions. If you need help choosing — ask Vector.”

---

## 3. Architecture (system map)

```text
Public /site (Storefront)
        ↓
Products · Analysis · Coming Soon honesty
        ↓
Order (/order) · Packages Basic/Business/Premium
        ↓
Payments (Landing Path A · Stripe/sandbox)
        ↓
Client Workspace (/client)
        ↓
Vector (consultant · chat secondary)
        ↓
Mission Control · Business Health (Owner)
        ↓
Evolution Center (/business/evolution)
        ↓
Rule Candidate → Knowledge Ledger
```

**Launcher law:** Genesis.exe = lifecycle only (start/stop/alive). No Git-based product decisions.

**Python:** backend 3.12 (`runtime.txt`).

---

## 4. Modules (status map)

| Module | Purpose | Status | Buy? | Notes |
|--------|---------|--------|------|-------|
| **Storefront `/site`** | What can I buy? | ✅ S0 | — | Chat secondary (Ask Vector) |
| **Landing Website** | Basic 350 · Business 650 · Premium 1200 | ✅ G2.3 | Yes | Path A |
| **Website Analysis v1** | URL → report → options | 🔄 Scope | Free diagnostic → Order website | Repair/SEO Coming Soon |
| **Website Repair** | Fix existing site | Coming Soon | No Buy | Priced in catalog |
| **SEO / Speed / Security** | Audits & opts | Coming Soon | No Buy | From Analysis recommendations |
| **Factory** | Generate landings | ✅ Mission 2 | via Order | Owner/factory tools |
| **Payments** | Checkout Path A | ✅ G2.3 | Yes | Landing only |
| **Client Workspace** | Client after purchase | ✅ G2.2 | — | |
| **Vector** | AI Business Employee / consultant | ✅ foundation | Activate / Coming Soon SKUs | Not the first screen |
| **Mission Control** | Owner daily path | ✅ | — | Via Genesis.exe |
| **Business Health** | Readiness lanes | ✅ | — | |
| **Evolution Center** | Support → learn | ✅ G3.1 | — | Owner dual confirm |
| **Knowledge Ledger** | Confirmed rules | ✅ G3.1 | — | After 2nd confirm |
| **Marketplace** | — | Frozen | — | Not opened |

**Dependencies (simplified):** Storefront → Order → Payments → Client; Analysis → recommendations → Order or Coming Soon; Evolution → Owner → Ledger (never auto-apply).

---

## 5. Commercial model

### Buyable today (Path A)

| Package | Price | CTA |
|---------|-------|-----|
| Landing Basic | **350 €** | Order |
| Landing Business | **650 €** | Order (recommended) |
| Landing Premium | **1200 €** | Order |

### Catalogued · Coming Soon (priced, not Buy)

AI Website Analysis (product SKU) · Website Repair · SEO Audit · Speed · Security · Google Business · Migration · Vector monthly tiers · CRM · Automation — **Coming Soon ≠ Buy**.

### Rule

> Don't sell unfinished products.

---

## 6. Customer Journey

```text
Visitor
  → Storefront (/site)
  → (optional) Website Analysis
  → Repair* | SEO* | New Website
  → Checkout
  → Paid
  → Client Workspace
  → Support / Vector
  → (Owner) Evolution learns from confirmed cases

* Coming Soon until delivery lifecycle exists
```

**3-click rule (S0):** Home → Package card → Order.

---

## 7. Business Logic (Analysis → offer)

```text
Website Analysis
        ↓
Health score + real checks only
        ↓
If site healthy & few issues → prefer Repair (when available)
If many gaps / repair ≈ new site cost → prefer Business Website
If SEO/speed only → SEO/Speed (when available)
        ↓
Always explain why (justification)
        ↓
Never invent check results
```

Principle: **Solve Digital Problems.**

---

## 8. Vector

### Is

- Face of the hired digital team  
- Consultant: need → option → preview/order  
- Secondary on `/site` (Ask Vector), not the hero  

### Is not

- Auto-changer of platform code  
- Unrestricted marketplace seller  
- Replacement for Owner approval on Evolution  

### Decisions

- Language Constitution (reply language = user messages)  
- Public chat via Genesis Brain; Sales Slice B (visual concept) **parked** until it lives on product cards  
- Analysis recommendations use locked prices and Coming Soon honesty  

### Evolution link

Vector/support may create tickets → Evolution proposals → Owner only applies knowledge after dual confirm. **Applied = false** always for code.

---

## 9. Evolution Center

```text
Ticket
  → Analysis
  → Proposal (Confidence · Impact · Rollback · Diff Summary)
  → Owner Approve
  → Rule Candidate
  → Owner Confirm
  → Knowledge Ledger
```

**Mission:** make the platform safer/stabler/smarter from **confirmed** experience — does not invent new product features.

**Auto Apply = false** (permanent until deliberate review).

---

## 10. Security

| Gate | Result |
|------|--------|
| Security Gate S1 | ✅ FINAL PASS |
| Permanent suite | `scripts/s1_security_regression_suite.py` |
| Freeze | Lifted after S1; Overall never 100% while a lane is yellow |

**Why:** production readiness requires green security lane; every vulnerability → permanent test.

---

## 11. Release History (stamped)

```text
Mission 1 ✅
G2.1 Public Platform ✅
G2.2 Client Workspace ✅
Security Gate S1 ✅   → cd0142b
G2.3 Commercial Readiness ✅ → 802838a
Production Ready ✅
G3.1 Evolution ✅ → 79a97f7
RC1 notes → 4209796
S0 Storefront First ✅ → fc40e44
Website Analysis v1 🔄 Scope Freeze
```

RC1 tip for “stages complete” story: through G3.1; S0 is post-G3.1 storefront UX.

---

## 12. Diagrams (index)

See sections 3, 6, 7, 9 — keep diagrams ASCII in PDF; Mermaid optional in Markdown viewers.

---

## 13. Roadmap

| Ready | Not opened / frozen |
|-------|---------------------|
| Path A websites + payments | Marketplace |
| Storefront-first `/site` | Auto-apply Evolution |
| Evolution G3.1 | G3.2 until Release Approved |
| Analysis v1 (in progress) | Full Repair/SEO delivery lifecycles |
| | Payment Hub / Gewerbe until first real client € |

---

## 14. Constraints (do not violate)

1. Don't sell unfinished products  
2. AI recommends · Owner approves · Auto Apply = false  
3. No Marketplace without explicit Scope Freeze  
4. One logical slice = one commit; no WIP in release commits  
5. Launcher never uses Git for process control  
6. No Brain/Conversation Pipeline rewrites without acceptance gates  
7. RC1 push only after Release Approved  

---

## 15. Appendix (pointers)

| Area | Location |
|------|----------|
| Commercial canon | `docs/COMMERCIAL_VALIDATION.md` |
| RC1 release notes | `docs/RC1_PRODUCTION_RELEASE_NOTES.md` |
| Storefront | `dashboard/frontend/app/site/SitePage.tsx` |
| Analysis v1 | `dashboard/backend/app/integration/website_analysis_v1.py` |
| Evolution | `dashboard/backend/app/evolution/` |
| Security suite | `scripts/s1_security_regression_suite.py` |
| Public analysis API | `POST /api/public/website-analysis` |
| Owner Evolution UI | `/business/evolution` |
| Catalog (FE) | `dashboard/frontend/app/lib/commercialCatalog.ts` |
| Catalog (BE) | `dashboard/backend/app/integration/commercial_catalog_g23.py` |

### Versioning

| Version | When |
|---------|------|
| **v1.0 / RC1** | Initial Canon |
| **v1.1 / RC1** | Product Decision Log + PD-E1 (outreach caps) |
| **v1.2+** | After next major PASS (e.g. Analysis FINAL · Repair lifecycle · Release Approved) |

Regenerate PDF: `py -3.12 scripts/build_project_canon_pdf.py`

---

*End of Project Canon RC1 v1.1*
