# Genesis Client

**Stage 1** — Tauri 2 + React/Vite desktop shell (Windows-first).

| Doc | Purpose |
|-----|---------|
| `ARCHITECTURE.md` | Stack, structure, gates |
| `docs/STAGE1_CHECKLIST.md` | Stage 1 tasks |
| `desktop/` | Runnable app |

## Quick start

```bash
cd client/desktop
npm install
npm run dev          # browser preview @ :1420
npm run tauri dev    # native window (Rust required)
```

Default API: `https://genesis-ai-engine-production.up.railway.app`

**Does not affect** Mission 1 public site or RC releases.
