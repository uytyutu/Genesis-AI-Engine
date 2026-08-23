# Virtus AI Workspace (Canon)

**Status:** CANON · owner-directed · one panel · product ownership · Virtus AI orchestrator

Virtus Core does **not** ship a second admin outside the platform.
After purchase, every client (Standalone or Connected) gets **one Workspace**:

```text
app.virtuscore.de/client
```

Standalone and Connected are **different capabilities of the same workspace**, not different products or different panels.

## Mission

> After purchase the client is not left alone with HTML.
> They receive an AI partner that knows **their** project — and grows with the business.

## One panel rule

| Mode | What they see |
| --- | --- |
| **Standalone** | Site / store tools: pages, media, texts, contacts, products, orders, settings, backup, domain, basic stats + Marketplace |
| **Connected** | Same tools **plus** AI Assistant depth, CRM, analytics, chatbots, automations, email, WhatsApp, booking, notifications, Campaign Studio (later) |

Upgrade = unlock nav sections. **No migration. No new site.**

## Product ownership principle

> **Virtus AI may freely change and develop only products the client owns.
> Any capability belonging to another product requires a separate purchase or Connected.
> After purchase the module integrates into the existing project — no data move, no second site.**

Examples:

- Owned website → «Добавь страницу О компании» → plan + preview + apply.
- Not owned CRM → «CRM — отдельный продукт. После подключения он интегрируется с заявками.»

No hidden free ecosystem features.

## Virtus AI (not “Grok”, not universal chat)

### Who

Virtus AI is the **digital project director** for the client's business inside Virtus Core.

It knows: platform products, owned modules, project history, checklist stage, niche goals.
It does **not** write diplomas, solve physics, or cover world news.

### Orchestrator

```text
Client → Virtus AI → understand → inspect project → plan → pick model → change → preview → confirm → publish
```

Models (Claude / GPT / Grok / Gemini / local) are **internal**. The client only sees Virtus AI.
Hard-wiring the product to one vendor is forbidden.

### Character

Calm professional partner. Remembers last session. Softly returns chat to the project.
Not a ChatGPT clone. Not a chatterbox.

### Modes

1. **Dialogue** — natural language edits within owned products.
2. **Guided launch** — Business Checklist step-by-step after purchase.

## Business Checklist

### Launch (after purchase)

Site created → domain → hosting/publish → company email → GBP → social → WhatsApp → analytics → SEO → backup.

Niche-aware extras: store → first products; restaurant → menu; psychologist → booking (upsell if not owned).

Each step explains **why it matters** + deep-link into Workspace.

### Growth (after launch complete)

First leads → SEO → reviews → GBP → WhatsApp → ads (Connected may go deeper).

Standalone: do **not** aggressively push CRM/automation after launch.
Connected: Virtus AI may recommend ecosystem moves when evidence supports them.

## Marketplace (inside Workspace)

«Расширьте свой бизнес» — modules with honest prices (Chatbot, CRM, Booking, Email, WhatsApp, Store, Marketing Studio coming).
Activate → nav item appears → integrates with existing site.

## Studio Portfolio Test (eye KPI)

Open ~20 shuffled sites, remove logos, ask:

1. In 3 seconds — what does the company do?
2. Does it look like a modern European digital studio?
3. Unique company — or generator?
4. Would I show this to a new client as my work?
5. Does the next site feel like a completely different company?

Any «no» → REBUILD.

Price probe: strangers guess **1500–3000 € / “studio work”**, not **300–500 € template**.

Commercial PASS = owner eyes only. JSON / media_integrity PASS ≠ commercial PASS.

## Post-purchase flow

1. Order paid  
2. Factory builds product  
3. Workspace + client account created  
4. Email: login + temporary password  
5. First login → change password → Launch checklist + Virtus AI  

## Implementation anchors

- FE shell: `/client` · `ClientWorkspaceShell`
- Gates: `factory/commerce_gates.py` + `commerce_model.py`
- AI layer: `integration/virtus_ai/` over Vector dialog surfaces
- Marketplace: `/client/shop`
- Gallery: `package-previews` + `/reality-gallery`

## Non-goals (this canon phase)

- Full CMS page editor as fake-complete UI
- Live multi-LLM billing in production before orchestrator stub is honest
- Second cabinet outside `/client`
