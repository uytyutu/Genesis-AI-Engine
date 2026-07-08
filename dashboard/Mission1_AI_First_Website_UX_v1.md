# Mission 1 UX Improvement — AI First Experience v1

**Type:** Product improvement · **NOT** governance  
**Status:** Mission 1 · in progress  
**Date:** 2026-07-05  
**Implementation:** `/site` — `GenesisConcierge` + `ConciergeService`

---

## Goal

When a visitor opens Genesis, they immediately understand — within **2–3 minutes**, without AI experience:

- What Genesis is  
- What Genesis can build  
- Why Genesis is different  
- How Genesis helps them  
- What happens after they start  

**Not** a traditional landing page. **Entering Genesis itself.**

---

## Homepage Philosophy

- Do **not** design a traditional landing page  
- Do **not** overload with long paragraphs  
- Genesis **immediately begins helping** the visitor  
- Answers through **conversation**, not documentation search  

---

## Plain language rule (customer-facing)

Every string on `/site`, `/order`, and public pages must pass this test:

> **Would a café owner who never used Genesis understand it on first read?**

If the visitor has to think about what a sentence means — rewrite it.

| Avoid | Use |
|-------|-----|
| «6 вопросов» | «несколько простых вопросов» / «около минуты» |
| «от 350 €» above the fold | price after dialogue, or in collapsed «Пакеты» |
| «цена до оплаты» | «цена до оформления заказа» |
| «Conversation-first» | «Расскажите, что хотите создать» |
| «Qualification flow» | «Давайте уточним несколько деталей» |
| «Mode: rules / LLM» | never show to visitors — only **Genesis** |

---

## AI Concierge

Official **Genesis Guide** — not just a chatbot.

**Responsibilities:** welcome · explain · recommend · honest limits · pricing · workflow · purchase help · post-purchase guidance (future).

**API:** `POST /api/public/concierge`  
**UI:** `dashboard/frontend/app/components/GenesisConcierge.tsx`  
**Backend:** `dashboard/backend/app/integration/concierge_service.py`

---

## Conversation First

Main action is **not** «Buy» or «Contact us».

Primary prompt:

> **«Расскажите, что вы хотите создать…»**

Example chips: сайт для автосервиса · кафе · цена · как работает · что такое Genesis.

---

## Website Structure (natural answers)

1. What is Genesis?  
2. What can Genesis create?  
3. How does the process work?  
4. How much does it cost?  
5. What happens after payment?  
6. Can Genesis build my idea?  
7. How long?  
8. What happens next?  

Secondary content: collapsible `<details>` on `/site` — not above the fold.

---

## AI Learning (future)

Concierge improves: explanations · onboarding · conversion · satisfaction.  
Every interaction → training signal (after validation). Mission 1: rule-based + honest responses.

---

## Mission Control

CEO does **not** read routine chats. Dashboard shows: customers · revenue · conversion · common questions · AI recommendations.

---

## Long-Term Goal

The site should feel like **opening Genesis for the first time**:

> «This AI already understands me before I become a customer.»

---

## Related

- `dashboard/Mission1_Autonomous_Sales_Experience_v1.md`  
- `dashboard/First_Customer_Plan_v1.md`  

**No new governance documents.**

---

## Closing

Product task only. Next improvements: real visitor feedback, conversion on `/order`, post-payment guidance — not more vision docs.

---

## Post–Mission 1 (not now — capture only)

**Visitor qualification (3 questions):** business vs personal · logo yes/no · payment needed → ~80% project clarity → preliminary € and timeline → «Продолжить?»

**Dynamic market pricing:** Concierge / Sales AI analyzes comparable market rates (region, service type, scope) and suggests optimal price per service — evidence-based, not guesswork. Uses observable data + validated outcomes (same principle as Algorithm Intelligence). **Until Invoice #0001:** fixed packages in `SalesOrderService` — predictable for first customer.

**Visitor memory:** recognize returning visitors (future).

Do not implement above until Mission 1 commercial milestone unless CEO directs from real user feedback.
