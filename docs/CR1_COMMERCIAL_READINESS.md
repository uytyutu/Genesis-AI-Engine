# CR1 — Commercial Readiness (Owner)

**Status: NOT READY** — starts only after **RC1 Certification PASS** (`docs/RC1_CERTIFICATION.md`).

Ads: **not yet**. Small budget only after this checklist; scale only after Owner 499 € shame-test.

## Gate order

```text
RC1 A/B/C/D PASS
      ↓
CR1 Commercial Ready
      ↓
5–10 €/day ads → first 5 clients
      ↓
feedback loop → scale
```

## CR1 checklist (Owner)

| # | Item | Result | Date |
| --- | --- | --- | --- |
| 1 | `/site` — 10s: what / get / price / buy (no jargon) | ☐ | |
| 2 | Catalog = Standalone Website+Shop · Connected +AI · honest add-ons only | ☐ | |
| 3 | All vitrine images load · demos open · no twin Heroes · no broken links · DE natural · no i18n keys · mobile OK | ☐ | |
| 4 | Factory: Interview→…→Media QA→Browser QA→Export; **no images = no export** | ☐ | |
| 5 | Business Workspace: Hero / logo / photo / AI edit / publish without developer | ☐ | |
| 6 | **10 etalon demos** (list below) — unique visual + DE + niche + mobile | ☐ | |
| 7 | Owner would buy ~499 € and recommend (shame-test) | ☐ | |

## 10 etalon niches

1. Beauty Studio  
2. Restaurant  
3. Dentist  
4. Auto Repair  
5. Cleaning  
6. Law  
7. Real Estate  
8. IT Company  
9. Electrician  
10. Hotel  

(Unique Visual Identity + Media History bind — no shared Heroes.)

## First 5 clients (goal after CR1)

Different niches e.g. dental · restaurant · auto · beauty · cleaning.  
Loop: use → feedback → permanent fix or auto-QA → next client.

## Defect law

Every defect → gone forever **or** automatic QA check.

Note (2026-08-08): Backend `main.py` annotation `Path` vs `_Path` broke cold start → Repair loop. Fixed; treat module-import NameError as Stability P0.

## Not in CR1

3D · Video Pipeline · Social Studio scale · Farm extensions · «one more engine»
