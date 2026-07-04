# Mission: Genesis Client Foundation

**Статус:** 🟢 STAGE 1 ACTIVE (после RC2 PASSED)  
**Цель:** фундамент кроссплатформенного клиента к EL3+.

---

## Stage 1 (сейчас)

- [x] Выбор стека: **Tauri 2 + React/Vite**
- [x] `client/ARCHITECTURE.md`
- [x] `client/shared/design-tokens.json`
- [x] `tauri init` → `client/desktop/`
- [x] Genesis shell (sidebar, titlebar, Home / Settings)
- [x] Theme system (dark / light / system)
- [x] Settings storage (local)
- [x] Auth scaffold + `GET /api/status` ping
- [x] Updater scaffold (plugin off until Stage 2)

**Checklist:** `client/docs/STAGE1_CHECKLIST.md`

---

## Этапы 2–4

| Этап | Платформа |
|------|-----------|
| 2 | Windows (рабочая версия, updater, native store) |
| 3 | macOS, Linux |
| 4 | Android, iOS |

---

## Правило

Не мешает Mission 1. Не публикуется как готовый продукт до gate.

**Prerequisite для `tauri dev`:** [Rust toolchain](https://www.rust-lang.org/tools/install)
