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
| **Commercial Validation** | Market proof | **← CURRENT** |
| Mission 3 | Client Platform (Business Dashboard evolution) | Later |
| Mission 4 | Premium Workspace | Later |
| Mission 5 | Platform Expansion | Later |

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

When several real orders exist, open **Mission 3** (and later stages) from **evidence** —  
not from a feature wishlist.
