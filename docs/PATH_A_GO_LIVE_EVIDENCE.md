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

## Gate 1 — пользовательский опыт

Клиент сам проходит весь обещанный путь:

- [ ] заказ
- [ ] оплата
- [ ] статус заказа
- [ ] скачивание ZIP
- [ ] открытие сайта
- [ ] правовые страницы клиента (Impressum / Datenschutz)
- [ ] нет неожиданных языковых или интерфейсных сбоев (DE-first Path A)

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
| Sandbox | ✅ логика Path A в тестах / локальных сценариях |
| Gate 1 | 🔄 ждёт живой проход CEO (Genesis.exe → клиентский путь) |
| Gate 2 | 🔄 ждёт live Stripe/webhook + ops checklist |
| Коммерческое доказательство | ⏳ после Gate 1 + Gate 2 |
