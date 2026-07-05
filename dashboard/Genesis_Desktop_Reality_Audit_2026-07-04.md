# Genesis Desktop Reality Audit — 2026-07-04

**Status:** CEO **APPROVED** · Mandate: `Genesis_CEO_Mandate_Reality_First_v1.md`  
**Brand + UI migration:** **OPEN** — see `Genesis_Finish_Desktop_Identity_2026-07-04.md`  
**Principle:** If the change is not visible in the running app, the task is not done.

---

## Executive summary

| What reports claimed | What CEO actually runs |
|---------------------|------------------------|
| Brand v1.0 Orbit Stack everywhere | Partial — `.ico` updated in repo, **exe was stale** until this audit |
| Desktop Stage 2.5 / RC2 UI | **Tauri app** (`client/desktop`) — **never built** (no Rust on machine) |
| Mission Control refresh | **Web app** at `localhost:3000` — opened by **Launcher**, not Tauri |
| 500 error fixed | Caused by **corrupt `.next` cache** + past CSS compile failure |

**Root cause of mismatch:** Three different surfaces were conflated in reports:

1. **Genesis Launcher** — `dist\Genesis.exe` (PyInstaller, desktop shortcut)
2. **Mission Control** — Next.js web (`dashboard/frontend`, browser)
3. **Genesis Client** — Tauri native app (`client/desktop`, requires `tauri build`)

CEO shortcut → Launcher → browser Mission Control. **Not** Genesis Client.

---

## Answers (7 questions)

### 1. Why is the desktop icon still old/wrong after Brand v1.0?

- Shortcut icon: `launcher\assets\genesis.ico` (updated **2026-07-04 22:19**)
- Embedded exe icon: baked in at PyInstaller build time
- **Before audit:** `dist\Genesis.exe` built **2026-07-03 06:02** — **21 hours older than .ico**
- Windows also caches shortcut icons independently of file mtime

**Fix applied:** Rebuilt `dist\Genesis.exe` with Orbit Stack `.ico`. Recreated desktop shortcut. Run `launcher\refresh_windows_icons.ps1` if icon still cached.

### 2. Is Windows icon cache involved?

**Yes, very likely** for the desktop shortcut even when `.ico` file is correct. Windows Explorer does not always re-read `IconLocation` until cache refresh or shortcut recreate.

### 3. Was Desktop rebuilt after resource replacement?

| Artifact | Before audit | After audit |
|----------|--------------|-------------|
| `launcher\assets\genesis.ico` | Updated | Regenerated |
| `dist\Genesis.exe` | **Stale (Jul 3)** | **Rebuilt (Jul 4)** |
| `client/desktop` Vite `dist/` | Not for daily use | `npm run build` OK |
| Tauri `Genesis Client.exe` | **Never existed** | Blocked — **Rust not installed** |

### 4. Which `.exe` is actually launched?

Desktop shortcut `Genesis.lnk` → **`D:\Games\Genesis-AI-Engine\dist\Genesis.exe`**

This is the **Python Launcher** (CustomTkinter), not Tauri Genesis Client.

Launcher then starts local backend + frontend and opens **http://localhost:3000** (Mission Control).

### 5. Does the running build match the latest commit?

**No.**

- Git: `main` **ahead 9 commits**, large set of **uncommitted local changes** (brand, i18n, AI Hub, Dev Studio, acquisition, etc.)
- Running exe was built from working tree but **before** latest icon regeneration
- Production (Vercel/Railway) does **not** include uncommitted/pushed work

### 6. Why does UI barely change after RC2 / Stage 2.5?

| Surface | Stage 2.5 scope | CEO sees it? |
|---------|-----------------|--------------|
| Mission Control web | Partial brand (GenesisMark in nav), old layout | **Yes** — this is what Launcher opens |
| Genesis Client (Tauri) | Dev Studio, i18n, new shell, AI Hub panels | **No** — never built, never launched |
| Production website | Old deploy | If CEO opens vercel URL instead of localhost |

Reports described **code in `client/desktop`**. CEO uses **Launcher → Mission Control web**. Different products.

### 7. Why the 500 error?

**Found in `launcher\logs\frontend.log`:**

```
SyntaxError: Unexpected token, expected "," (37:14)
./app/globals.css → GET / 500
```

Cause: **broken Next.js dev cache** (`.next`) after a prior failed CSS compile. Webpack cache rename failures (`ENOENT` on `.pack.gz`).

**Fix:** Delete `dashboard\frontend\.next`, run `npm run build` — **build passes**, all routes including `/acquisition` compile.

---

## Actions completed in this audit

- [x] Regenerated all brand assets (`scripts/generate_brand_assets.py`)
- [x] Rebuilt `dist\Genesis.exe` with Orbit Stack icon embedded
- [x] Recreated desktop shortcut (`launcher\install_shortcut.ps1`)
- [x] Added `launcher\refresh_windows_icons.ps1` for icon cache
- [x] Cleared `.next`, verified `npm run build` succeeds
- [x] Built `client/desktop` Vite bundle (`npm run build`)
- [ ] Tauri native exe — **blocked: install Rust** (`https://rustup.rs`) then `cd client/desktop && npm run tauri build`

---

## CEO verification checklist

1. Close Genesis if running
2. Run: `powershell -ExecutionPolicy Bypass -File launcher\refresh_windows_icons.ps1`
3. Double-click desktop **Genesis** — icon should be Orbit Stack (blue gradient, white stack bars)
4. Click Launch — Mission Control should load **without 500**
5. For **new Desktop UI** (Dev Studio, i18n): install Rust, then build Tauri — or run dev: `cd client\desktop && npm run tauri dev`

---

## Honest gap

**Architecture strong. User-visible Desktop (Tauri) not shipped yet.**

Next rubicon for dogfood: either (A) CEO installs Rust + daily `Genesis Client.exe`, or (B) we promote Dev Studio into Mission Control web so Launcher path shows new features without Tauri.
