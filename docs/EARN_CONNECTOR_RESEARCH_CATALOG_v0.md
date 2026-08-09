# Earn Connector Research Catalog v0

**Status:** Research only — **no adapters, no scaffold, no code.**  
**Locked with:** `docs/MISSION_BOARD.md` (Mission 3) · `docs/EARN_CONNECTOR_SPEC_v0.md`  
**Date:** 2026-08-01  
**Goal:** find the first **legal** Earn Connector with best ROI for Virtus Core capabilities — not prove Toloka.

---

## North star of this catalog

Farm is a **universal orchestrator**, not a “Toloka farm.”

```
Acquisition → bring demand
Execution   → tools do the work (Toloka, LLM, OCR, …)
Earn        → money in (Stripe, Own API, RapidAPI, …)
Spend       → cost of tools (ledger view of Execution)
        ↓
REAL PROFIT = Revenue − Execution Cost
```

**Earn Connector** = channel that **collects money**.  
A tool does **not** need to pay Virtus to be valuable — it must improve REAL PROFIT of paid jobs.

This catalog ranks **Earn** candidates only. Toloka/Scale requester stay **Execution + Spend** (see Mission Board).

**Rank 1–2 unchanged:** Own API / Services + Stripe · RapidAPI Provider.

**Payout:** not in this catalog — see `swarm/payout_manager.py` and CEO tab `/payout`. Earn sources declare official withdraw methods there.

If a better Earn platform appears in six months, Virtus adds a connector — architecture stays.

**Out of scope here:** treating Toloka as an Earn source; Circumventing ToS. Path A Stripe is already an Earn channel (Mission 1).

**Income estimates** below are **order-of-magnitude / directional**, not forecasts. Prefer Legal Review + small live probe over spreadsheet optimism.

---

## Scoring (for shortlist)

| Factor | Weight | Question |
|--------|--------|----------|
| ToS automation | Critical | Officially allowed for our execution mode? |
| Payout clarity | High | Documented path to bank/PayPal/Stripe? |
| API / official integration | High | Can Earn Connector methods map without bots? |
| Fit to Virtus strengths | High | Sites, docs, outreach, analysis, automation, APIs? |
| Entry barrier | Medium | Time/money/KYC before first €? |
| Risk | Critical | Ban, clawback, legal, reputation? |
| ROI potential | Medium | Plausible € after costs? |

**Hard reject:** automation forbidden + only human-UI path with no HITL gate in our product.

---

## Category A — B2B API Work

Services where our AI / automation performs **paid work for developers or agents** via official product surfaces.

### A1. RapidAPI Hub (API Provider / seller)

| Field | Finding |
|-------|---------|
| Official model | Publish API → buyers subscribe on Rapid Hub → Rapid takes marketplace fee → provider payout |
| Automation allowed? | **Yes** for serving the API you own (that *is* the product). Not a microtask bot. |
| Payout | PayPal only (USD). ~25% marketplace fee (from Nov 2025). Monthly consolidation; payout ~2 months lag (e.g. July → early September) |
| API | Provider dashboard + Hub listing; you host the billed API |
| Entry | Build a useful API; listing; PayPal KYC |
| Risk | **Medium** — fee + lag; marketplace competition; you own support/SLA |
| Income potential | **Medium–High if product sticks** — usage-based; depends on demand, not task queue |
| Virtus fit | High — wrap Document / Site / Analysis / Places-derived tools as metered APIs |

**ROI note:** First Earn that matches “platform pays Virtus for automated work” *and* ToS-clean. Cold-start discovery is the hard part.

### A2. Own API + Stripe Machine Payments Protocol (MPP) / Agentic Commerce

| Field | Finding |
|-------|---------|
| Official model | Agents/clients pay your HTTP/MCP endpoints via Stripe MPP / Agentic Commerce Suite; funds settle to your Stripe balance |
| Automation allowed? | **Yes** — you are the merchant; automation is the product |
| Payout | Existing Stripe payout schedule (bank) — same stack as Path A |
| API | Stripe PaymentIntents / Checkout / MPP docs; catalog syndication for agents (rollout / waitlist for suite pieces) |
| Entry | Stripe account (already Path A); implement paywall on endpoints; possible suite waitlist |
| Risk | **Low–Medium** — legal clarity high; product-market risk; protocol adoption still early |
| Income potential | **High if agents adopt** — speculative volume; excellent unit economics (no 25% Hub cut) |
| Virtus fit | Highest strategic fit — Digital Company sells work to humans *and* agents |

**ROI note:** Best long-term Earn shape. Not a “browse queue → submit” connector; still maps to Earn ledger as `ConfirmedPayout` from Stripe.

### A3. AWS Marketplace / similar SaaS listings

| Field | Finding |
|-------|---------|
| Official model | List SaaS/API; AWS bills enterprise buyers; seller share |
| Automation allowed? | Yes for product delivery |
| Payout | AWS seller disbursements (contractual) |
| API | Marketplace APIs + metering |
| Entry | **High** — seller registration, listing review, compliance |
| Risk | **Medium** — slow sales cycle; ops burden |
| Income potential | **High ceiling, slow start** |
| Virtus fit | Medium — enterprise path after Mission 1–2 |

**Shortlist:** Research backlog, not first connector.

---

## Category B — Data / Labeling

Platforms for annotation / training data. Most public APIs are **requester = Spend**. Contributor/earn side is usually UI + human judgment.

### B1. Toloka (Performer / Earn side)

| Field | Finding |
|-------|---------|
| Official model | Pipeline/projects; performers complete tasks; requesters pay Toloka |
| Automation allowed? | **Likely restricted / forbidden** for unsupervised bots on human-judgment tasks — Legal Review mandatory; do not assume |
| Payout | Performer wallet → withdraw per Toloka rules (region-dependent) |
| API | Strong **requester** API (already Spend in codebase). Performer Earn API for “fetch→submit→paid” **not confirmed as Mission-ready** |
| Entry | Account, quals, region |
| Risk | **High** if botting; **Medium** if human/HITL only |
| Income potential | **Low–Medium** microtask rates; not Virtus’s strength |
| Virtus fit | Poor as *first* Earn — we already have Spend wiring; Earn unfinished for a reason |

**Verdict:** Toloka is **Execution + Spend**, not first Earn. Use only when attributed cost raises REAL PROFIT of a paid job. Do **not** optimize for “Toloka income.”

### B2. Clickworker (Contributor)

| Field | Finding |
|-------|---------|
| Official model | Crowdsourcing jobs → weekly bill run → PayPal / Payoneer / SEPA |
| Automation allowed? | Expect **forbidden** for bots; human work |
| Payout | Min ~€10–20; bill run Wed–Fri; delayed settlement |
| API | Public API is **customer/requester** (Spend), not contributor earn |
| Entry | Low–medium; tax/ID |
| Risk | **High** for automation; **Medium** for manual |
| Income potential | **Low** microtask |
| Virtus fit | Weak — no official earn API for connector |

### B3. Appen / Remotasks / Amazon MTurk (contributor)

| Field | Finding |
|-------|---------|
| Official model | Human microtasks / annotation |
| Automation allowed? | Generally **no** |
| Payout | Platform wallets / gift cards / bank (varies) |
| API | Mostly requester; worker automation unofficial |
| Entry | Varies; often quals |
| Risk | **High** for bots |
| Income potential | **Low** |
| Virtus fit | Reject for first Earn Connector |

### B4. Labelbox / Scale (as Earn)

| Field | Finding |
|-------|---------|
| Official model | Enterprise labeling **platforms/services** — you pay them |
| Automation allowed? | N/A for Earn — we would be customer |
| Payout | None to us |
| API | Requester / workspace APIs = **Spend** |
| Verdict | Spend only |

---

## Category C — Automation Marketplaces

Paid templates, connectors, or partner revenue for automation skills.

### C1. n8n Creator Hub + third-party workflow markets (FlowMarket, Gumroad, etc.)

| Field | Finding |
|-------|---------|
| Official model | Sell workflow templates / setup services; marketplace or direct digital goods |
| Automation allowed? | **Yes** — product is automation artifacts; buyers run them |
| Payout | Stripe Connect / Gumroad / Lemon Squeezy / platform schedule |
| API | Listing + commerce APIs; not a task queue |
| Entry | Build 1–3 strong templates; Creator Hub may require free publishes first |
| Risk | **Low–Medium** — IP, support, platform fee; market noise |
| Income potential | **Medium** — passive SKUs €10–100+; services €100–5k |
| Virtus fit | Medium — package Farm/outreach/site pipelines as templates; less “agent fetches jobs” |

### C2. Zapier Solution Partner / Make Technology Partner

| Field | Finding |
|-------|---------|
| Official model | Referral commissions / co-sell / ISV connector distribution — **not** paid task queue |
| Automation allowed? | Building integrations = yes; spamming platform = no |
| Payout | PartnerStack / partner portal (often monthly) |
| API | Developer platforms for apps |
| Entry | Certification / verified app |
| Risk | **Low** compliance; **High** effort before € |
| Income potential | **Medium** recurring on referrals; slow |
| Virtus fit | Partner channel, weak first Earn Connector |

---

## Category D — AI Agent Marketplaces

Platforms that claim to host/sell agents.

### D1. Agent.ai

| Field | Finding |
|-------|---------|
| Official model | Discover / build / run agents; marketplace credits |
| Automation allowed? | Building agents yes |
| Payout | Credits have **no monetary value**; cannot cash out (per platform credits docs) |
| API | REST for run/search (community/CLI exist) |
| Entry | Free signup |
| Risk | **Low** legal; **High** for Earn goal (no cash) |
| Income potential | **None** as Earn today |
| Virtus fit | Distribution/marketing only — **not** Earn Connector |

### D2. Emerging skill / agent skill exchanges (e.g. Stripe Connect-based skill markets)

| Field | Finding |
|-------|---------|
| Official model | List skill/MCP tool → buyer pays → Connect payout (varies by site) |
| Automation allowed? | If platform is built for agent skills — usually yes for delivery |
| Payout | Stripe Connect when implemented |
| API | Site-specific; often immature |
| Entry | Early ecosystems; verify each ToS |
| Risk | **High** platform risk (shutdown, low liquidity) |
| Income potential | **Unknown / speculative** |
| Virtus fit | Watchlist — Legal Review per site before any adapter |

### D3. Sell agents via Stripe Agentic Commerce (own surface)

Same economic spine as **A2** — Virtus is merchant of record. Prefer this over unproven third-party agent malls.

---

## Category E — Human-in-the-loop

Hybrid: human judgment + automation assist. Automation of **submission without human** usually banned.

### E1. Upwork (freelancer)

| Field | Finding |
|-------|---------|
| Official model | Bid → contract → deliver → Upwork payout |
| Automation allowed? | AI **draft** OK; **auto-submit proposals / bots** forbidden; public API has **no** proposal submit mutation |
| Payout | Upwork → bank/Payoneer (fees) |
| API | GraphQL read-heavy; write for proposals not officially exposed |
| Entry | Profile, Connects, niche proof |
| Risk | **High** if auto-bid; **Medium** with HITL submit |
| Income potential | **Medium–High** for website/doc services (Virtus strength) — but not “hands-off Farm” |
| Virtus fit | Possible **HITL Earn** later: discover jobs → draft → human Approve → manual submit. Not first autonomous connector |

### E2. Outlier (Scale) / DataAnnotation / Surge (contributor)

| Field | Finding |
|-------|---------|
| Official model | Expert RLHF / ranking / writing; weekly contractor pay |
| Automation allowed? | **No** — human expertise is the product; bots = ban |
| Payout | Contractor channels (platform-specific) |
| API | No public “earn queue submit” for third-party farms |
| Entry | Assessments; selective |
| Risk | **High** for automation; labor classification lawsuits exist in sector |
| Income potential | **Medium–High hourly** for skilled humans — **not** Virtus autonomous ROI |
| Virtus fit | Reject as Farm Earn target |

### E3. Fiverr / similar gigs

| Field | Finding |
|-------|---------|
| Official model | Gig listings → orders → delivery |
| Automation allowed? | Delivery automation OK if buyer ToS/gig promise allows; platform botting restricted |
| Payout | Platform → PayPal/bank |
| API | Seller APIs limited / partner |
| Entry | Gig setup |
| Risk | **Medium** |
| Income potential | **Medium** with productized services |
| Virtus fit | Productized “Site in 48h” gigs — HITL sales, automated delivery. Secondary to Path A |

---

## Preliminary ranking (first Legal Review targets)

| Rank | Candidate | Category | Why |
|------|-----------|----------|-----|
| **1** | **A2 — Own API / services + Stripe (MPP / standard Checkout)** | B2B API | Legal clarity; payout already understood; maps to REAL; max Virtus leverage |
| **2** | **A1 — RapidAPI Provider** | B2B API | Official marketplace earn; automation = product; PayPal lag/fee tradeoff |
| **3** | **C1 — Automation templates (n8n / Gumroad / FlowMarket)** | Automation | Legal sell of artifacts; lower integration depth; good probe of packaging |
| **4** | **E1 — Upwork HITL assist** | HITL | Strong € potential; **not** autonomous; needs CEO-in-loop |
| **Watch** | Emerging agent skill markets | AI Agent | Re-check quarterly for real cash + API |
| **Defer / Reject as first Earn** | Toloka/Clickworker/Appen/MTurk/Outlier performer bots | Data / HITL | ToS + weak API + wrong capability fit |
| **Never as Earn** | Toloka/Scale **requester** | Spend | Already Spend |

---

## Recommended next steps (still no code)

1. **Legal Review pack for Rank 1–2** (A2 + A1): ToS excerpts · fee schedule · payout docs · what “automation allowed” means for our delivery mode.
2. **Capability map:** list 3 Virtus offerings that could be metered APIs or paid endpoints (e.g. site package generate, document pack, lead research report).
3. **Choose exactly one** after Legal Review PASS → then scaffold against real contract (`EARN_CONNECTOR_SPEC_v0.md`).
4. Keep Mission 1 Path A as primary €; Earn catalog does not block it.

---

## Explicit non-goals (this document)

- No Earn Layer code / adapters / Toloka Performer.
- No enabling `FARM_LIVE_MODE` / `TOLOKA_AUTO_SUBMIT`.
- No proof that Toloka is the answer.
- No mixing Farm REAL with Path A Stripe in one ledger without connector class tags.

---

## Revision

| Ver | Date | Change |
|-----|------|--------|
| v0 | 2026-08-01 | First multi-category catalog; shortlist A2 → A1 → C1 |
| v0.1 | 2026-08-01 | Farm roles: Earn vs Execution; Toloka = tool ROI, not Earn |
