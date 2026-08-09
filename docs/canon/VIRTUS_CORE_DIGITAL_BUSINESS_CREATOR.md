# Virtus Core — Digital Business Creator (Canon)

**Status:** CANON · owner-directed · supersedes Basic / Business / Premium ladder for *client-facing* commerce.

Virtus Core is **not** a website builder.
Virtus Core is an **AI Digital Business Platform**.

## Mission

> Virtus Core does not generate sites. It studies the business, understands the owner, and creates a digital presence that reflects the company — as if a European digital studio built it for this client alone.

## Generation philosophy

```
Human → Business → Goals → Brand → Site / Store / Workspace
```

Never:

```
Niche → Template → Swap text → Done
```

Factory starts by answering:

1. Who is this company?
2. Why should anyone trust them?
3. What do they sell?
4. Why choose them?
5. What atmosphere fits?
6. Who works there?
7. Which projects / media prove it?
8. Which Business Components does this model need?

Only then: HTML / Store / Admin.

## Commerce model (two modes)

| Mode | Promise | Billing |
| --- | --- | --- |
| **Standalone** | Buy once · own the product · self-host / ZIP · **same** Virtus AI Workspace (site tools only) | One-time |
| **Connected** | Same product · ecosystem in the **same** Workspace (CRM, AI depth, bots, automation, analytics) | Product + subscription |

One panel: `/client` — see `docs/canon/VIRTUS_AI_WORKSPACE.md`. Do not ship a second admin outside Virtus Core.

**Do not sell “Premium”.** Connected is ecosystem attachment, not a prettier template.

Legacy IDs (`basic` / `business` / `premium`) map for API compatibility:

- `basic` · `business` · `standalone` → **Standalone**
- `premium` · `connected` → **Connected**

## Catalog philosophy

The vitrine shows **ready digital solutions by business**, not “site types”:

- Business websites (Handwerk, Dachreinigung, Zahnarzt, …)
- Online stores by industry (Fashion, Beauty, Electronics, …)
- Automation products
- AI chatbots by role
- Marketing (later)

Each niche must feel visually distinct. Sub-niches (e.g. Italian family restaurant vs sushi bar) must produce different concepts.

## Smart AI Business Interview

Not five fields. A short interview (form **or** free-text dialogue) that captures:

- Company · city · team · founding
- Clients · segment
- Style / feeling (not template picker)
- Differentiator (Hero seed)
- Top services
- **Dream Mode** — five-year aspiration without budget limits
- **Business scale** — solo · small team · company · franchise

### Adaptive clarifying questions

After the owner speaks, Factory asks **business** questions that change the product — never technical ones.

Examples:

- Psychologist → online / practice / both?
- Restaurant → delivery? → zones + order CTA
- Craft → apartments / houses / commercial?

### Law №T — Factory owns technical decisions

The owner never chooses:

- sticky header · left nav · page count · renderer · widget checklist

They describe the business. **Virtus Core designs the digital solution.**

## Business Intelligence Generation (before HTML)

Order of artifacts:

```
Business Interview
→ Sub-niche + business model
→ Business Identity
→ Brand Book / Tone / Design System
→ Photography · Video · Motion language
→ Reputation · Local identity
→ Business Components (not “widgets”)
→ Media briefs
→ Website / Store / Workspace
```

## Business Components

AI selects components. The client does not pick a widget library.

Examples: Cost Calculator, Before/After, Online Booking, Menu, Practice Areas, Wishlist, Emergency Call.

## Quality law

If it feels like a template → **REBUILD**.
PASS only after: Would I buy? · German Company Test · Portfolio Test · 3-Second Test · Factory ≥ Virtus Core.

## Client-eye acceptance (portfolio bar)

Any sprint that claims quality must pass Reality Sprint (`docs/canon/VIRTUS_CORE_REALITY_SPRINT.md`):

1. Open ~10 sites across niches.
2. Remove logos — are they clearly different companies? (Law №4)
3. Would you show ≥8/10 to a prospect as portfolio?
4. Would a German owner say: «Ja — genau so einen Auftritt will ich»?

JSON artifacts alone are not enough. **Visible difference for the client wins.**

## Implementation SSOT files

- `app/factory/commerce_model.py`
- `app/factory/solution_catalog.py`
- `app/factory/business_interview.py`
- `app/factory/interview_clarify.py` — clarifying Q · scale · Dream Mode · technical decisions
- `app/factory/business_intelligence.py`
- `app/factory/factory_service.py` (orchestrates BI → media → HTML)
