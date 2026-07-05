# Genesis i18n — shared localization

**Scope:** Desktop · Web · Mobile (future)  
**Default (CEO):** `ru`  
**Fallback:** `en`

## Add a language

1. Add locale id to `types.ts` → `LOCALE_IDS`
2. Register in `registry.ts` (`packReady: false` until translated)
3. Add `locales/<id>.json` (copy `en.json` structure)
4. Import pack in `core.ts` when ready

## CEO Desktop today

Full packs: **ru**, **en**, **de** — selector in Settings.

Other 14 locales: registered, fallback to English until Consumer launch.

## Chat language

**React:** `client/desktop/src/i18n/I18nProvider.tsx` wraps shared core.

## RTL

`ar`, `fa` — `dir: rtl` in registry; applied via `document.documentElement.dir`.

## Do not

- Hardcode UI strings in components — use `t('key')`
- Translate manually into 17 languages in one PR — add packs incrementally
