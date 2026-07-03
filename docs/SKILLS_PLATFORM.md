# Genesis Skills Platform

**Status:** Architecture principle — frozen. No Skills code until Factory v0.1 proves one skill.

---

## Core principle (non-negotiable)

> **Genesis is not an app for making websites. Genesis is a platform where new capabilities are added as Skills. Any new product type — website, bot, app, API, automation — is implemented as a separate Skill without changing the system core.**

Websites are **the first skill**, not the definition of the product.

---

## What is a Skill?

A **Skill** is a pluggable capability that:

1. Registers with Brain as one or more agents and/or services
2. Uses Kernel for multi-step jobs (plan → execute → result)
3. Runs in **Sandbox** by default (Level 1 autonomy)
4. Exposes **explainable proposals** (“why?”) to Command Center
5. Does **not** modify Kernel, Brain queue protocol, or Integration Layer contracts

Adding a Skill = new folder + registration + tests — **not** a core rewrite.

---

## Factory product families (future Skills)

Factory is the **Product Department** — it hosts many builders:

```
Factory (Product Department)
├── Websites
├── Telegram Bots
├── Desktop Apps
├── Mobile Apps
├── AI Agents
├── SaaS
├── Automations
├── Dashboards
├── APIs
├── Chrome Extensions
├── WordPress Plugins
├── Shopify Apps
└── Discord Bots
```

**v0.1 ships one Skill only:** `landing-page-v1` (Websites family).

Each family is a **Skill pack** — added incrementally after the previous one is stable in sandbox.

---

## Skills marketplace (growth model)

Genesis grows by **adding Skills**, not rewriting the core:

| When | Skill example |
|------|----------------|
| Today (planned) | Landing Page |
| +1 month | Telegram Bot Builder |
| +2 months | CRM Builder |
| +1 year | AI Employee Builder |

The owner sees in Command Center which Skills are **installed**, **in progress**, or **locked**.

---

## Engineering rules for every new Skill

1. **Kernel stays frozen** — Skill implements `Agent.run()` or calls Integration Layer
2. **Brain dispatches** — Skill jobs are normal queued tasks with audit events
3. **Command Center displays** — proposals, previews, Approve / Revise — never Builder internals
4. **Sandbox first** — no publish until Level 2 approval
5. **Tests required** — Skill cannot ship without its own test suite

---

## Skill vs Department

| Concept | Meaning |
|---------|---------|
| **Department** | Organizational unit (Marketing, Sales, Research…) — may own many Skills |
| **Skill** | Concrete capability (Landing Builder, SEO Analyzer…) — plugs into Brain |

Example: `Landing Factory` is a **Skill** inside the **Product Department**.

**Departments use Skills** — Marketing uses SEO / Copywriting / Analytics Skills; Factory uses Website / Telegram / API builders; Support uses AI Chat / Ticket Skills. See `docs/DIGITAL_COMPANY_VISION.md` and `docs/MARKETPLACE.md`.

---

## Commerce (future — documented only)

Platform economy and store mechanics are **not coded yet**:

- `docs/ECONOMY.md` — client flow, three models, Payment Hub, revenue streams
- `docs/MARKETPLACE.md` — developer store, commission, Validator gate

Payment Hub must stay **provider-agnostic**. Live charges require owner sign-off (`WHY.md`).

- Hard-coding “website only” into Kernel or Brain
- One giant Factory class that knows all product types
- Skipping sandbox for “just this once”
- Adding a Skill before the previous one passes owner acceptance in browser

---

*Vision: `docs/DIGITAL_COMPANY_VISION.md` · Factory design: `docs/FACTORY_FRAMEWORK_ARCHITECTURE_v0.1.md`*
