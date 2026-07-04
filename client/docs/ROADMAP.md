# Genesis Client — Development Roadmap

Последовательный план разработки (не мечты).

| # | Этап | Статус | Критерий |
|---|------|--------|----------|
| 1 | Foundation | ✅ | Tauri + tokens |
| 2 | Genesis Desktop v1 | ✅ commit | Connect, Home, Chat, Projects, Settings |
| **2.5** | **Daily Driver** | 🔄 **NOW** | 70–80% работы без браузера |
| 3 | Company Brain v1 | 📐 | Память компании: решения, клиенты, уроки |
| 4 | Executive v1 | 📐 | CEO mode |
| 5 | Digital Employees v1 | 📐 | Sales first |
| 6 | Marketplace v1 | 📐 | Module catalog |
| 7 | Digital Departments | 📐 | Teams of employees |
| 8 | macOS / Linux / mobile | 📐 | After Windows stable |

---

## Stage 2.5 — Daily Driver (active)

**Doc:** `STAGE2_5_DAILY_DRIVER.md`

**Gate → push (оба):**
1. Rust → native window (`npm run tauri dev`)
2. CEO: *«Мне удобнее Desktop»* (заменяет 70–80% браузера)

**Не переходить к Stage 3 до закрытия 2.5.**

---

## Stage 3 — Company Brain

Не просто память чата. Память **компании**:

- почему приняли решение;
- почему отказались;
- что сказал клиент;
- чему научились;
- что сработало / не сработало.

Строится **поверх** Daily Driver Desktop.
