# Genesis Brand — CEO Approval Report

**Date:** 2026-07-04  
**CEO:** Ramish  
**Decision:** **APPROVED** — Genesis Brand v1.0 **Orbit Stack** is the official brand.

> Бренд не меняется вместе с настроением. (`Genesis_Brand_v1_FROZEN.md`)

---

## Actions completed

1. Regenerated **all raster assets** from `brand/genesis-mark-master.svg` + `genesis-mark-favicon.svg`  
2. Replaced legacy **letter G** marks in Desktop UI (Connect + titlebar) with `GenesisMark`  
3. Updated **Tauri Windows square logos** (StoreLogo, Square*) from master  
4. Ran **brand audit** — `scripts/brand_audit.py` → **PASS**

**Pipeline:** `python scripts/generate_brand_assets.py` → `python scripts/brand_audit.py`

**Visual audit:** `brand/generated/audit/orbit-stack-size-audit.png`

---

## Final audit result

| Check | Result |
|-------|--------|
| Legacy G / gear in UI | **PASS** (none) |
| Master SVG → all targets | **PASS** (50 files) |
| Size audit sheet | **PASS** |
| CEO approval recorded | **PASS** |

Machine-readable: `brand/generated/audit/brand-ceo-approval-report.json`

---

## Updated files (code)

| File | Change |
|------|--------|
| `client/desktop/src/pages/ConnectPage.tsx` | G → `GenesisMark` |
| `client/desktop/src/components/Shell.tsx` | G → `GenesisMark` |
| `client/desktop/src/styles/globals.css` | Logo styles for SVG |
| `dashboard/frontend/app/icon.tsx` | v1.0 FROZEN comment |
| `dashboard/Genesis_Brand_v1_FROZEN.md` | CEO officially approved |
| `scripts/generate_brand_assets.py` | Tauri Square* logos |
| `scripts/brand_audit.py` | CEO approval audit script |

---

## Regenerated assets (50 files)

### Masters
- `brand/genesis-mark-master.svg`
- `brand/genesis-mark-favicon.svg`

### Windows Launcher / Installer
- `launcher/assets/genesis.ico`
- `launcher/assets/genesis-icon.png`

### Tauri Desktop (Windows · Linux · macOS bundle)
- `client/desktop/src-tauri/icons/icon.ico`
- `client/desktop/src-tauri/icons/icon.icns` (+ `icon.icns.png`)
- `client/desktop/src-tauri/icons/icon.png`
- `client/desktop/src-tauri/icons/16x16.png` · `32x32.png` · `128x128.png` · `128x128@2x.png`
- `client/desktop/src-tauri/icons/Square30x30Logo.png` … `Square310x310Logo.png`
- `client/desktop/src-tauri/icons/StoreLogo.png`
- `client/desktop/public/icon.svg` · `icon-192.png` · `icon-512.png`
- `client/desktop/src/assets/genesis-mark.svg`

### Website (favicon · PWA · Open Graph)
- `dashboard/frontend/public/brand/genesis-mark.svg`
- `dashboard/frontend/public/brand/genesis-mark-favicon.svg`
- `dashboard/frontend/public/brand/favicon-16.png` · `favicon-24.png` · `favicon-32.png`
- `dashboard/frontend/public/brand/icon-192.png` · `icon-512.png`
- `dashboard/frontend/public/brand/apple-touch-icon.png`
- `dashboard/frontend/public/brand/genesis-mark-180.png` · `192.png` · `512.png`
- `dashboard/frontend/app/icon.tsx` (dynamic 32px)
- `dashboard/frontend/app/opengraph-image.tsx` (Orbit Stack mark)
- `dashboard/frontend/app/manifest.ts` → `/brand/icon-*.png`
- `dashboard/frontend/app/layout.tsx` → favicon metadata

### Android
- `brand/generated/android/mipmap-*/ic_launcher.png`
- `brand/generated/android/mipmap-*/ic_launcher_round.png`

### iOS
- `brand/generated/ios/AppIcon-1024.png`
- `brand/generated/ios/AppIcon-180.png`

### Audit
- `brand/generated/audit/orbit-stack-size-audit.png`
- `brand/generated/audit/brand-ceo-approval-report.json`

### React components (inline Orbit Stack)
- `dashboard/frontend/app/components/GenesisMark.tsx`
- `client/desktop/src/components/GenesisMark.tsx`

---

## Retired (do not use)

- Letter **G** monogram in UI  
- Gear icon  
- Manual PNG/ICO edits outside pipeline  
- `launcher/assets/generate_brand_icon.py` / `build_icon.py` — superseded by `scripts/generate_brand_assets.py`

---

## Brand Law

Orbit Stack v1.0 is **frozen**. Change only with documented serious reason + CEO Approve.

---

*Genesis Brand v1.0 · Orbit Stack · CEO Approved 2026-07-04*
