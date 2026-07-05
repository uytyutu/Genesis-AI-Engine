# Genesis Brand v1.0 — FROZEN

**Mark:** Orbit Stack  
**Status:** **CLOSED** · FROZEN 2026-07-04 · CEO OFFICIALLY APPROVED (Ramish)  
**Meaning:** Brand work is **done**. No more brand initiatives unless CEO explicitly requests.  
**Masters:** `brand/genesis-mark-master.svg` (full) · `brand/genesis-mark-favicon.svg` (16-24px)  
**Audit:** `brand/generated/audit/orbit-stack-size-audit.png`  
**CEO report:** `dashboard/Genesis_Brand_CEO_Approval_Report_2026-07-04.md`  
**Guidelines:** `Genesis_Brand_Guidelines_v1.md`

---

## Brand Law (not Genesis Law — brand constitution)

> **Бренд не меняется вместе с настроением.**

| Rule | Meaning |
|------|---------|
| **Freeze** | Orbit Stack v1.0 — единственный официальный mark |
| **Change gate** | Новый mark только при **серьёзной** причине + CEO Approve |
| **Serious reasons** | Юридический конфликт · нечитаемость на новой ОС · ребренд компании (не «нам кажется скучно») |
| **Pipeline** | Только `genesis-mark-master.svg` → `generate_brand_assets.py` |
| **No forks** | Не рисовать «ещё одну G» в отдельных экранах |
| **Horizon** | Любое предложение «сделать красивее» → Horizon, не выполнять |
| **Closed** | Приоритет разработки = функциональность, не бренд |

---

## Final Polish Audit — 2026-07-04

### 1. Узнаваемость по размерам

| Size | Variant | Result | Notes |
|------|---------|--------|-------|
| 16px | **compact** | PASS | 2 слоя + ядро; orbit убран |
| 24px | **compact** | PASS | Читается в табе браузера |
| 32px | full | PASS | 3 слоя + ядро |
| 48px | full | PASS | Android mdpi |
| 64px | full | PASS | Taskbar medium |
| 128px | full | PASS | Desktop shortcut |
| 256px | full | PASS | Windows ICO |
| 512px | full | PASS | Master export |
| 1024px | full | PASS | iOS App Store |

**Доработка:** добавлен `genesis-mark-favicon.svg` для ≤24px — упрощение без потери метафоры (слои + CEO).

---

### 2. Современность (5-10 лет)

**Честный ответ: да, с высокой вероятностью.**

| За | Против |
|----|--------|
| Геометрия, не модный 3D | Градиенты могут устареть визуально |
| Squircle — стандарт OS UI | |
| Нет текста в mark | |
| Нет «AI sparkle» клише | |
| Как Notion/Linear — форма, не эффект | |

Градиент `#5b8def→#4f46e5` привязан к RC2 — **не менять** без Brand gate.

---

### 3. Премиальность

| Критерий | Orbit Stack |
|----------|-------------|
| Чистые края | SVG, subpixel via cairo |
| Свет / глубина | Shine ellipse, не drop-shadow |
| Плотность | Не перегружен |
| Уникальность | Не буква, не шестерёнка |
| Уровень референсов | Соответствует minimalist SaaS tier |

---

### 4. Company OS (не чат-бот)

| Ассоциация | Элемент |
|------------|---------|
| Слои системы | 3 платформенных уровня |
| Человек в центре | Core dot (CEO) |
| Цикл работы | Orbit arc (только full, ≥32px) |
| Не ассоциируется | Робот, пузырь чата, буква G |

---

### 5. Desktop Windows

| Контекст | Asset | Status |
|----------|-------|--------|
| Рабочий стол | `genesis.ico` 16-256 | PASS |
| Панель задач | ICO 16/24/32 | PASS compact @16-24 |
| Пуск | ICO 48+ | PASS |
| Заголовок окна | Tauri `icon.ico` | PASS |
| Установщик | PyInstaller `--icon genesis.ico` | PASS |
| Проводник | ICO multi-size | PASS |

---

### 6. Website

| Контекст | Asset | Status |
|----------|-------|--------|
| Favicon 16/24/32 | `public/brand/favicon-*.png` + `icon.tsx` | PASS |
| SVG | `genesis-mark.svg` | PASS |
| Open Graph | `opengraph-image.tsx` | PASS |
| PWA | `manifest.ts` 192/512 | PASS |
| Apple touch | 180px | PASS |
| Mobile tabs | compact ≤24 | PASS |

---

### 7. Brand Consistency

| Surface | Source | Aligned |
|---------|--------|---------|
| Website | GenesisMark.tsx = master paths | YES |
| Desktop | Same component paths | YES |
| Windows Launcher | generate_brand_assets | YES |
| Tauri | same script | YES |
| Android scaffold | same script | YES |
| iOS scaffold | 1024/180 | YES |
| Documentation | This file + Guidelines | YES |
| Presentations | Use `genesis-mark-512.png` | YES |

**Единый визуальный язык:** squircle gradient + Orbit Stack white mark.

---

## Вердикт

**Orbit Stack остаётся лучшим вариантом после аудита.**

Зафиксировано как **Genesis Brand v1.0 FROZEN**.

Дальнейшие изменения — только через Brand Change Gate (CEO + документированная причина).

---

## Regenerate (never edit PNG/ICO by hand)

```bash
pip install -r scripts/requirements-brand.txt
python scripts/generate_brand_assets.py
```

---

*CEO: Orbit Stack approved. Brand frozen.*
