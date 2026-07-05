# Genesis Brand Guidelines v1.0

**Status:** FROZEN 2026-07-04 · **Genesis Brand v1.0**  
**Mark:** Orbit Stack (CEO approved)  
**Freeze doc:** `Genesis_Brand_v1_FROZEN.md`  
**Masters:** `brand/genesis-mark-master.svg` + `brand/genesis-mark-favicon.svg` (16-24px)  
**Regenerate:** `python scripts/generate_brand_assets.py`

> **Brand Law:** Бренд не меняется вместе с настроением. См. `Genesis_Brand_v1_FROZEN.md`.

---

## CEO decision: 5 concepts reviewed

### Concept 1 — Monogram G (legacy RC2)

White letter **G** on blue-violet gradient squircle.

| Pros | Cons |
|------|------|
| Simple, readable at 16px | Generic — many apps use letter marks |
| Already in production | Does not express Company OS |
| Fast to render | Feels "startup template", not premium OS |

**Verdict:** Retire as primary mark.

---

### Concept 2 — Orbit Stack (RECOMMENDED — implemented)

Three horizontal layers (Platform → Company → Executive) + **CEO core dot** + subtle orbit arc.

| Pros | Cons |
|------|------|
| Encodes **Company OS** metaphor | Slightly less obvious than "G" at 16px |
| Unique vs letter-only marks | Needs master SVG pipeline |
| Scales to 32px with contrast layers | |
| Aligns with Laws (human core = CEO) | |
| Premium gradient + shine (RC2 tokens) | |

**Verdict:** **Genesis Brand v1.0 FROZEN** — official mark.

---

### Favicon variant (16-24px)

Two layers + core only — `genesis-mark-favicon.svg`. Full mark (3 layers + orbit) from 32px up.

---

### Concept 3 — Bold ring G

Filled geometric G (stroke-free), Apple/Google style.

| Pros | Cons |
|------|------|
| Excellent small-size legibility | Still "another G app" |
| Timeless | No OS / layers story |

**Verdict:** Strong fallback; less differentiated.

---

### Concept 4 — Hex core

Hexagon with inner glow — "tech node".

| Pros | Cons |
|------|------|
| Reads "AI / tech" | Overused in crypto/Web3 |
| Distinct silhouette | Cold, not "company for humans" |

**Verdict:** Rejected — wrong emotional tone.

---

### Concept 5 — Gear / cog (legacy launcher)

Mechanical gear with G — old `build_icon.py` era.

| Pros | Cons |
|------|------|
| Suggests "engine" | Dated, industrial |
| | Conflicts with modern AI product aesthetic |
| | User explicitly excluded |

**Verdict:** **Removed.**

---

## Why Orbit Stack

Genesis is not a chat window. It is:

> **Company OS that helps the owner run the business — layers of capability orbiting human decisions.**

| Element | Meaning |
|---------|---------|
| Bottom layer (faint) | Platform / future infrastructure |
| Middle layer | Company operations |
| Top layer (bright) | Active executive decisions |
| Core dot | CEO — Law №5 accountability |
| Orbit arc | Continuous company cycle |

---

## Color palette

| Token | Hex | Use |
|-------|-----|-----|
| Genesis Blue | `#5b8def` | Gradient start |
| Genesis Indigo | `#4f46e5` | Gradient end |
| Surface dark | `#050508` | App background |
| Text primary | `#ececf1` | UI on dark |
| Mark white | `#ffffff` @ 96% | Layers on gradient |

**Gradient angle:** 135deg (RC2 consistent).

---

## Typography (wordmark)

- **Product name:** Genesis AI Engine  
- **Short:** Genesis  
- **Tagline (EN):** Company OS for digital business  
- **Component:** `GenesisLogo.tsx` — do not stretch mark

---

## Clear space & minimum size

| Context | Minimum |
|---------|---------|
| Favicon | 32x32 px |
| App icon | 48x48 dp (Android mdpi) |
| Sidebar | 36x36 px (2.25rem) |
| Marketing | 128px+ |

Clear space: **0.25x** mark width on all sides.

---

## Usage rules

### Do

- Use master SVG or generated assets only
- Run `generate_brand_assets.py` after SVG changes
- Place on dark or neutral backgrounds
- Use full-color on marketing; SVG in UI components

### Do not

- Rotate, skew, or add drop-shadow to the mark
- Change gradient colors without CEO approval
- Place on busy photos without dark scrim
- Use gear/legacy icons
- Recreate mark in a different font

---

## File map

| Output | Path |
|--------|------|
| Master SVG | `brand/genesis-mark-master.svg` |
| Launcher ICO/PNG | `launcher/assets/` |
| Tauri | `client/desktop/src-tauri/icons/` |
| Web SVG/PNG | `dashboard/frontend/public/brand/` |
| Desktop web | `client/desktop/public/icon.svg` |
| Android scaffold | `brand/generated/android/` |
| iOS scaffold | `brand/generated/ios/` |
| React components | `GenesisMark.tsx` (web + desktop) |

---

## Dark & light themes

Mark is **self-contained** (gradient background). Works on:

- Dark UI (Mission Control, Desktop) — primary  
- Light pages — add 1px border `#e5e7eb` if needed  
- Windows/macOS title bars — use generated ICO/ICNS

---

## Open Graph & PWA

- `app/opengraph-image.tsx` — dynamic OG with mark  
- `app/manifest.ts` — PWA icons 192/512  
- `app/icon.tsx` — favicon 32px (Orbit Stack layout)

---

## macOS ICNS note

`icon.icns` is PNG placeholder until built on macOS with `iconutil`. Windows/Linux/Android use ICO/PNG.

---

## CEO approval

| Item | Status |
|------|--------|
| Orbit Stack v1.0 | **FROZEN — CEO OFFICIALLY APPROVED** 2026-07-04 |
| Full asset rollout | `Genesis_Brand_CEO_Approval_Report_2026-07-04.md` |
| Favicon compact variant | Implemented |
| Legacy G / Gear | Retired |
| Brand audit | PASS — `scripts/brand_audit.py` |

---

*Quality reference (not copied): Linear, Raycast, Notion, Arc — minimal geometry, bold small-size forms, restrained gradients.*
