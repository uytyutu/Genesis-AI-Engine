# Context Pack — Business Profile SSOT (~30 lines)

**Law:** Enter once → use everywhere. One profile for paid Order **and** Giveaway. No second “gift client” identity.

**Chain (canonical):**
`User → Business Profile → (Order | Giveaway entitlement) → Website Basic → Factory → Client Workspace → Edit/Preview/ZIP → Upsell`

**Layers (do not mix):**
| Layer | Owns | Not |
|---|---|---|
| **User** | auth, email, person, Business ID | niche, services, media |
| **Business Profile** | company facts Factory needs | payment, Stripe |
| **Order / Giveaway** | commercial entitlement | copy of company facts |
| **Product (Website…)** | deliverable + edits → write-back to Profile | shadow company DB |

**Profile fields (v1 minimum):** name · niche · description · contacts · address · services · socials · logo/media refs · language/market. Extend later; never duplicate into each SKU.

**Today (facts):** `customer_identity` = User/Card + thin `DigitalCompany`; Factory still reads `business_interview` on order contacts — **gap to close**, not a second SSOT.

**Scope folders (implementation chats only):**
`dashboard/backend/app/integration/customer_identity/` · Factory **read adapter** only · Client Workspace profile UI · Vector context **read** of profile. No new parallel DB.

**Forbidden this mission:** Giveaway product UI · Shop SKU · B4.3 Vector rewrite · Mission 1 / Farm · new markdown canon outside this Pack.

**Slices:** (1) schema+store ✅ · (2) API+Owner/Client read ✅ · (3) Factory consume · (4) Workspace edit write-back · (5) Giveaway attaches to existing profile.

**PASS:** Same filled profile drives Factory + Website + Workspace + Vector Context; second purchase does not re-ask full form.
