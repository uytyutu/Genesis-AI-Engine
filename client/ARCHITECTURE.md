# Genesis Client — Stage 1 Architecture

**Mission:** Genesis Client Foundation · Stage 1  
**Статус:** 🟢 ACTIVE (параллельно RC2, не публикуется)  
**Цель:** фундамент Windows-first клиента без отвлечения от Mission 1.

---

## Выбор технологии

| Решение | Обоснование |
|---------|-------------|
| **Tauri 2** | Нативный Windows .exe, малый размер, Rust backend |
| **React + Vite** | Тот же UI-подход, что публичный сайт |
| **Shared tokens** | `client/shared/design-tokens.json` ← `app/lib/tokens.ts` |
| **API** | Railway `GENESIS_API_URL` — те же endpoints, что web |

**Не сейчас:** Electron (тяжелее), Flutter (другой UI stack), полноценный mobile.

---

## Структура репозитория (план)

```
client/
├── README.md
├── ARCHITECTURE.md          ← этот файл
├── shared/
│   └── design-tokens.json   ← синхрон с web
├── desktop/                 ← Tauri 2 (Windows first)
│   ├── src-tauri/
│   └── src/                 ← React shell
└── docs/
    └── STAGE1_CHECKLIST.md
```

---

## Stage 1 — scope (не полный продукт)

- [x] Выбор стека (Tauri 2 + React)
- [x] Архитектура и структура папок
- [x] Design tokens export
- [ ] `tauri init` в `client/desktop/` (следующий шаг после RC2 deploy)
- [ ] Пустой shell: sidebar + main area
- [ ] Auth scaffold (API key / session file, local only)
- [ ] `GET /api/health` ping

---

## Синхронизация с web

| Web (RC2) | Client |
|-----------|--------|
| `components/ui/*` | Копия или shared package (Stage 2) |
| `lib/tokens.ts` | `shared/design-tokens.json` |
| Public pages | N/A — client = owner workspace позже |

**Правило:** Client Foundation **не трогает** `dashboard/frontend/app` публичные страницы во время RC2.

---

## Платформы (порядок)

1. Windows (Stage 2)
2. macOS, Linux (Stage 3)
3. Android, iOS (Stage 4)

---

## Gate

Client **не релизится** до стабильного web + EL3 feedback. Stage 1 = проектирование + scaffold только.
