# Genesis Platform Economy

**Status:** Vision document — business model and money flow. **No payment code** until Factory Skill v0.1 is proven in sandbox.

**Related:** `MARKETPLACE.md` · `docs/SKILLS_PLATFORM.md` · `WHY.md` (legal compliance)

---

## What Genesis becomes (long-term)

Genesis is not a single app that sells websites.

Genesis is a **platform** — infrastructure where:

- **Clients** order digital products
- **Genesis AI** analyzes, builds, validates (sandbox)
- **Developers** (optional) supply Skills and templates
- **Platform owner** earns from usage, commissions, and subscriptions
- **Payment Hub** routes money without locking to one provider

Value compounds in the **ecosystem**: users + Skills + tools + payments + analytics.

---

## End-to-end value chain (future)

```
Client request
      ↓
Genesis understands intent (Research / Ideas)
      ↓
Planner (Brain + Kernel)
      ↓
Skill executes (Factory department)
      ↓
QA validates quality
      ↓
Sandbox preview
      ↓
Client reviews → Approve / Revise
      ↓
Payment (Payment Hub)          ← 🟡 Level 2: client pays; 🔴 platform payouts: owner
      ↓
Publish (Level 2 — owner / client approval)
      ↓
Analytics & usage stats
      ↓
Improvement proposals (“why?”) → Evolution
```

**Today:** steps through Sandbox + Preview only. Payment and Publish are **not implemented**.

---

## Three commercial models

### Model 1 — Genesis does everything

Client: *"Make me a website."*

- AI + Factory Skill builds in sandbox → preview → client pays fixed price (e.g. €49)
- **100% to platform** (no third-party executor)
- Best for: simple Skills (landing pages, basic bots)

### Model 2 — Hybrid marketplace

Client: *"I need an online store."*

Genesis detects complexity beyond full automation:

| Option | Price | Who builds |
|--------|-------|------------|
| Auto version | €79 | Genesis Skills |
| Enhanced version | €290 | Verified developer + Genesis tools |

- Platform takes **commission** (e.g. 10–20%) on developer-led jobs
- Genesis still owns: brief, QA gate, escrow flow (future), publish approval

### Model 3 — Skills & template store

Third-party **developers** publish Skills/templates:

- CRM, restaurant site, dental landing, Telegram bot, etc.
- Listed in **Genesis Store** after Validator passes
- Each sale: **author revenue + platform commission**
- Platform does not need to build every template itself

---

## Revenue streams (when platform matures)

| Stream | Description |
|--------|-------------|
| Subscriptions | Monthly access to Genesis / pro features |
| Product sales | Fixed-price auto-built products (Model 1) |
| Marketplace commission | % on developer-delivered projects (Model 2) |
| Template / Skill store | % on each download or sale (Model 3) |
| Enterprise licenses | On-prem or dedicated Command Center |
| Paid AI features | Premium models, faster builds, extra quota |

No single stream is required at launch. **Model 1 + one Skill** is enough to validate.

---

## Payment Hub (architecture principle — build early as interface, implement late)

> **Do not tie Genesis to one payment provider.**

**Payment Hub** is a module (Finance Department) that:

- Defines a **single internal API**: `create_checkout`, `confirm_payment`, `refund`, `payout_to_seller`
- Adapts **providers** as plugins: cards, wallets, bank transfer, regional gateways
- Logs every transaction for Analytics and owner audit
- Enforces **autonomy levels**:
  - **🟡** Client checkout may be semi-automated after legal setup
  - **🔴** Platform payouts, commissions, and provider keys — **owner only** until explicitly delegated

```
Command Center / Client UI
        ↓
   Payment Hub (abstraction)
        ↓
   ┌────┴────┬──────────┐
 Stripe   PayPal   LocalBank …
```

**v0.x:** Payment Hub exists as **documented interface + stubs only**. No live charges until legal review and owner sign-off (`WHY.md`).

---

## Who earns what (summary)

| Role | Earns from |
|------|------------|
| Platform owner (you) | Subscriptions, auto-build sales, commissions, store fees |
| Client | Receives digital product / service |
| Skill author | Store sales minus platform commission |
| Developer (marketplace) | Project fee minus platform commission |

Genesis AI does not “earn money.” The **platform and humans** in the ecosystem do.

---

## Mature goal (aligned with `WHY.md`)

> **Genesis creates user value so efficiently that a sustainable business can be built on top of it.**

Revenue follows **useful products people pay for** — not autonomous AI spending or promising guaranteed income.

---

## What we do not promise

- Guaranteed profit or passive income
- Fully autonomous billing without owner oversight (initially)
- Single-provider lock-in
- Skipping sandbox before paid delivery

---

## Build order (economy features)

1. ✅ Document economy (this file)
2. ◯ Factory Skill v0.1 — sandbox + preview (no payment)
3. ◯ Owner Acceptance — real user can complete one cycle
4. ◯ Payment Hub **interface** + sandbox mocks in tests
5. ◯ Model 1 — one priced product, one provider, owner-approved go-live
6. ◯ Model 3 — store listing for first third-party template
7. ◯ Model 2 — developer marketplace + commission

**Do not implement step 4 before step 2–3 work in the browser.**

---

*Marketplace mechanics: `MARKETPLACE.md` · Skills: `docs/SKILLS_PLATFORM.md` · Company org: `docs/DIGITAL_COMPANY_VISION.md`*
