# Commercial Validation

**Rule:** Новые крупные функции добавляются только тогда, когда они решают проблему, подтверждённую реальными пользователями или аналитикой.

**Status:** ACTIVE (2026-07-21)  
**Mode:** market proof — not feature building  
**Prior mission:** Mission 2 — **COMPLETE**

## Roadmap

| Stage | Theme | Status |
|-------|--------|--------|
| Mission 0 | Foundation | ✅ |
| Mission 1 | Public Launch | ✅ |
| Mission 2 | Factory + Order Experience | ✅ |
| **Commercial Validation** | Market proof | **ACTIVE** (parallel) |
| **Mission 3** | Perception → semantics → market → portal | **OPEN** |
| Mission 4 | Premium Workspace | Later |
| Mission 5 | Platform Expansion | Later |

## Mission 3 — REORDERED (2026-07-21, CEO)

**Why opened early:** Visual Product Audit + 3-second Premium Test = **FAIL** (then improved).  
**Why reordered again:** Niche sweep (8 niches) proved Media Intelligence is size/aspect only —  
Beauty / Computer / Green heroes off-topic. Systemic algorithm gap, not dental-only.

| Slice | Theme | Status |
|-------|--------|--------|
| **R3.1** | **Premium Visual System** | **≈ READY — CEO Premium Test** |
| **R3.2** | **Section-Aware Media Gate** | **IN PROGRESS** |
| **R3.3** | **Section-Aware Content Gate** | After R3.2 |
| R3.4 | Global Market Experience | After R3.3 |
| R3.5 | Client Portal Foundation | After R3.4 |

**Not now:** full «Semantic Content Engine» · new LLM stack · CRM · Dashboard · particles.  
**Horizon (Premium, later):** Visual Style at order (Classic White / Soft Gradient / AI bg / upload) — not R3.2.

### Owner Visibility Rule (binding)

> If the product owner opens the screen and does not see the claimed improvement **without hints**, the improvement is **not done** — regardless of lines of code or internal checkboxes.

### Premium Test (R3.1 acceptance)

Show **Basic / Business / Premium** with **no names and no prices**. Ask: *Which is the most expensive?*  
PASS = ≥ **8 / 10** pick Premium immediately.

**2026-07-21 before:** FAIL. **After Premium Visual:** agent + CEO feedback ≈ 8–8.5/10 — **CEO closes R3.1**.  
Evidence: `_audit_visual_dental_r31/sandbox/compare-3sec.html` (:8767).

### Section-Aware Media Gate (R3.2 — definition)

**Goal:** not «generate better» — **do not publish illogical sites**.

Small smart step — **not** a new generator / not a new neural net / **no LLM**.

```
niche + section → allowed categories → media tag → PASS / FAIL
```

On FAIL: swap image · or mark FAIL · never publish an obviously illogical result.

**Publish path:** Quality Gate → **Media Gate** → Publish.

| Block | Expectation (example) | Fail → |
|-------|----------------------|--------|
| Hero | Face / customer result / front-of-house matching niche | swap / reject |
| Gallery | Interior / team / real work — not random tech dump | swap |
| Services | Relates to services of **this** niche | swap |
| About | Team / owner / office | swap |
| Contact | Facade / map / entrance / reception | swap |

Niche deny examples (Hero): Beauty ≠ restaurant/florist/industry · Computer ≠ flowers/café/dental · Green ≠ cosmetics/restaurant.

Today (before): `niche → hash hero slot → pixel gate → insert`.  
Target: `niche → page → **which block?** → what user expects → pick → **meaning check** → insert`.

**Acceptance (R3.2):** multi-niche sweep — Auto · Beauty · Law · Restaurant · Green · Computer · Dental · Handwerk.  
Off-topic hero in any niche = **FAIL**. Same Owner Visibility Rule.

Evidence baseline: `_audit_niche_sweep/` + canvas `niche-semantic-sweep`.  
Module: `dashboard/backend/app/factory/media_gate.py`.

### Section-Aware Content Gate (R3.3 — definition)

Same idea for **copy**: no generic «Beratung / Umsetzung / Support» when niche has real services.  
Each section text must pass niche relevance — or FAIL quality gate.

### Frozen until later slices

Global Market · Client Portal · Premium Visual Style picker · full Semantic Content Engine.

## Mission 2 — CLOSED

| Capability | Status |
|------------|--------|
| Factory v1 | ✅ |
| Order Experience v2 | ✅ |
| Analytics (A2.1 funnel) | ✅ |
| Commercial Ready | ✅ |

Architecture point set. No large new directions until real buyers validate the path  
(visit → order → pay → Factory/Compliance delivery → result).

**Frozen unless critical bug:** client cabinet, CRM, calendar, blog, AI-chat expansions, heavy integrations.

## Guiding question

> Does the market confirm that what we built actually delivers value?

Not: «What else should we build?»

## Focus (only these four)

1. **First real users** — get people to start an order; watch behavior  
2. **First real payments** — full live chain (Stripe → Factory → Compliance → delivery → notify)  
3. **Funnel check** — Money Monitor → Order Experience Funnel; where drop-off concentrates  
4. **Feedback patterns** — repeating questions/friction only (ignore one-offs until they repeat)

## Decision journal (facts only)

Add one row (or one dated section) after each real observation window.  
Improvements listed here must cite funnel numbers or repeating friction — not gut feel.

### Template

| Field | Value |
|-------|--------|
| Date | YYYY-MM-DD |
| Visitors (approx.) | |
| Order started | |
| Reached step 2 / 3 / 4 | |
| Checkout summary viewed | |
| Stripe redirect | |
| Paid | |
| Drop-off hotspot | |
| Problems (live chain) | |
| Repeating feedback | |
| Decision (if any) | Based on: … |
| Next check | |

---

### Entries

_(none yet — first real traffic / payment opens Entry 1)_

<!--
### YYYY-MM-DD — Entry N

- Visitors:
- Order started:
- Paid:
- Drop-off:
- Problems:
- Feedback pattern:
- Decision:
-->

## Where to look

- Funnel card: Money Monitor / Business KPI → **Order Experience Funnel**  
- Events: `memory/pricing_analytics.jsonl` (via existing Path A analytics)  
- Order UX notes (shipped slices): `docs/ORDER_EXPERIENCE_CHANGELOG.md`

## After validation

Commercial Validation stays **ACTIVE** in parallel (real orders / funnel).  
Mission 3 opened on **owner-visibility evidence** (Premium Test FAIL → Premium Visual).  
After R3.1 PASS → R3.2 Media Gate → R3.3 Content Gate → market → portal.  
Later stages still wait on market proof where noted.
