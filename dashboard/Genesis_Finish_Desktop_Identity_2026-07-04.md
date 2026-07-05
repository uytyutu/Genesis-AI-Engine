# Finish Desktop Identity — 2026-07-04

**Status:** **OPEN** — Cursor self-verify done; **CEO final check** after next report  
**Mission:** Brand v1.0 Orbit Stack + unified Genesis UI — **zero console for CEO**

---

## Honest answers

| Question | Answer |
|----------|--------|
| **Миграция бренда завершена полностью?** | **Нет** — автоматизация добавлена; CEO ещё не провёл финальный double-click test |
| **Новый интерфейс завершён полностью?** | **Нет** — shell готов; Tauri Desktop не собран |

**Brand v1.0 + Desktop UI = OPEN** until CEO confirms with **only double-click Genesis**.

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

- [ ] CEO double-click only — Orbit Stack everywhere
- [ ] CEO sees unified Genesis UI on daily path
- [ ] No 500 on startup (production `next start`)
- [ ] Tauri Desktop — отдельный milestone (Rust)

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
