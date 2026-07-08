# Mission 1 — Genesis AI Public Layer v1

**Type:** Product · **NOT** governance  
**Date:** 2026-07-05  
**Status:** Implemented (text) · Voice = same layer later

---

## Objective

Visitors on `/site` must feel they talk to **Genesis itself** — like ChatGPT — not a FAQ widget or order form.

**Not a chatbot.** **Genesis AI** — conversational intelligence that knows products, prices, limits, and guides decisions.

---

## Architecture (text + future voice)

```
Visitor text          Visitor voice (future)
      ↓                        ↓
      └──────────┬─────────────┘
                 ↓
          GenesisAIService          ← single intelligence
                 ↓
    ┌────────────┴────────────┐
    ↓                         ↓
 LlmChatProvider         Rules fallback
 (OpenAI-compatible)    (offline / no key)
    ↓
 genesis_ai_knowledge.py   (system prompt: products, prices, policies)
```

**One brain, two channels.** Voice adds STT → same `GenesisAIService` → TTS. No second assistant.

---

## API

| Endpoint | Purpose |
|----------|---------|
| `POST /api/public/genesis-ai` | Chat (alias: `/api/public/concierge`) |
| `GET /api/public/genesis-ai/status` | `llm_configured`, `mode` |

**Request:** `question`, `history[]`, optional `context`  
**Response:** `answer`, `mode` (`llm` \| `rules`), optional `cta_href` after client agrees

---

## Modes

| Mode | When | Visitor sees |
|------|------|--------------|
| **llm** | `GENESIS_LLM_API_KEY` or `OPENAI_API_KEY` in `dashboard/backend/.env` | Natural Genesis dialogue |
| **rules** | No key / LLM error | Structured fallback (dev only) |

### Mission 1 gate — BLOCKING

```
AI Conversation .... FAIL until llm_configured: true
```

Public release **not recommended** while status returns `"llm_configured": false`.

**Setup (CEO, ~2 min):**

1. Copy `dashboard/backend/.env.example` → `dashboard/backend/.env`
2. Set `GENESIS_LLM_API_KEY=sk-...`
3. Restart backend
4. Verify: `GET /api/public/genesis-ai/status` → `"llm_configured": true`

Visitors never see model name, provider, or mode — only **Genesis**.

---

## Configuration

```env
GENESIS_LLM_API_KEY=sk-...
GENESIS_LLM_MODEL=gpt-4o-mini
GENESIS_LLM_BASE_URL=https://api.openai.com/v1   # optional
```

---

## UI

Component: `GenesisConcierge.tsx` (export `GenesisAI`) — branded **Genesis AI** on `/site`.

---

*Sales rules: `Mission1_Autonomous_Sales_Experience_v1.md` · Dogfooding: `Mission1_Dogfooding_Guide.md`*
