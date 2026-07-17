# Path A — уровни доказательств (go-live)

**Locked:** CEO 2026-07-17  
**Scope:** продажа Landing Page («digitaler Neustart»), DE B2B  
**Не путать с:** RC1 Gates в `VECTOR_CAPABILITIES.md` (Documents / Sites / Analysis…)

Реальность важнее предположений. Три уровня — разные вопросы; один не заменяет другой.

| Уровень | Что доказывает | Что не доказывает |
|---------|----------------|-------------------|
| **1. Sandbox** (техническая проверка) | Логика реализована; сценарий проходит в тестовой среде | Готовность принять живого клиента |
| **2. Gate 1 + Gate 2** (готовность к эксплуатации) | Продукт готов к приёму реального клиента | Что боевая цепочка выдержит реальное использование |
| **3. Коммерческое доказательство** | Первый успешно выполненный заказ с реальным платежом | — (это первое настоящее подтверждение всей цепочки) |

Даже после обоих Gate остаются вещи, которые нельзя полностью подтвердить без реального использования (боевой webhook, доставка писем, поведение пользователей). Поэтому уровень 3 обязателен и отдельно от Gate.

**Правило:** первый реальный клиент — только когда пройдены **оба** Gate. После этого доказательство = первый успешный оплаченный заказ, не ещё один sandbox.

### Масштабный запуск vs контролируемый пилот

| Режим | Когда | Что значит |
|-------|--------|------------|
| **Контролируемый пилот** | Gate 1 + Gate 2 закрыты; 5–10 компаний | Ручной CEO-надзор, честная сдача пакета, feedback = дорожная карта |
| **Масштабный запуск** | После пилота + Factory = обещаниям пакетов | Автоматизированный поток без ручного «спасания» каждого заказа |

Пилот **легален** при ручной доводке Factory под оплаченный пакет. Открытый рынок — нет, пока обещание ≠ артефакт и язык клиента не чистый DE.

### Матрица Factory ↔ пакеты (HTML)

| Фича | Basic | Business | Premium |
|------|-------|----------|---------|
| One-page + responsive + Basis-SEO | ✅ | ✅ | ✅ |
| Kontakte + Anfrageformular | ✅ | ✅ | ✅ |
| WhatsApp-Button | ✅ | ✅ | ✅ |
| Google Maps embed | — | ✅ | ✅ |
| Bewertungsblock | — | ✅ | ✅ |
| Logo-Platzhalter (`logo.png`) | — | ✅ | ✅ |
| Erweitertes SEO = OG + Schema.org LocalBusiness (**kein** sitemap) | — | ✅ | ✅ |
| Premium-Design | — | — | ✅ |
| Kostenrechner | — | — | ✅ |
| Analytics-Platzhalter `G-XXXXXXXXXX` (ID manuell) | — | — | ✅ |
| Bewertungen = Textvorlagen (nicht echte Reviews) | — | ✅ | ✅ |
| Maps = Google Maps iframe nach Firmendaten | — | ✅ | ✅ |
| logo.png = Platzhalter bis Kundendatei | — | ✅ | ✅ |
| Korrekturen / Support / Domain-Hilfe | Prozess (CEO) | Prozess | Prozess |

Код: `app/factory/package_features.py` → `build_landing` / `start_production`.  
Контрольная закупка (без UI): `dashboard/backend/scripts/control_buy_business.py`.

### Двигатели денег (проверка 2026-07-17)

| Двигатель | Роль | Статус логики |
|-----------|------|---------------|
| **Stripe** (Path A) | Оплата Landing → webhook → settlement → Factory | ✅ подпись обязательна; idempotent replay; sandbox + redirect fallback; DE settlement 3 WD |
| **Toloka / Farm** | Параллельный labeling € | ✅ dry_run по умолчанию; auto-submit только `FARM_LIVE_MODE=live`; **не** подмешивает B2B в Outbox без `FARM_AUTO_PREPARE_OUTREACH=1` |
| **Country Desk** | Поиск DE SMB → письмо → `/order` | Отдельный путь; не зависит от Farm tick |

---

## Freeze — до первого пилотного клиента

**Не расширять:** TikTok · Content Engine · панель «Развитие» · новые направления Farm · админ-формы domain/GA до живого Gate 1 PASS.

**Фокус:** Gate 1 → первая реальная оплата → выполнение заказа → реакция клиента → только потом фичи.

## Gate 1 — пользовательский опыт

Клиент сам проходит весь обещанный путь (Genesis.exe → зелёный стек):

- [ ] заказ (`/order`, пакет **Business**)
- [ ] оплата (sandbox или Stripe test)
- [ ] статус заказа
- [ ] скачивание ZIP
- [ ] открытие `index.html` — WhatsApp · Maps iframe · отзывы-шаблоны · `logo.png` · OG + Schema
- [ ] правовые страницы клиента (Impressum / Datenschutz)
- [ ] нет неожиданных языковых или интерфейсных сбоев (DE-first Path A; `/order/pay` без RU)

### Gate 1 — чеклист Business ZIP

| Артефакт | Ожидание |
|----------|----------|
| `index.html` | имя фирмы, телефон из заказа |
| WhatsApp | `wa.me/…` |
| Maps | iframe `maps.google.com` + `#maps` |
| Bewertungen | `#testimonials` + пометка Beispieltexte |
| Logo | `logo.png` в разметке (файл кладёт клиент/CEO) |
| SEO | `og:title` + `application/ld+json` |
| Premium-only отсутствует | нет `G-XXXXXXXXXX`, нет `#calculator` |
| ZIP | `impressum.html`, `datenschutz.html`, `README_PUBLISH.txt` |

**Эталон без UI:** `py -3.12 dashboard/backend/scripts/control_buy_business.py` → `ALL_OK True`.

## Gate 2 — эксплуатационная готовность

Безопасно принять реальный заказ и оказать услугу:

- [ ] боевой Stripe и webhook
- [ ] корректные Impressum / Datenschutz **Virtus Core** (продавец)
- [ ] доступность сервиса и восстановление после сбоев
- [ ] понятные сообщения об ошибках для клиента
- [ ] логирование и возможность диагностировать проблемы

## Статус

| Уровень | Статус |
|---------|--------|
| Sandbox | ✅ `control_buy_business.py` ALL_OK (2026-07-18) — Business ZIP структура |
| Gate 1 (UI) | 🔄 **ждёт CEO** — стек :8000/:3000 не был зелёным после запуска Genesis.exe агентом |
| Gate 2 | 🔄 ждёт live Stripe/webhook + ops checklist |
| Коммерческое доказательство | ⏳ первый немецкий клиент 350–1200 € + довольный результат |

**Вердикт на сейчас:** продукт **готовится к контролируемому пилоту**, не к массовому рынку. Следующий вопрос бизнеса — не Factory, а «заплатит ли первый реальный клиент и останется ли доволен».
