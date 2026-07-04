# Stage 1 Checklist — Genesis Client Foundation

**Status:** 🟢 ACTIVE (после RC2 PASSED)

## Done

- [x] Tauri 2 + React/Vite scaffold (`client/desktop/`)
- [x] Genesis window shell (sidebar + titlebar + main)
- [x] Theme system (dark / light / system) from `shared/design-tokens.json`
- [x] Settings storage (`localStorage`, key `genesis.client.settings.v1`)
- [x] Auth scaffold (optional API key, local only)
- [x] API ping → `GET /api/status`
- [x] Navigation foundation (Home, Settings)
- [x] Updater scaffold (`lib/updater.ts`, Tauri plugin disabled in config)

## Local dev (no Rust)

```bash
cd client/desktop
npm install
npm run dev
# http://localhost:1420
```

## Desktop (requires Rust)

https://tauri.app/start/prerequisites/

```bash
cd client/desktop
npm run tauri dev
```

## Stage 2 (not now)

- `tauri-plugin-store` for native settings
- `tauri-plugin-updater` + release endpoint
- Owner workspace views
- Shared UI package with web RC2 kit
