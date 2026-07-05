# Genesis CEO Mandate — Reality First v1

**Date:** 2026-07-04  
**Status:** **APPROVED — FROZEN** until CEO review  
**Triggers:** Reality Audit 2026-07-04 · Trading Studio Horizon · focus mandate

---

## Главный вывод

Мы строим **один продукт**, а не три разных.

```
Launcher → Mission Control (Web)
Genesis Desktop (Tauri)
```

Для пользователя это **один Genesis**.

---

## Принцип разработки (новый, обязательный)

> **Работающий продукт важнее работающего кода.**

> **Если CEO не может увидеть изменение своими глазами — задача не завершена.**

Задача считается **завершённой** только если:

1. Изменение **видно** в работающем приложении
2. Прошла **ручная проверка**
3. CEO **может** это увидеть и проверить

Код в репозитории без видимого результата = **не done**.

---

## Два фильтра перед любой новой функцией

Cursor **обязан** ответить на оба вопроса **до начала работы**:

| # | Вопрос | Нет → |
|---|--------|-------|
| 1 | Приближает ли это **первого клиента** или **улучшает текущий Genesis**? | **Horizon** |
| 2 | **Не замедлит** ли это Mission 1 или Development Studio? | **Horizon** |

Применяется ко **всем** новым направлениям: Trading Studio, Marketplace, Executive, Digital Employees и любым будущим цифровым отделам.

### Правило цифровых отделов

> **Ни один новый цифровой отдел не должен замедлять Mission 1 или Development Studio.**

Архитектура и roadmap в Horizon — **OK**. Код и UI, отнимающие время у ядра — **нет**.

---

## Решение №1 — Отчёты = реальность

Больше нельзя считать задачу выполненной только потому, что изменился код.

Каждый отчёт о завершённом этапе **обязан** содержать:

```markdown
## USER CAN VERIFY

□ Что изменилось
□ Где открыть
□ Что должно быть видно
□ Что нажать
□ Что должно произойти
```

**Нет этого раздела → отчёт неполный.**

---

## Решение №2 — Launcher path до Tauri primary

Пока Tauri Desktop **не** основное приложение:

> **Launcher → Mission Control должен получать все важные новые возможности.**

CEO не должен читать отчёты о функциях, которыми нельзя пользоваться через свой ежедневный путь (ярлык Genesis → Mission Control).

Новые Studios / Hub / Brain-фичи — **сначала** в web Mission Control (или Launcher), **параллельно** Tauri когда Rust готов.

---

## Решение №3 — Rust = высокий приоритет

После установки Rust (`https://rustup.rs`):

1. Собрать настоящий **Genesis Desktop** (`client/desktop` · `npm run tauri build`)
2. Ежедневно запускать **его**
3. Постепенно отказаться от браузера как основного окна

До сборки Tauri — Mission Control остаётся **primary surface**, но с тем же функционалом.

---

## Решение №4 — USER CAN VERIFY (шаблон)

**CEO — только double-click. Без PowerShell.**

```markdown
## USER CAN VERIFY

1. Двойной клик Genesis
2. Orbit Stack: ярлык · окно · панель задач
3. «Запустить Genesis»
4. Новый UI + нет 500
```

Cursor **до отчёта** сам: `py scripts/verify_desktop_identity.py` · rebuild exe · auto shortcut/icon.

---

## Решение №5 — Reality Audit после каждого большого этапа

После крупного релиза / этапа — **Reality Audit**:

| Проверить | |
|-----------|--|
| Иконка рабочего стола | Orbit Stack · не stale exe |
| Какой `.exe` запускается | `dist\Genesis.exe` vs Tauri |
| Launcher | стартует без ошибок |
| Desktop (Tauri) | собран · совпадает с коммитом |
| Web (Mission Control) | localhost · нет 500 |
| Production | Vercel/Railway vs local |
| Git | committed · pushed если нужно |
| Build | exe пересобран после ресурсов |

Сравнивать **то, что видит пользователь**, не diff в коде.

Шаблон: `Genesis_Desktop_Reality_Audit_2026-07-04.md`

---

## Приоритеты (зафиксировано)

| # | Направление |
|---|-------------|
| 1 | **Mission 1** — первые реальные клиенты |
| 2 | **Development Studio** — Genesis заменяет Cursor как рабочее место |
| 3 | **AI Hub** — единая работа с AI-моделями |
| 4 | **Desktop Daily Driver** — Genesis = главное окно |
| 5 | **Company Brain** — память на реальном опыте |
| 6 | Executive Dashboard |
| 7 | Consumer Platform |
| 8 | Trading Studio — **Horizon** (после этапов 1–7 + gate) |

**Фокус Cursor:** перестать открывать новые большие направления. **Довести существующее** до ежедневного использования.

---

## Trading Studio (Horizon — без изменений)

Архитектура и Roadmap остаются. См. `Genesis_Trading_Studio_*_v1.md`.

**Разрешено:** документация · архитектура · UX · модели · paper · backtest · risk · journal (на бумаге).

**Запрещено до CEO Gate:** биржи · реальные сделки · капитал компании · автоторговля.

---

## Связанные документы

- `Genesis_Desktop_Reality_Audit_2026-07-04.md` — первый audit
- `Genesis_Development_Priorities_v1.md` — A/B/C + фильтры
- `Genesis_Development_Policy.md` — непрерывная разработка
- `.cursor/rules/genesis-development.mdc` — правила Cursor

---

*CEO APPROVED · Reality First · один продукт · сильное ядро до расширения экосистемы*
