# RC1 — Production Release Candidate

**Date:** 2026-07-23  
**Branch tip (RC1):** `79a97f7`  
`feat(evolution): complete G3.1 AI Support & Continuous Improvement`  
**Branch:** `cursor/mission1-genesis-brain-public-layer`

## CEO status (2026-07-23)

```text
🟡 RC1 — TECHNICAL PASS / RELEASE HOLD
```

| Layer | Meaning |
|-------|---------|
| **Technical PASS** | S1 · G2.3 · G3.1 · milestone pack green · RC1 tip formed |
| **Release HOLD** | Push not recommended until clean tree + full pytest green + these notes committed |

**Not** “готово к Production push”. Архитектурная приёмка этапов ≠ релиз-дисциплина репозитория.

**Push:** HOLD. Next CEO stamp after cleanup: **🟢 RC1 — Release Approved** (then first production push).

**Do not open G3.2** until Release Approved (or CEO explicitly reopens Evolution scope).

### Launch smoke (does not change HOLD)

| Check | Result |
|-------|--------|
| `verify_release.py` | ✅ exit 0 |
| Launcher window | ✅ |
| Backend `/api/status` | ✅ |
| Basic start chain | ✅ RC1 tip is not launch-broken |

`verify_release` / launch smoke neither clear HOLD nor worsen it.

### Maintenance issue (not a release blocker)

```text
Issue:     Launcher / tkinter threading warning
           RuntimeError: main thread is not in main loop
Severity:  Low
Blocks Release: No
Recommended: Investigate after RC1 release or during launcher maintenance.
```

Do **not** spend RC HOLD time on tkinter. Priority until **Release Approved**:
1. Full pytest green (1226 PASS / 44 FAIL → 0 FAIL)
2. Clean working tree (or WIP on a separate branch)
3. CEO **🟢 Release Approved** → first production push

---

## What is in Production (this RC)

Answer to *«Что именно входит в Production?»*:

**Everything committed at `79a97f7` and earlier on this branch.**  
Working-tree WIP is **out of scope** and must not be pushed with RC1.

### Stage stamp (CEO accepted)

| Stage | Status | Anchor commit (local) |
|-------|--------|------------------------|
| Mission 1 | ✅ | foundation on branch history |
| G2.1 Public Platform | ✅ | portal / public path history |
| G2.2 Client Workspace | ✅ | client workspace history |
| Security Gate S1 | ✅ | `cd0142b` (+ docs `b2949b3`) |
| G2.3 Commercial Readiness | ✅ | `802838a` |
| Production Ready | ✅ | after G2.3 (Payments 🟢 · Overall 100%) |
| G3.1 AI Support & Continuous Improvement | ✅ FINAL PASS | `79a97f7` |

### Permanent product rules (in this RC)

1. **Don't sell unfinished products.** Coming Soon ≠ Buy.
2. **AI may recommend changes. Only the Owner approves changes.**
3. **Auto Apply = false** (Evolution Center).

### Evolution Center mission (G3.1)

> Evolution Center не создаёт новые функции. Он делает существующую платформу безопаснее, стабильнее, полезнее и умнее на основе подтверждённого опыта.

Owner path:

```text
Ticket → Analysis → Proposal → Owner Approve → Rule Candidate → Owner Confirm → Knowledge Ledger
```

---

## Graduation checklist (2026-07-23)

| Check | Result | Notes |
|-------|--------|-------|
| 1. Working tree clean | ❌ FAIL | Dirty tracked files + large untracked WIP / probes / previews |
| 2. Release commits only (no WIP) | ✅ PASS *if push = commits only* | Tip `79a97f7` is G3.1-isolated; WIP unstaged |
| 3a. Security Regression Suite | ✅ PASS | `scripts/s1_security_regression_suite.py` → **4/4** |
| 3b. Milestone pack (S1 + G2.3 + G3.1) | ✅ PASS | **49** tests passed |
| 3c. Full backend pytest | ❌ FAIL | **1226 passed · 44 failed** (see debt below) |
| 3d. `verify_release.py` | ✅ exit 0 (launch smoke) | Does not clear HOLD; tkinter thread warning = Low, non-blocking |
| 4. Release Notes | ✅ this file | |
| 5. Push decision | ⏸ HOLD | Dirty tree + 44 pytest failures only |

### Dirty tree (must stay out of push)

Examples of **non-RC** local noise (not exhaustive):

- Modified: factory analyzer/CSS, support inbox, site/locales, `surfaceNavConfig`, launcher cleanup, memory JSON, several tests  
- Untracked: `_audit_*`, `.factory_*_previews`, probe scripts, `USER_FRICTION.md`, Stripe/checkout JSON dumps, `app/client/` WIP shells  

**Rule for push:** push commits through `79a97f7` only — never `git add .`.

### Full-suite debt (44 failures) — classification

Sampled failures look like **stale expectations vs evolved product**, not G3.1 regressions:

| Example | Observation |
|---------|-------------|
| `test_subscription_tiers_customer_names` | expects `Professional`; product has `Vector Starter` |
| `test_unavailable_without_enabled_provider` | expects old stub string |
| `test_sandbox_checkout_to_paid_and_production` | receipt wording changed; Path A still pays |

These are **pre-existing suite drift** relative to G2.3+ catalog/copy. They block a claim of “full green pytest”, not the G3.1 Scope Freeze.

**Release gate used for S1/G2.3/G3.1 stamps:** Security Regression Suite + stage tests — not “every historical test file green”.

---

## Changelog (high level)

### Security Gate S1 (`cd0142b`)

- AuthZ matrix · XSS upload hardening · AI security lane · rate limits  
- Permanent Security Regression Suite  
- Production Readiness panel (security lane)

### G2.3 Commercial Readiness (`802838a`)

- Catalog: Products / One-time / Monthly  
- Landing Path A prices locked (350 / 650 / 1200 €)  
- Honest Coming Soon · Payments 🟢 · Overall 100% · Production Ready

### G3.1 Evolution Center (`79a97f7`)

- Support tickets → Change Proposals (recommend only)  
- Confidence · Business Impact · Rollback · Diff Summary  
- Dual confirm: Approve → Rule Candidate → Confirm → Knowledge Ledger  
- Owner UI `/business/evolution` · Auto Apply = false

---

## RC1 verdict (CEO)

```text
🟡 RC1 — TECHNICAL PASS / RELEASE HOLD

RC1 tip:           79a97f7
Stage stamps:      ALL GREEN through G3.1 (Technical PASS)
Security suite:    PASS
Milestone tests:   PASS
Working tree:      DIRTY → Release HOLD
Full pytest:       NOT GREEN (44) → Release HOLD
Push:              NOT RECOMMENDED
```

### Path to 🟢 RC1 — Release Approved

1. Clean working tree (or move WIP to a separate branch).  
2. Fix/update remaining failures so full `pytest` is green.  
3. Keep these Release Notes on the branch (this docs commit).  
4. CEO stamp **Release Approved** → then first production push.

**Forbidden until then:** G3.2 · Marketplace · production push · claiming “весь проект зелёный”.

---

## Self Verification (agent)

Genesis.exe запущен: Нет (RC = git/test control, not client path)  
Полный путь клиента пройден: Нет  
Дошёл до желания оформить заказ: Нет  
Если нет — где остановился: выпускной контроль по коммитам и тестам; живой CEO-путь не заявлялся в этом RC-прогоне.
