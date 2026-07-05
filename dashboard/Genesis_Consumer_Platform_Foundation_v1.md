# Genesis Consumer Platform Foundation v1

**Date:** 2026-07-04  
**Status:** Foundation laid — CEO Desktop i18n + architecture  
**Gate:** Platform Launch Gate — no Store, no subscriptions, no marketplace

---

## Главный принцип

Genesis строится как **Company OS**.

1. Сначала — лучший инструмент для CEO (Dogfood First)  
2. Потом — упрощённая Consumer версия для клиентов по всему миру (One Window)

Стратегия **не меняется**. Этот документ — технический фундамент.

---

## §2 — Русский язык для CEO (implemented)

| Item | Status |
|------|--------|
| Default locale | **ru** |
| CEO Desktop packs | ru, en, de — full |
| Settings selector | Русский / English / Deutsch |
| Storage | `settings.locale` in `genesis.client.settings.v3` |

**Code:** `client/shared/i18n/` · Desktop `SettingsPage` · `I18nProvider`

Остальные строки Home (статистика, API labels) — **следующий проход** i18n; chrome локализован.

---

## §3 — Международная локализация (architecture)

### Stack

```
client/shared/i18n/
├── types.ts          # 17 locale ids
├── registry.ts       # metadata, RTL, packReady flags
├── core.ts           # t(locale, key), fallback en
├── detect.ts         # script detection for chat
├── I18nProvider.tsx  # React context
└── locales/
    ├── ru.json       # CEO pack ✅
    ├── en.json       # CEO pack ✅
    └── de.json       # CEO pack ✅
```

### Supported locales (registered)

| Code | Language | Pack | RTL |
|------|----------|------|-----|
| ru | Русский | ✅ | |
| en | English | ✅ | |
| de | Deutsch | ✅ | |
| uk | Українська | fallback en | |
| fr | Français | fallback en | |
| es | Español | fallback en | |
| it | Italiano | fallback en | |
| pt | Português | fallback en | |
| pl | Polski | fallback en | |
| tr | Türkçe | fallback en | |
| ar | العربية | fallback en | ✅ |
| fa | فارسی | fallback en | ✅ |
| hi | हिन्दी | fallback en | |
| zh-Hans | 中文（简体） | fallback en | |
| zh-Hant | 中文（繁體） | fallback en | |
| ja | 日本語 | fallback en | |
| ko | 한국어 | fallback en | |

### Add a language (no manual scatter)

1. Copy `locales/en.json` → `locales/<id>.json`  
2. Translate keys (or machine-translate + review)  
3. Import in `core.ts`, set `packReady: true` in `registry.ts`  

**Не переводить вручную все 17 сразу** — система готова, паки добавляются по мере Consumer launch.

### Future: Web + Mobile

Same `client/shared/i18n` — import from Next.js and Tauri/Capacitor shells.

---

## §4 — Общение с пользователем (implemented foundation)

| Rule | Implementation |
|------|----------------|
| User writes in X → Genesis replies in X | `detect_locale_from_text()` + `effective_chat_locale()` |
| UI locale as default | `settings.locale` passed to `/api/assistant/ask` |
| Rule-based assistant | Full templates **ru / en / de** |
| Other locales (fa, ar, ja…) | Reply in **English** until LLM stage |
| LLM stage | Provider returns in detected locale when model supports |

**Backend:** `locale_service.py`, `assistant_locale.py`, `assistant_service.py`  
**API:** `POST /api/assistant/ask` `{ question, locale? }`

---

## §5 — Платформы (architecture)

### Shared core (max reuse)

```
client/
├── shared/
│   ├── design-tokens.json
│   └── i18n/                 ← UI strings, all platforms
├── desktop/                  ← Tauri 2 (Windows first) ✅
├── web/                      ← dashboard/frontend (existing)
└── mobile/                   ← FUTURE: Tauri mobile or Capacitor shell
```

### Platform matrix

| Platform | Shell | Status | Notes |
|----------|-------|--------|-------|
| Windows | Tauri 2 | ✅ Active | Primary CEO target |
| macOS | Tauri 2 | 🔜 Stage 3 | `icon.icns` placeholder |
| Linux | Tauri 2 | 🔜 Stage 3 | Same React bundle |
| Android | Tauri mobile / scaffold | 📋 Icons in `brand/generated/android` |
| iPhone | Tauri mobile / scaffold | 📋 Icons in `brand/generated/ios` |
| iPad | Same as iOS | 📋 Responsive Consumer layout |

**Принцип:** один React UI + shared i18n/tokens; различаются только **native shell**, **window chrome**, **store packaging** (post-gate).

---

## §6 — Consumer UX (architecture, not built)

### CEO Mode (owner)

Full access:

- Development Studio (future)  
- Executive · Company Brain  
- Mission Control modules  
- Factory · internal tools  

**Today:** Desktop = CEO workspace (single mode).

### Consumer Mode (clients)

Simple nav:

```
Главная · Чат · Проекты · Файлы · Настройки · Поддержка
```

No internal Genesis Company modules.

### Implementation plan (post-foundation)

```typescript
// Future: client/shared/mode.ts
type AppMode = "ceo" | "consumer";

// Resolved from: auth role, license, feature flags
// CEO: full Sidebar nav
// Consumer: consumerNav only + i18n from user locale
```

**Gate:** Consumer Mode ships with Platform Launch Gate, not before.

---

## §7 — One Window & AI Hub (vision v1)

**Canonical:** `Genesis_AI_Hub_Architecture_v1.md` · `Genesis_One_Window_Roadmap_v1.md`

| Stage | Summary | Status |
|-------|---------|--------|
| **1** | Cursor as engine — plan · approve · handoff · verify (text + voice) | 🔜 next code |
| **2** | Multi-provider Hub (capability routing) | ❌ scaffold only |
| **3** | Development Studio (editor · git · terminal) | ❌ |
| **4** | Perfect Pallet in Genesis Desktop | ❌ dogfood target |
| **5** | Genesis primary; Cursor background | ❌ |

**Provider layer:** `client/shared/ai-hub/` · `ai_hub/provider_registry.py`

**Rule:** Do not remove Cursor early. Transition is gradual.

Detail: `Genesis_Development_Studio_Audit_v1.md`

---

## §8 — Не делать сейчас

- Windows Store / Microsoft Store  
- App Store / Google Play  
- Subscriptions / Marketplace / SaaS publish  

→ **Platform Launch Gate**

---

## Files touched (v1 foundation)

| Area | Path |
|------|------|
| i18n shared | `client/shared/i18n/*` |
| Desktop wiring | `client/desktop/src/App.tsx`, Settings, Sidebar, Shell, Connect |
| Assistant locale | `dashboard/backend/app/integration/locale_service.py` |
| Tests | `tests/test_locale_service.py`, `tests/test_assistant_timeline.py` |

---

*Genesis Consumer Platform Foundation v1 · aligns with Dogfood First + One Window*
