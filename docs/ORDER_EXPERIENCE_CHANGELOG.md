# Order Experience Changelog

UX journal for Path A `/order` — not a technical log. Track what we ship for conversion and what we learn from real buyers.

## Roadmap

| ID | Theme | Status |
|----|--------|--------|
| A1.1 | Autosave & Resume Draft | Done (`61eee9f`) |
| A1.2 | Wizard Navigation | Done (`bb0fbdf`) |
| A1.3 | Live Preview / AI Guidance | Done (`a5eb22e`) |
| A1.4 | Premium Checkout Experience | Done (this slice) |
| A1.5 | (reserved / deepen checkout) | Planned |
| A1.6 | Payment Confirmation Experience | Planned |

## Entries

### A1.1 — Autosave & Resume Draft (2026-07-21)

**Why:** Long 4-step form lost all input on refresh — silent conversion killer.

**Shipped:**
- Debounced local draft on this device (`visitor_id` × market)
- Restore after refresh with clear banner
- Start over
- Clear draft after successful order create
- Localized strings + smoke test

**Expected effect:** Fewer abandoned mid-form sessions after accidental refresh or tab restore.

**Measure later:** drop-off between step 1→2 and refresh-return rate (funnel events / support notes).

---

### A1.2 — Wizard Navigation (2026-07-21)

**Why:** After drafts survive refresh, buyers still need clear progress and safe movement between opened steps.

**Shipped:**
- Progress markers: completed (✓), current (➜), locked (○)
- Click only steps already opened (`maxReachedStep` in draft)
- Sticky Back / Next bar; Next validates only the current step
- Draft stores `formStep` + `maxReachedStep`; restore lands on the saved step

**Expected effect:** Less confusion mid-funnel; fewer “where was I?” abandons.

**Measure later:** time-on-step and back-navigation rate vs drop-off.

---

### A1.3 — Live Preview & AI Guidance (2026-07-21)

**Why:** Turn “filling a form” into “watching my site take shape” — without running Factory ZIP.

**Shipped:**
- Live mini-site chrome (name, niche, package, brand style / palette)
- Guidance block from Composer rules (niche, style, hero hint, market, language) — no LLM
- Progress strip (structure / style / colors / package / contacts / details)
- Example carousel kept below as secondary proof

**Explicit non-goal:** Factory generation / ZIP during order.

**Expected effect:** Higher intent to pay — buyer feels the product is already working.

**Measure later:** time on `/order` with package selected; conversion step 3→4→pay.

---

### A1.4 — Premium Checkout Experience (2026-07-21)

**Why:** Reduce uncertainty at the money moment — clear summary, process after pay, single dominant CTA.

**Shipped:**
- Final order summary (company, niche, market, language, package, deliverables, price)
- After-payment steps (register → Factory → Compliance → ZIP → email)
- “I checked the details” confirmation before pay is enabled
- Dominant pay block (package + price + Pay)

**Explicit non-goals:** upsells, timers, scarcity, popups.

**Expected effect:** Higher checkout start rate; fewer “what happens next?” support questions.

**Measure later:** checkout_start / payment success vs confirm-checkbox abandon.

---

### Later (not started)

- **A1.6** — richer payment confirmation / status experience  
- Then **Mission A2** — first real sales + friction journal  

After first real sales, annotate which A1 rows moved conversion.
