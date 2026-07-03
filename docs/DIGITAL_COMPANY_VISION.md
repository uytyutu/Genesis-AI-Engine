# Genesis as a Digital Company

**Status:** Vision approved — architecture direction, not implementation yet.  
**Factory remains blocked** until Owner Acceptance passes.

**Skills principle:** `docs/SKILLS_PLATFORM.md`

---

## What Genesis is

Genesis is **not** a website generator.

Genesis is an **operating system for a digital company** — departments, **digital employees**, and skills coordinated by Brain, with the owner as final authority.

**Genesis does not compete with ChatGPT, Claude, or Cursor.** It hires them as specialists. New models = new employees plugged in — core unchanged.

Websites are the **first skill**. Bots, apps, APIs, and automations follow the same plug-in model.

### Owner-facing words

| Technical (dev mode) | Owner sees |
|---------------------|------------|
| AI Agent | Digital Employee |
| Kernel / Brain | Department |
| Morning brief | Options based on **available data** — owner chooses what to explore |

> Assistant must not pretend to know the market perfectly.  
> *«Я подготовил три возможные идеи на основе доступных данных. Выберите, какую исследовать или реализовать дальше.»*

---

## Mature goal (replaces “earn money automatically”)

> **Genesis must create user value so efficiently that a sustainable business can be built on top of it.**

No software guarantees revenue. Revenue appears when people pay for useful products. Genesis optimizes **speed, quality, explanation, and owner control** — not magic profit.

---

## Shift in philosophy

| Before | Now |
|--------|-----|
| “AI that makes websites” | **Digital company OS** |
| Factory = the product | Factory = **one department** |
| Add features in one codebase | Add **Skills** without touching core |

---

## Departments (company org — future)

When the system scales to hundreds of agents, **departments** keep it understandable:

```
Genesis
│
CEO Office
│   ├── Strategy & daily brief
│   └── Owner approvals (Level 2 / 3)
│
├── Product Department
│     ├── Landing Factory      ← Skill v0.1
│     ├── Website Factory
│     ├── Telegram Factory
│     ├── SaaS Factory
│     └── Mobile Factory
│
├── Marketing Department
│     ├── SEO · Ads · Social · Analytics
│
├── Sales Department
│     ├── CRM · Leads · Clients
│
├── Support Department
│     └── Owner assistant (Command Center chat today)
│
├── Finance Department
│     └── Revenue, budgets (🔴 owner for payments)
│
└── Research Department
      ├── Market intelligence
      └── Ideas feed → owner picks → Factory runs
```

**Engineering mapping today:**

| Department (vision) | Built now | Layer |
|---------------------|-----------|-------|
| Kernel | ✅ | Task → plan → agents → result |
| Brain | ✅ | Queue, dispatch, audit |
| Command Center | ✅ | Live UI + Integration |
| Support | ✅ partial | Rule-based assistant (v0.1) |
| Launcher | ✅ | One-click start |
| Product / Factory | 📋 design | First Skill: Landing Page (sandbox) |
| QA / Analytics / CEO / Research | ◯ | After first Skill proven |

Layers stay **ignorant of each other**. Departments are **agents + Skills** on Brain — not monolith rewrites.

---

## Platform stack (how layers connect)

```
Launcher
    ↓
Command Center  ← owner sees Ideas, Roadmap, morning brief
    ↓
Brain           ← dispatches jobs to departments / Skills
    ↓
Kernel          ← plan → agents → result (frozen)
    ↓
Factory / Skills ← sandbox build
    ↓
QA              ← quality gates
    ↓
Analytics       ← what sells, what fails
    ↓
Marketplace     ← future (Level 2 publish)
```

---

## Ideas (future Command Center section)

Owner opens **Ideas**. Genesis shows demand-ranked opportunities with **why**:

> **Высокий спрос:**  
> • сайт для стоматологий  
> • бот для доставки еды  
> • CRM для салонов  
> • AI-консультант для магазинов  

Owner selects one → **Создать** → Factory Skill runs in sandbox → preview → Approve / Revise.

No auto-spend. No auto-publish.

---

## Company Roadmap (future Command Center UI)

Owner sees **company development**, not just engineering tickets:

```
Genesis — Развитие компании
████████░░  42%

Kernel          ✔
Brain           ✔
Command Center  ✔
Launcher        ✔
Factory         ⏳ 12%  (first Skill in progress)
Skills Library  🔒
Marketplace     🔒
Marketing AI    🔒
CEO AI          🔒
```

Today: engineering timeline on home page (~32%).  
Future: this **company roadmap** merges build progress + department readiness.

---

## The “Why?” principle

Every non-trivial action must be explainable:

```
Создаю Landing Page.

Причина:
За 7 дней — 24 запроса на сайты автосервисов.

Вероятность продажи: 81%
Ожидаемое время: 4 минуты.
```

Required on future **proposal cards** (Ideas, Factory jobs, template improvements).

---

## Three autonomy levels

| Level | Color | Rule | Examples |
|-------|-------|------|----------|
| **1** | 🟢 | Automatic — sandbox only | Build, test, fix, docs, night jobs, new template drafts |
| **2** | 🟡 | Prepared — **owner Approve** | Publish, domain, payments, ads, client messages |
| **3** | 🔴 | **Owner only** | Pay, contracts, legal, delete projects |

**Sandbox is permanent for Level 1.**

---

## Morning brief (north-star UX)

> **Доброе утро, Рамиш.**  
> Пока ты спал:  
> • создано 12 новых шаблонов (sandbox)  
> • улучшено 4 продукта  
> • найдено 3 направления с высоким спросом  
> • подготовлено 7 продуктов на проверку  
> • 1 ошибка в шаблоне — исправлена  
>
> Рекомендую начать со стоматологий — {reason}.  
> **[Ideas]** **[Одобрить]** **[Посмотреть]**

---

## Build priority (discipline)

1. ✅ Launcher — owner verifies one-click start
2. ✅ Command Center — daily-usable for non-programmers
3. ◯ Factory v0.1 — **one Skill**: Landing Page, sandbox only
4. ◯ Skills library — 10–20 **quality** templates (not shallow generators)
5. ◯ QA department — product quality scoring
6. ◯ Analytics — template usage and outcomes
7. ◯ Research / Ideas — market signals with “why”
8. ◯ More Skills (Telegram, CRM, …) — one proven Skill at a time

**Do not skip steps.** Do not add Skills before step 3 works end-to-end in browser.

---

## What we do not promise

- Automatic money
- Autonomous spending or publishing
- Replacing the owner
- One market only (websites) — platform expands via Skills

We promise: **explained, sandbox-safe, compounding capabilities** on a stable core.

---

*Constitution: `WHY.md` · Skills: `docs/SKILLS_PLATFORM.md` · Economy: `docs/ECONOMY.md` · Store: `docs/MARKETPLACE.md` · Build order: `docs/BUILD_ORDER.md`*
