# Finish Desktop Identity — 2026-07-04

**Status:** **CLOSED (2026-07-08)** — Virtus Core migration shipped; CEO path works via `Genesis.exe`  
**Mission:** Brand v1.0 Orbit Stack + unified UI — **zero console for CEO**

---

## Honest answers

| Question | Answer |
|----------|--------|
| **Миграция бренда завершена полностью?** | **Да** — Virtus Core / Vector в launcher, MC, `/site`, Tauri UI (2026-07-08) |
| **Новый интерфейс завершён полностью?** | **Да на CEO path** — Launcher → Mission Control; Tauri = отдельный milestone |

**Brand v1.0 + Desktop UI = CLOSED** on daily CEO path (Tauri build optional later).

---

## CEO rule (2026-07-04) — FROZEN

> CEO **не** запускает PowerShell, **не** чистит кэш, **не** ищет причину.  
> Если для проверки нужна консоль — задача **не завершена**.

Genesis автоматически:

1. Обновляет ярлык `Desktop\Genesis.lnk` (иконка из `dist\Genesis.exe`)
2. Мягко обновляет кэш (`ie4uinit -show`) при каждом запуске
3. При смене exe/ico — **один раз** очищает icon cache и перезапускает Explorer (фоном, без участия CEO)

Код: `launcher/desktop_identity.py` · вызывается из `Genesis.exe` при старте и из `launcher/build.ps1`.

---

## USER CAN VERIFY (CEO — только это)

```
1. Двойной клик Genesis (рабочий стол)

2. Запустилось

3. Вижу Orbit Stack: ярлык · окно · панель задач

4. «Запустить Genesis» → новый интерфейс (sidebar + topbar)

5. Нет 500
```

**Без PowerShell. Без ручных команд.**

---

## Cursor self-verify (before asking CEO)

```bash
py scripts/verify_desktop_identity.py
py scripts/verify_release.py   # if available
```

Проверить exe · ico · shortcut · `.next` build · brand PNGs.

---

## Close criteria

- [x] CEO double-click only — Orbit Stack / Virtus mark on shortcut + launcher
- [x] CEO sees unified UI on daily path (Mission Control)
- [x] No 500 on startup (production `next start` with auto-repair)
- [ ] Tauri Desktop daily driver — отдельный milestone (Rust)

---

## Windows Icon Cache — почему не 100% без Explorer restart

Windows кэширует иконки **вне процесса приложения**. Genesis может:

- ✅ Пересобрать exe с новой иконкой
- ✅ Пересоздать ярлык с `IconLocation = exe,0`
- ✅ Вызвать `ie4uinit -show`
- ✅ Один раз очистить `iconcache*` + перезапустить Explorer при смене бренда

Полностью без перезапуска Explorer **иногда** невозможно на Windows 10/11 — это ограничение ОС, не Genesis. Genesis делает **максимум автоматически** при первом запуске после обновления.

---

*Working product beats working code.*
