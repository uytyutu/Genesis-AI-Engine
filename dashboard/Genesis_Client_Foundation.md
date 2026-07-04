# Mission: Genesis Client Foundation

**Статус:** 🔵 PLANNED (параллельно Mission 1 / RC1, не блокирует EL3)  
**Цель:** к моменту EL3 иметь не только сайт, но и **фундамент** настоящего кроссплатформенного клиента.

**Не путать с Horizon:** Marketplace, Multi-Agent Platform, Executive — по-прежнему 🔒 до EL3.

---

## Этапы

| Этап | Фокус | Когда |
|------|--------|-------|
| **1** | Архитектура, UI kit, главный экран, навигация, auth scaffold, API sync | Сейчас (постепенно) |
| **2** | Windows — рабочая версия (приоритет №1) | После этапа 1 |
| **3** | macOS, Linux | После стабильного Windows |
| **4** | Android, iPhone | После desktop |

**Почему Windows первой:** большинство первых пользователей — за компьютером; быстрее feedback до мобильных платформ.

---

## Этап 1 — чеклист (не начинать до завершения RC1 Release Audit)

- [ ] Выбрать стек (кандидат: Tauri 2 + React/Vite — единый UI, Windows-first)
- [ ] Структура monorepo / `client/` в репозитории
- [ ] Design tokens (shared с web public)
- [ ] Главный экран (shell)
- [ ] Навигация
- [ ] Auth scaffold (session / API key)
- [ ] Sync с Genesis API (`NEXT_PUBLIC_API_URL` / Railway)

---

## Правило

**Mission 1 (EL3) не замедляется.** Client Foundation — 10% времени Cursor, 90% — RC1 + первый клиент.
