# Genesis Marketplace & Store

**Status:** Vision document — no marketplace code until one platform-owned Skill works end-to-end in sandbox.

**Related:** `docs/ECONOMY.md` · `docs/SKILLS_PLATFORM.md` · `WHY.md`

---

## Purpose

The **marketplace** is where Genesis becomes a **platform**, not only an internal tool:

- External **developers** publish Skills and templates
- **Clients** discover and buy products
- **Genesis** validates quality, takes commission, provides infrastructure
- **Authors** earn from sales

The platform owner earns from **commission + infrastructure**, similar to large app stores and freelance marketplaces — without Genesis having to build every product alone.

---

## Store flow (future)

```
Developer
    ↓
Creates Skill or template pack
    ↓
Validator (QA department) — security, sandbox, tests, policy
    ↓
Genesis Store listing (metadata, preview, price)
    ↓
Users browse / search / Ideas recommendations
    ↓
Purchase via Payment Hub
    ↓
Author receives payout (minus commission)
    ↓
Genesis receives platform fee
    ↓
Analytics → ranking, “why” recommendations
```

---

## Who can create Skills?

| Creator | When | Gate |
|---------|------|------|
| **Genesis core team** | First — proves the pipeline | Owner + tests + Owner Acceptance |
| **Verified developers** | After store v0.1 | Validator + manual review (v0.1) |
| **Community** | Later | Reputation score + automated checks |

**Rule:** Nothing enters the Store without passing **Validator** in sandbox. No arbitrary code execution on owner machines without review.

---

## Listing requirements (every Skill / template)

1. **Sandbox-only build** demonstrated
2. Automated **test suite** passes
3. **Explainability** — what it builds, for whom, limitations
4. **License** — compatible with platform rules (`WHY.md`)
5. **No** spam, ToS bypass, or illegal use cases
6. **Versioning** — updates re-validated before publish

---

## Commission model (default proposal — owner sets final %)

| Sale type | Platform fee (example) |
|-----------|-------------------------|
| Auto-built product (Genesis Skill only) | 100% to platform |
| Template / Skill download | 15–30% |
| Developer-led project (Model 2) | 10–20% |

Exact percentages are **owner configuration** (Finance Department), not hard-coded in Kernel.

---

## Client experience (ties to Ideas)

Client or owner opens **Ideas** or **Store**:

> **High demand:** dental website · food delivery bot · salon CRM · shop AI consultant

Select → **Create** → Skill runs → preview → pay (🟡) → publish (🟡) → stats

For store templates: **Buy** → download / deploy to sandbox → customize → publish with approval.

---

## Departments in the marketplace

Marketplace is not one blob — **departments use Skills**:

```
CEO Office          — strategy, pricing policy, approve major listings
Product Department  — Factory Skills (Website, Telegram, API builders…)
Marketing Department— SEO, Copywriting, Analytics Skills
Sales Department    — CRM, Leads, Clients Skills
Support Department  — AI Chat, Ticket Skills
Finance Department  — Payment Hub, payouts, commissions (🔴 owner)
Research Department — demand signals → Ideas feed
```

Adding a marketplace feature = adding **Skills + store metadata**, not rewriting Brain.

---

## Genesis Store vs internal Skills

| | Internal Skill | Store Skill |
|--|----------------|-------------|
| Author | Platform | Platform or third party |
| Visibility | Owner only | Clients / public catalog |
| Payment | N/A until go-live | Payment Hub |
| Validator | CI + owner | CI + Validator agent + review |

Platform-owned Skills (e.g. `landing-page-v1`) ship first **internally**; store opens when Validator and Payment Hub stubs are proven.

---

## Trust and safety (non-negotiable)

- **Sandbox first** — every Skill runs isolated until publish approval
- **No autonomous payouts** — 🔴 Level 3 until owner delegates
- **Audit log** — every listing, sale, payout traceable (Brain `audit.jsonl` pattern extends to commerce events)
- **Refund policy** — owner-defined, enforced via Payment Hub

---

## Build order (marketplace)

1. ◯ One internal Skill (Landing) — sandbox cycle complete
2. ◯ Owner Acceptance on Command Center
3. ◯ Validator spec for Skills (reuse Factory QA design)
4. ◯ Store **UI mock** in Command Center (no real money)
5. ◯ Payment Hub interface + test doubles
6. ◯ First **platform-owned** paid product (Model 1)
7. ◯ First **third-party** listing (Model 3, manual approval)
8. ◯ Developer marketplace jobs (Model 2)

**Do not open the Store before step 1–2.**

---

## What success looks like (12–24 months vision)

- Clients order simple products without talking to a developer
- Developers earn from templates without you building everything
- You earn from commission and subscriptions without promising “AI prints money”
- Genesis recommends **what to build next** with data and “why” — owner still approves

---

*Economy overview: `docs/ECONOMY.md` · Architecture: `docs/SKILLS_PLATFORM.md` · `docs/DIGITAL_COMPANY_VISION.md`*
