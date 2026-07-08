# Genesis Runtime Investigation v1

**Mission:** prove browser uses latest code; document voice path; message trace.

## 1. Runtime checklist (verified)

| Risk | Finding |
|------|---------|
| Service Worker | **None** — no registration in `dashboard/frontend` |
| CDN | **None** locally; production = Railway direct |
| Stale backend | **Confirmed root cause** — port 8000 held old uvicorn; `hi_build: null` vs `v1.2` |
| localStorage | Old assistant messages replayed; fixed via `HI_BUILD_EXPECTED` cache bust |
| `.next` | Run `npm run build` after changes; dev uses HMR |

### Proof commands

```powershell
# Backend build id
Invoke-RestMethod http://127.0.0.1:8000/api/public/genesis-ai/status

# Must show: hi_build = human-intelligence-v1.2

# Frontend console on /site
# [Genesis runtime] { frontend_build, backend_hi_build, match: true }

# Clean rebuild
cd dashboard/frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run dev
```

## 2. Voice investigation

| API | Role |
|-----|------|
| `navigator.mediaDevices.getUserMedia` | Permission + mic stream (required before STT) |
| `webkitSpeechRecognition` | STT (Chrome/Edge) |
| `speechSynthesis` | TTS reply |

**Secure context:** HTTPS or `localhost` / `127.0.0.1` only.

**User never sees:** `NotAllowedError`, `DOMException`, stack — mapped in `voiceErrorMessage()`.

**Not a Next.js bug:** mic runs client-side; Next only serves JS bundle.

## 3. Message path: «Давай поговорим»

```
Browser GenesisConcierge.tsx
  → POST /api/public/genesis-ai?debug=1
  → main.py ask_concierge
  → GenesisAIService.chat (NOT ConciergeService)
  → GenesisBrain.chat
  → ConversationStateLayer (facts)
  → GenesisMemoryLayer
  → GenesisReasoningLayer + Intent
  → Provider chain → genesis-local (no API key)
  → GenesisPersonalityLayer.finalize
  → GenesisSelfCritiqueLayer
  → JSON { answer, debug.path }
```

**Legacy ConciergeService:** not called from `main.py`.

## 4. Conversation State (new)

```
Messages → Fact Extraction → conversation_state JSON per visitor
         → Reasoning (skip known fields)
         → One question max OR direct advice
```

Persisted: `memory/genesis_brain/users/{visitor_id}.json` → `conversation_state`.

## 5. Acceptance

Run before sign-off:

```powershell
python scripts/browser_acceptance_api.py
python scripts/genesis_50_dialogues.py
```

Browser: DevTools → Clear site data → `/site` → verify console `[Genesis runtime] match: true`.
