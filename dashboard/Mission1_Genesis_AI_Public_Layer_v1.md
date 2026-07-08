# Mission 1 — Vector Public Layer v1

**Type:** Product · **NOT** governance  
**Date:** 2026-07-05 · **Updated:** 2026-07-08  
**Status:** ✅ Shipped — `/site` + `GenesisConcierge` · Voice on same layer

---

## Objective

Visitors on `/site` talk to **Vector** (assistant of **Virtus Core**) — like ChatGPT — not a FAQ widget.

**Not a chatbot.** Public AI — conversational intelligence for products, prices, limits, decisions.

---

## Architecture

```
Visitor text          Visitor voice
      ↓                      ↓
      └──────────┬───────────┘
                 ↓
          GenesisAIService          ← single intelligence (internal name)
                 ↓
    ┌────────────┴────────────┐
    ↓                         ↓
 Workforce / LLM           Rules fallback
                 ↓
 public_brand.py + personality layers
```

**One brain, two channels.** Voice: STT → same service → TTS.

---

## API (unchanged paths)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/public/genesis-ai` | Chat |
| `GET /api/public/genesis-ai/status` | `llm_configured`, `mode` |
| `GET /api/public/genesis-ai/greeting` | Personalized welcome |

Visitors see **Vector / Virtus Core** — never internal `Genesis` branding.

---

## UI

- `GenesisConcierge.tsx` on `/site` — public brand via `publicBrand.ts`
- Mission Control `/ai` — owner scope, same component

---

*Sales rules: `Mission1_Autonomous_Sales_Experience_v1.md`*
