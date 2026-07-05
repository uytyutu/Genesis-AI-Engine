# Genesis Autonomy Levels

**Status:** Future Roadmap · Research layer  
**Implementation:** Stage 1 UI after Mission 1 stable · Stage 2+ after commercial milestones  
**Principle:** Autonomy grows; Production reliability stays first.

**Memory:** `dashboard/backend/memory/research/genesis_autonomy_levels.json`

---

## Core idea

Genesis should **reduce CEO involvement over time**, not increase it. Autonomy is staged — not all-at-once.

---

## Stage 1 — Now (Production focus)

Genesis works; **reports what it did**. CEO sees an activity journal — no approval queue for every step.

**Example — Research (Architecture Freeze safe):**

```text
🟢 Genesis Activity
• Video model research completed
• Research Note #009 added
• Usefulness score: 92/100
• Decision: saved to Research
• Production was not modified
```

**Example — Production maintenance (when allowed by policy):**

```text
🟢 API cache optimized
🟢 Internal bug fixed
🟢 Performance +8%
🟢 All tests passed
```

CEO reads the log. **Reality over Features** — every line must be true.

**UI target (future):** Mission Control → **Genesis Activity** panel.

**Not now:** build only after Mission 1 does not suffer.

---

## Stage 2 — After Stable

Genesis **decides within approved policy** without per-action CEO clicks:

- fix errors (safe class)
- update documentation
- improve performance
- optimize costs
- prospect clients
- draft proposals
- market analysis
- publish content per approved strategies

Bounded by **CEO Decisions** + Truth Layer + tri-filter (revenue · reliability · CEO time).

---

## Stage 3 — Long-term (Digital CEO)

Genesis optimizes toward goals CEO sets:

- notices high-profit services
- adjusts campaigns
- launches landings, A/B tests
- scales winners, cuts losers
- weekly report: *«Profit +18% because …»*

CEO sets **goals and limits**; Genesis chooses path.

**Morning vision — Genesis Daily Report:**

```text
• Fixed: 4 safe issues
• Performance: +6%
• Found: 3 potential clients
• Sent: 3 proposals
• Published: 5 pieces
• New order: 1
• Revenue today: €245
• Recommended: scale winning campaign
```

### Self-improvement loop (after Digital CEO)

Beyond daily reports, Genesis runs a **continuous improvement cycle** — not waiting for CEO commands to evolve:

```
Observe → Think → Plan → Act → Verify → Learn
```

| Step | Role |
|------|------|
| **Observe** | Market, clients, errors, trends, profit |
| **Think** | Multi-model analysis |
| **Plan** | Choose best action path within policy |
| **Act** | Execute safe actions only |
| **Verify** | Did it actually get better? (Truth Layer) |
| **Learn** | Store in Memory (Learning / Knowledge) |

Genesis becomes **continuous improvement**, not one-shot automation.

---

## Hard limit — Garage vs Production

**Never** unlimited autonomous Production code changes. Strong AI can break working systems.

| Zone | Autonomy |
|------|----------|
| **Garage** | Free experiment — code, test, delete, rebuild |
| **Production** | Auto-apply **only safe changes** that pass tests, linters, quality gates, no regressions |
| **Risky changes** | Garage first → validation → promotion path |

Same path as Media Engine:

```
Research → Garage → Validation → Stable → Production
```

Aligns with Runtime Migration, Truth Layer, Dogfooding, Release Guardian.

---

## Spending limits — no automatic money without budget

Genesis may act freely on **non-financial** work:

- publish content (within strategy)
- write code in Garage
- fix safe Production bugs
- market analysis
- send commercial proposals (no spend)

**Requires pre-approved budget and rules** — never automatic without limits:

- API purchases
- subscriptions
- paid advertising
- server rental above budget
- any financial commitment

CEO sets **budget caps**; Genesis operates inside them or asks.

CEO decision: `dec-2026-07-05-no-auto-spend-without-budget`.  
Future finance architecture: `docs/Genesis_Finance_Security_Vision_Directive.md` (design only until milestones).

---

## Company model (how Genesis is organized)

| Role | Who / What |
|------|------------|
| **CEO** | You — strategy, limits, Success Log evidence |
| **Genesis** | Operational director — daily execution |
| **Garage** | R&D — experiment freely |
| **Production** | Live business — safe auto-apply only |
| **Media Engine** | Future marketing department (Research/FROZEN) |
| **Memory** | Corporate knowledge — Learning · Success · Decisions · Research |
| **Success Log** | Company achievement history |

More autonomy for Genesis → less CEO routine → more CEO strategy.

### CEO strategic reserve — permanent

Even at maximum autonomy, **substantial strategic changes always require CEO**. This rule does not expire.

| CEO only | Genesis may recommend |
|----------|----------------------|
| New business direction | Yes — CEO approves launch |
| Monetization model change | Yes — CEO approves |
| Major financial commitments | Yes — within budget rules only |
| Product positioning shift | Yes — CEO approves |
| Legally significant decisions | Yes — CEO only |

Genesis runs operations; **CEO owns the course and key risks**.

CEO decision: `dec-2026-07-05-ceo-strategic-reserve`.

### Long-term morning (vision)

CEO opens **Mission Control Dashboard**, not the code editor:

- what was done overnight
- validated results and confirmed hypotheses
- Genesis recommendations for growth

Realistic if built in stages — stability and verified outcomes first.

---

## Relation to current mission

| Now | Later |
|-----|-------|
| Mission 1 · first paying customer | Stage 1 Activity UI |
| Dogfooding · real bugs only | Stage 2 policy-bound autonomy |
| Research notes passive | Stage 3 Digital CEO |

**No new governance documents.** This file + `ceo_decisions.json` entry.

---

*CEO directive: autonomy increases; Production protection never relaxes without CEO approval. Strategic course and key risks remain CEO forever.*
