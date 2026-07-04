# Stage 2 Checklist — Windows Client

**Status:** 🟢 IN PROGRESS  
**Rule:** каждый пункт приближает **рабочее** приложение, не декоративные экраны.

## Stage 2 goals

| # | Feature | Status | Real behavior |
|---|---------|--------|---------------|
| 1 | App window | ✅ | Tauri config 1200×760, centered, min size |
| 2 | Auth / connect | ✅ | Connect screen → `/api/status` + session |
| 3 | API connection | ✅ | Shared `apiClient`, live Railway |
| 4 | Home | ✅ | `/api/owner/dashboard` — stats, services, events |
| 5 | Chat | ✅ | `POST /api/assistant/ask`, history in localStorage |
| 6 | Projects | ✅ | `GET /api/factory/products` |
| 7 | Settings | ✅ | Account / API / theme cards |
| 8 | Command Palette | ✅ | `Ctrl+K` — navigate, search, disconnect |
| 9 | Auto-update | 🔄 | Scaffold; plugin off until release endpoint |
| 10 | Packaged `.exe` | ⬜ | Requires Rust — daily driver smoke |

## Run

```bash
cd client/desktop
npm run dev          # browser — full Stage 2 UX
npm run tauri dev    # native .exe (install Rust first)
```

## Prerequisite — Rust (Windows)

https://rustup.rs → then `npm run tauri dev`

**Roadmap:** `client/docs/ROADMAP.md`

- `tauri-plugin-store` native settings
- `tauri-plugin-updater` + signed releases
- Company Brain memory layer
- Shared UI package with web RC2 kit
