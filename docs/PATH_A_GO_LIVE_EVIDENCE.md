# Path A — уровни доказательств (go-live)

**Phase:** Ready for Pilot · **Hold at Gate 1** (UI)  
**Locked:** CEO 2026-07-17 · wording update 2026-07-18  
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

**Формулировка статуса ядра (канон):**  
> Техническое ядро подтверждено автоматическими тестами и контрольным сценарием. Теперь требуется подтверждение реальным пользовательским проходом.

Не говорить просто «технически ядро подтверждено» — без живого Gate 1 это неполная формулировка.

### Масштабный запуск vs контролируемый пилот

| Режим | Когда | Что значит |
|-------|--------|------------|
| **Контролируемый пилот** | После живого Gate 1 PASS; 5–10 компаний | CEO-надзор, честная сдача, feedback = дорожная карта |
| **Масштабный запуск** | После пилота + повторяемый процесс | Поток без ручного спасания каждого заказа |

### Матрица Factory ↔ пакеты (HTML)

| Фича | Basic | Business | Premium |
|------|-------|----------|---------|
| One-page + responsive + Basis-SEO | ✅ | ✅ | ✅ |
| Kontakte + Anfrageformular | ✅ | ✅ | ✅ |
| WhatsApp-Button | ✅ | ✅ | ✅ |
| Google Maps embed | — | ✅ | ✅ |
| Bewertungsblock (Beispieltexte) | — | ✅ | ✅ |
| Logo-Platzhalter (`assets/logo.png`) | — | ✅ | ✅ |
| Erweitertes SEO = OG + Schema.org LocalBusiness (**kein** sitemap) | — | ✅ | ✅ |
| Premium-Design | — | — | ✅ |
| Kostenrechner | — | — | ✅ |
| Analytics-Platzhalter `G-XXXXXXXXXX` | — | — | ✅ |
| Korrekturen / Support / Domain-Hilfe | Prozess (CEO) | Prozess | Prozess |

Код: `app/factory/package_features.py` → `build_landing` / `start_production`.  
Контрольная закупка (без UI): `dashboard/backend/scripts/control_buy_business.py`.

### Двигатели денег

| Двигатель | Роль | Статус логики |
|-----------|------|---------------|
| **Stripe** (Path A) | Оплата Landing → webhook → settlement → Factory | ✅ подпись обязательна; idempotent replay; sandbox + redirect fallback; DE settlement 3 WD |
| **Toloka / Farm** | Параллельный labeling € | ✅ dry_run по умолчанию; auto-submit только `FARM_LIVE_MODE=live`; **не** подмешивает B2B в Outbox без `FARM_AUTO_PREPARE_OUTREACH=1` |
| **Country Desk** | Поиск DE SMB → письмо → `/order` | Отдельный путь; не зависит от Farm tick |

---

## Freeze — до первого пилотного клиента и после него

**Не расширять до живого Gate 1 PASS:** TikTok · Content Engine · панель «Развитие» · новые направления Farm · админ-формы domain/GA «на всякий случай».

**После первого клиента** записывать замечания **только** в три корзины (не открывать фиче-бэклог):

| Корзина | Когда чинить | Примеры |
|---------|--------------|---------|
| **1. Критические** | Сразу | оплата не проходит · ZIP не скачивается · Factory ломается |
| **2. Доверие** | После подтверждения | непонятная формулировка · неясно, что в пакете · сложно найти кнопку |
| **3. Horizon** | Не трогать | TikTok · Content Engine · Development Center · новые движки |

Шаблон записи по заказу: `docs/FIRST_CUSTOMER_POSTMORTEM.md`.

**Фокус сейчас:** доступность стека → живой Gate 1 → первая реальная оплата → выполнение → реакция → postmortem.

## Gate 1 — пользовательский опыт

**Hold at Gate 1:** пока UI (Genesis.exe / :8000/:3000) недоступен — первоочередная задача **доступность**, не новые фичи. Сигнал CEO, когда стек зелёный → проход `/order` Business.

Клиент сам проходит весь обещанный путь (Genesis.exe → зелёный стек):

- [ ] заказ (`/order`, пакет **Business**)
- [ ] оплата (sandbox или Stripe test)
- [ ] статус заказа
- [ ] скачивание ZIP
- [ ] открытие `index.html` — WhatsApp · Maps iframe · отзывы-шаблоны · `assets/logo.png` · OG + Schema
- [ ] правовые страницы клиента (Impressum / Datenschutz)
- [ ] нет неожиданных языковых или интерфейсных сбоев (DE-first Path A; `/order/pay` без RU)

### Gate 1 — чеклист Business ZIP

| Элемент | Ожидание | Верификация |
|---------|----------|-------------|
| WhatsApp | `wa.me/…` | ссылка из номера заказа |
| Maps | iframe | контейнер `#maps` + `maps.google.com` |
| Testimonials | slot + disclaimer | `#testimonials` + `Beispieltexte` |
| Logo | slot | `img` с `src="assets/logo.png"` |
| OG + Schema | meta | `og:title` + `LocalBusiness` в `head` |
| Exclude | Analytics / Rechner | нет `G-XXXXXXXXXX`, нет `#calculator` |
| ZIP | полный набор | `impressum.html`, `datenschutz.html`, `README_PUBLISH.txt` |

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
| Sandbox | ✅ тесты + `control_buy_business.py` — структура Business ZIP |
| Gate 1 (UI) | 🔄 **Hold** — ждёт зелёный стек Genesis.exe (:8000/:3000), затем CEO-проход |
| Gate 2 | 🔄 ждёт live Stripe/webhook + ops checklist |
| Коммерческое доказательство | ⏳ первый немецкий клиент + postmortem |

**Вердикт:** Ready for Pilot по техническому контуру (тесты + control-buy). **Не** Ready for Mass Market. Следующий вопрос бизнеса — живой Gate 1 и первый оплаченный клиент, не новые фичи.
