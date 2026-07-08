# Mission 1 Release Readiness — End-to-End Validation

**Type:** Product / QA · **NOT** governance  
**Status:** Active — CEO dogfooding as first customer  
**Date:** 2026-07-05  
**Rule:** Do not assume anything works until tested.

---

## Purpose

Before **Gewerbe**, **public launch**, or **paying customers**, Genesis must pass manual end-to-end validation.

**CEO = first customer.** Cursor guides; CEO executes and records **PASS / FAIL / BLOCKED / SKIP**.

Nothing is “ready” because it compiles. **Reality over Features.**

Test **every critically important process** — not everything that exists. Focus on what affects **customer understanding, orders, money, and trust**.

**Anti-pattern:** endless testing («ещё один тест… ещё месяц»). Use the **four stages** below. Advance when stage criteria are met — not when perfection is imagined.

---

## Four stages (stop rules)

| Stage | Name | Exit criteria | Gewerbe / public? |
|-------|------|---------------|-------------------|
| **1** | **Technical Ready** | Compact Release Checklist below — all critical ☐ → PASS | No |
| **2** | **Dogfooding** | CEO completes 2+ full journeys as non-developer (site → order → status; test pay if configured) | No |
| **3** | **Beta Ready** | 2–3 outsiders try without explanation; feedback collected; critical FAILs fixed | No |
| **4** | **Release Ready** | Stage 1–3 done + Gewerbe (if needed) + Stripe + domain + email | **Yes** |

**Stage 1** maps to detailed sections A–K (critical steps only required for gate).  
**Stage 2** — order as first customer: site, shop concept, app concept, etc.; pay path; post-order status.  
**Stage 3** — friend/relative; ask: unclear? want to close? hard? liked?  
**Stage 4** — only after above.

---

## Compact Release Checklist (Stage 1 gate)

Genesis must **not** recommend public launch until every **critical** row is **PASS**.

| Area | PASS | FAIL | Notes |
|------|------|------|-------|
| Website `/site` | ☐ | ☐ | |
| AI Concierge | ☐ | ☐ | |
| Order flow `/order` | ☐ | ☐ | |
| Mission Control | ☐ | ☐ | |
| Performance (acceptable) | ☐ | ☐ | |
| Security (smoke) | ☐ | ☐ | `python scripts/security_audit.py` — BLOCKER 7 |
| Mobile | ☐ | ☐ | |
| Desktop | ☐ | ☐ | |
| Payments (test or clear N/A) | ☐ | ☐ | |
| Backup (GitHub + secrets) | ☐ | ☐ | |
| Recovery (reinstall path) | ☐ | ☐ | |
| Documentation | ☐ | ☐ | |
| **Known critical bugs** | ☐ None | ☐ | |

**Recommendation — Release public:** ☐ **YES** · ☐ **NO**

*Copy to `Mission1_Release_Readiness_Results.md` when complete.*

### Stage 1 — Technical Ready (what the compact checklist covers)

- ✅ Site · AI Concierge · order · Mission Control · auth (if any) · AI responds · stability · no critical errors  
- Detailed steps: Sections A–K below (⚠️ = counts toward compact checklist)

### Stage 2 — Dogfooding (CEO as first customer)

- Order a site (and optionally describe shop / app / game / AI — even if not fully delivered yet)  
- Full path: conversation → `/order` → confirmation → status → test payment if Stripe test ready  
- **Not as developer** — as someone who knows nothing about Genesis

### Stage 3 — Beta Ready

- 2–3 people, no explanation  
- Collect: unclear · wanted to close · hard · liked  
- Fix critical issues only — then proceed

### Stage 4 — Release Ready

- Gewerbe (if not yet) · Stripe live · domain · email · public URL

---

## How to use

1. Start Genesis (Launcher → Mission Control or local dev).
2. Work through steps **in order** within each section (sections can be parallel by device).
3. Mark each step in `Mission1_Release_Readiness_Results.md`.
4. **FAIL** → fix before public release (or document BLOCKED with reason).
5. **Critical** steps (marked ⚠️) must be PASS before recommending Gewerbe or live payments.

**Gate (all must be true before public + Gewerbe):**

- [ ] All ⚠️ critical steps PASS  
- [ ] No open FAIL on Website + Ordering + Concierge  
- [ ] CEO completed full path: `/site` → consultation → quote → YES → `/order` → (test payment if configured)  
- [ ] Mission Control reflects real state (no fake “done”)  

**Guided walkthrough:** `Mission1_Dogfooding_Guide.md` (step-by-step, Cursor as test manager).  

Only then: register business · open public access · accept paying customers.

---

## Section A — Website (`/site`)

| # | Step | Check | Crit |
|---|------|-------|------|
| A1 | Open `http://localhost:3000/site` (or production URL) | Page loads &lt; 5s on CEO machine | ⚠️ |
| A2 | First paint | AI Concierge visible above the fold — not buried under text | ⚠️ |
| A3 | Headline | «Расскажите, что вы хотите создать…» visible | ⚠️ |
| A4 | Quick suggestions | All 7 chips visible (🏪🍽️🚗📱🎮🤖📦) and clickable | |
| A5 | Input | Placeholder readable; can type in Russian | |
| A6 | Submit empty | Button disabled or polite prompt | |
| A7 | Mobile width (375px) | Concierge usable; no horizontal scroll | ⚠️ |
| A8 | Tablet width (768px) | Layout OK | |
| A9 | Desktop (1280px+) | Layout OK | |
| A10 | Expand «Кратко: что такое Genesis» | Answers 6 questions without leaving page | |
| A11 | Expand «Пакеты и цены» | Shows Basic / Business / Premium with € | ⚠️ |
| A12 | Expand «Частые вопросы» | FAQ opens; readable | |
| A13 | Footer links | Impressum, Datenschutz, AGB, Kontakt work | |
| A14 | «Рассчитать стоимость» | Focuses chat — no raw € / «6 вопросов» above fold | ⚠️ |
| A15 | Performance | No obvious jank on first load (subjective) | |
| A16 | Accessibility | Tab reaches input + chips; focus visible | |

---

## Section B — Customer experience (first-time visitor)

| # | Step | Check | Crit |
|---|------|-------|------|
| B1 | 2-minute test | Non-technical person (or CEO fresh eyes) understands what Genesis is | ⚠️ |
| B2 | Value prop | Can answer: what Genesis builds | ⚠️ |
| B3 | Differentiation | Can answer: why not a normal agency | |
| B4 | Pricing clarity | Knows price is shown before pay | ⚠️ |
| B5 | After pay | Knows what happens after payment | |
| B6 | Path to order | Can reach `/order` without asking CEO | ⚠️ |
| B7 | Confusion points | Note any “want to close tab” moments (write in Results) | |
| B8 | Language | Russian copy feels natural, not robotic | |

---

## Section C — AI Concierge

| # | Step | Check | Crit |
|---|------|-------|------|
| C0 | `GET /api/public/genesis-ai/status` | `llm_configured: true` before public release | ⚠️ BLOCKING |
| C1 | Backend up | `POST /api/public/genesis-ai` returns answer (not connection error) | ⚠️ |
| C2 | Normal: «Мне нужен сайт для кафе» | Consultation starts; **no** immediate `/order`; no Studio push | ⚠️ |
| C3 | Normal: «Мне нужен сайт для автосервиса» | Consultation + prefilled business; questions follow | ⚠️ |
| C4 | «Что такое Genesis?» | Clear studio + AI explanation | |
| C5 | «Сколько стоит?» | Lists packages or from € + CTA | ⚠️ |
| C6 | «Что после оплаты?» | Process explained | |
| C7 | Difficult: «Сделайте мне маркетплейс как Amazon» | Honest limits; no false promise | ⚠️ |
| C8 | Unsupported: «Взломайте алгоритм TikTok» | Refuses; stays professional | |
| C9 | Incorrect: empty / gibberish | Graceful response | |
| C10 | Long message (300+ chars) | Handles or truncates without crash | |
| C11 | 5+ messages in a row | Full consultation → quote → order CTA only after «да» | ⚠️ |
| C12 | Honesty | No “guaranteed success” / no fake market data | ⚠️ |
| C13 | CTA | «Оформить заказ» appears **only after** client agrees → `/order` | ⚠️ |
| C14 | «Хочу Genesis Studio» | Studio pitch; no forced service `/order` | ⚠️ |

---

## Section D — Ordering (`/order`)

| # | Step | Check | Crit |
|---|------|-------|------|
| D1 | Open `/order` | Form loads; step indicator 1·2·3 visible | ⚠️ |
| D2 | Package Basic | Select / auto-suggest; price shown | ⚠️ |
| D3 | Package Business | Price updates | |
| D4 | Package Premium | Price updates | |
| D5 | Custom needs | Logo + domain checkboxes change suggestion | |
| D6 | Validation | Submit empty → errors, no silent fail | ⚠️ |
| D7 | Valid test order | Test business name + email; order created | ⚠️ |
| D8 | Confirmation screen | Order ID, package, price visible | ⚠️ |
| D9 | Payment button | If Stripe test: checkout opens OR clear “not configured” | |
| D10 | Status page | `/order/status/{id}` loads after create | |
| D11 | Mobile `/order` | Form usable on phone width | ⚠️ |
| D12 | Legal | AGB + Datenschutz links present | |

---

## Section E — Mission Control (`/`)

| # | Step | Check | Crit |
|---|------|-------|------|
| E1 | Launcher → Open Mission Control | Opens browser or surface | ⚠️ |
| E2 | Dashboard loads | No infinite skeleton | ⚠️ |
| E3 | System status | Running / stopped accurate | |
| E4 | Sales / orders panel | Shows orders if any exist | |
| E5 | Navigation | Key pages reachable from shell | |
| E6 | Notifications | No spam; real events only | |
| E7 | Demo mode | Clearly labeled if demo | |
| E8 | Refresh | 15s poll does not break UI | |
| E9 | Backend down | Clear message, not blank screen | |
| E10 | CEO metrics | Revenue reflects truth (0 if none) | ⚠️ |

---

## Section F — User application (Launcher + Desktop)

| # | Step | Check | Crit |
|---|------|-------|------|
| F1 | Install / run `Genesis.exe` | Starts without manual terminal | ⚠️ |
| F2 | «Запустить Genesis» / boot | Backend + frontend pipeline | ⚠️ |
| F3 | Boot failure | Dialog + report if fail (not silent) | |
| F4 | Mission Control opens after boot | Per config (browser OK) | ⚠️ |
| F5 | Second launch while running | Fast path or clear message | |
| F6 | Stop / restart | Clean shutdown; ports released | |
| F7 | Desktop app (if used) | Connects to API | |
| F8 | Settings | Persist across restart | |
| F9 | Assistant `/ai` | Owner assistant responds | |
| F10 | Error in logs | No critical unhandled exceptions during boot | |
| F11 | Recovery | Kill processes → relaunch works | ⚠️ |
| F12 | Dogfooding | Events written to `dogfooding_events.jsonl` | |

---

## Section G — Cross-platform

Test on devices CEO has. Mark SKIP if device unavailable.

| # | Step | Platform | Check |
|---|------|----------|-------|
| G1 | `/site` + Concierge | Windows (CEO PC) | ⚠️ |
| G2 | `/order` | Windows | ⚠️ |
| G3 | Mission Control | Windows browser | ⚠️ |
| G4 | `/site` | Android Chrome | |
| G5 | `/site` | iPhone Safari | |
| G6 | `/site` | Tablet | |
| G7 | Launcher | Windows only (expected) | |
| G8 | macOS / Linux | SKIP or manual if available | |

---

## Section H — Stability

| # | Step | Check |
|---|------|-------|
| H1 | 30 min session | MC + `/site` stay responsive |
| H2 | 10 Concierge messages | No memory leak / slowdown |
| H3 | Restart Genesis | Full boot &lt; 2 min (CEO target) |
| H4 | Offline API | Concierge fallback → link to `/order` |
| H5 | Frontend crash | Error boundary; recoverable |
| H6 | CPU idle | No runaway process after close |
| H7 | Multiple tabs | Two MC tabs — no corrupt state |

---

## Section I — Security (smoke)

| # | Step | Check | Crit |
|---|------|-------|------|
| I1 | `.env` not in git | `git status` clean of secrets | ⚠️ |
| I2 | API keys not in Concierge responses | |
| I3 | CORS | Production origins configured when deployed | |
| I4 | Public concierge | No owner-only data leaked | ⚠️ |
| I5 | Order PII | Email/phone only in order flow | |
| I6 | HTTPS | Production URL uses TLS | ⚠️ |

---

## Section J — Documentation

| # | Step | Check |
|---|------|-------|
| J1 | CEO can find First Customer Plan | `First_Customer_Plan_v1.md` |
| J2 | Payment setup documented | `Mission1_Payment_and_Launch_Strategy_v1.md` |
| J3 | Legal pages live | Impressum, Datenschutz, AGB |
| J4 | Contact email works or documented | hello@genesis-ai-engine.com |
| J5 | Disaster recovery | GitHub + secrets backup (CEO) |

---

## Section K — Final review

| # | Step | Check | Crit |
|---|------|-------|------|
| K1 | All ⚠️ PASS or documented BLOCKED | | ⚠️ |
| K2 | FAIL list empty or fixed | | ⚠️ |
| K3 | CEO sign-off: «I would pay for this» | Subjective | ⚠️ |
| K4 | Recommend Gewerbe | Only if K1–K3 yes | |
| K5 | Recommend public URL + live Stripe | Only if payment tested | ⚠️ |

---

## Cursor role during dogfooding

When CEO says **«Шаг A1»** or **«Release readiness»**:

1. State current step and what to do.  
2. Wait for CEO result (PASS/FAIL + notes).  
3. Record in Results file if asked.  
4. On FAIL — fix product bug (Type 1), not new architecture.  
5. Do not recommend Gewerbe until Section K passes.

**Example:**

> **Шаг C2 из 84.** Представь, что ты владелец кафе. Нажми 🍽️ или напиши: «Мне нужен сайт для кафе.»  
> Проверь: ответ понятен · есть цена или CTA · кнопка ведёт на заказ.  
> Отметь PASS или FAIL.

---

## Business model (reference — not part of this checklist)

| Model | What | When |
|-------|------|------|
| **Услуги** | Разовый проект (сайт, магазин…) — оплата за задачу | Mission 1 now — fixed packages |
| **Подписка** | Genesis Studio — платформа, AI, автоматизация | After Platform Launch Gate |

**Dynamic market pricing** (Market → Complexity → Hours → Margin → Recommended €): **Type 2** — after real orders and reliable sources. Until then: fixed packages + honest Concierge quotes. See `Mission1_Autonomous_Sales_Experience_v1.md`.

---

*Related: `First_Customer_Plan_v1.md` · `Mission1_AI_First_Website_UX_v1.md` · `Genesis_Business_Launch_Gate_v1.md` · `launcher/dogfooding.py`*
