# Mission: Genesis Client Foundation

**Статус:** 🟢 STAGE 2 ACTIVE (Windows Client)  
**Цель:** рабочее Windows-приложение к EL3+.

---

## Stage 1 ✅

Scaffold, theme, settings, API ping — commit `248b305`.

## Stage 2 (сейчас)

**Checklist:** `client/docs/STAGE2_CHECKLIST.md`

| Экран | API |
|-------|-----|
| Connect | `/api/status` |
| Home | `/api/owner/dashboard` |
| Chat | `POST /api/assistant/ask` |
| Projects | `/api/factory/products` |
| Settings | local + disconnect |

**Осталось для полного Stage 2:** Rust toolchain → `npm run tauri dev` → packaged `.exe` smoke.

---

## Этапы 3–7 (Horizon / architecture)

| Этап | Название |
|------|----------|
| 3 | Company Brain |
| 4 | Executive |
| 5 | Marketplace |
| 6 | Digital Employees |
| 7 | Digital Departments |

Проектирование только — не полная реализация до EL3 feedback.

---

## Правило

Не мешает Mission 1. Каждый этап = реальная польза, не красивые пустые экраны.
