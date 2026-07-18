# Path A — уровни доказательств (go-live)

**Phase:** Ready for Pilot · **Gate 1 = HOLD**  
**Locked:** CEO 2026-07-17 · Gate 1 A+B+C 2026-07-18 · HOLD discipline 2026-07-18  
**Scope:** продажа Landing Page («digitaler Neustart»), DE B2B  
**Не путать с:** RC1 Gates в `VECTOR_CAPABILITIES.md` (Documents / Sites / Analysis…)

Реальность важнее предположений. Три уровня — разные вопросы; один не заменяет другой.

### Gate 1 = HOLD (канон статуса)

**HOLD ≠ «продукт плохой» и ≠ «нужны новые функции».**  
HOLD = отсутствует одно (или более) из **необходимых доказательств** приёмки (сейчас: живой UI + ZIP из Download).

Статус проекта меняется **не** количеством коммитов, а появлением новых **объективных** доказательств. Критерии приёмки воспроизводимы и не переписываются под удобство.

### Управление изменениями на HOLD (жёстко)

1. **Не расширять Scope**
2. **Не добавлять новые модули**
3. **Не менять критерии Gate 1** (A+B+C + Business-чеклист уже locked)
4. **Сначала** восстановить доступность стека (`:8000` / `:3000` через Genesis.exe)
5. **Затем** полный пользовательский путь Business → Download ZIP
6. **Только после этого** решение: Gate 1 PASS или FAIL по фактам

Запрещено на HOLD: TikTok · Content Engine · панель «Развитие» · новые направления Farm · «пока стек чиним — ещё фичу».

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
| **Go-live-Stufe (kommerziell)** | ZIP + Anleitung (Selbst-Publish) | + Hilfe Upload (Zugang Kunde) | + Voll-Publish Domain/SSL/Go-live (Zugang Kunde) |
| Domain/Hosting-**Miete** | ❌ zahlt Kunde | ❌ zahlt Kunde | ❌ zahlt Kunde |
| Hosting-Modell (Pilot) | Hilfe bei Wahl + Self-Publish | Hilfe bei Wahl + Upload | Hilfe bei Wahl + Voll-Publish |

**Оффер (канон):** продаём **готовый работающий результат** и услугу публикации по пакету; ZIP = владение файлами, не «главный продукт». Gate 1 критерии HTML **не меняются**.

### Hosting / Domain — граница ответственности (Pilot = Вариант 1)

```
Клиент → пакет → оплата Virtus → сайт (ZIP)
Business/Premium: Virtus публикует на хостинге клиента
  (существующий или новый по рекомендации)
```

| Вариант | Суть | Статус |
|---------|------|--------|
| **1 — Hilfe bei Wahl** | Помогаем выбрать; среди популярных в DE — Hetzner · IONOS · All-Inkl · Netcup; договор клиент↔провайдер; Premium/Business = Setup | **✅ пилот** (копия + README_PUBLISH) |
| 2 — Partner/Affiliate | редирект на оплату провайдера + комиссия | Horizon |
| 3 — Полный Reseller | Virtus продаёт домен/DNS/SSL/хостинг и счета | Horizon (другой бизнес) |

**Не делаем на Gate 1:** реселлер API, собственные счета за хостинг, PaymentCenter multi-vendor.

### Двигатели денег

| Двигатель | Роль | Статус логики |
|-----------|------|---------------|
| **Stripe** (Path A) | Оплата Landing → webhook → settlement → Factory | ✅ сумма из заказа на checkout; webhook: order exists · amount · **currency** · idempotent replay |
| **Toloka / Farm** | Параллельный labeling € | ✅ dry_run по умолчанию; auto-submit только `FARM_LIVE_MODE=live`; **не** подмешивает B2B в Outbox без `FARM_AUTO_PREPARE_OUTREACH=1` |
| **Country Desk** | Поиск DE SMB → письмо → `/order` | Отдельный путь; не зависит от Farm tick |

**PaymentCenter (Stripe / PayPal / Mollie):** Horizon — не внедрять на Gate 1 HOLD. Сейчас Factory видит только `paid` после `RevenuePipelineService`; мультивендор — после пилота.

**Ниши Factory (DE Path A):** dental · auto · **handwerk** · **computer** · **appliance** · law · beauty · energy · green · generic.

### Niche profiles — готовность к `niche_id` (ответ CTO)

| Вопрос | Ответ |
|--------|--------|
| Gate 1 завязан на один шаблон? | **Нет.** Уже есть `analysis.niche` + `resolve_niche_profile(niche_id)` + разные copy/palette. |
| Можно завтра добавить `niche_id`? | **Да.** Точка расширения: `app/factory/niche_profiles.py` → `resolve_niche_profile()`. `build_landing` уже берёт стиль по niche. |
| Полный `themes/{niche}/config.json` + бренд со старого сайта? | **Horizon после пилота** (15–20 отраслевых ключей, не 1000 шаблонов). |

### Дорожная карта тем (после Gate 1 + первого клиента)

```
Сейчас:   niche_profiles.py (палитра по niche) — Factory ядро стабильно
Потом:    themes/{niche}/ + Variant (dental/implant vs family) — без смены build_landing контракта
Позже:    Brand Transfer (цвет/лого/шрифт со старого сайта)
```

**Приоритет канон:** Gate 1 live → первый платящий → feedback → themes/variants → Brand Transfer.  
Не строить `themes/` и Brand Transfer под HOLD.

Gate 1 проверяет **механику** (продажа → оплата → ZIP-структура). Визуальные niche profiles уже не «случайный цвет», но file-based theme pack — не блокер Gate 1.

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

## Gate 1 — приёмка (PASS только при трёх уровнях)

**Правило:** Gate 1 = PASS **только** если совпали **все три** уровня. Один зелёный слой не засчитывает Gate.

| Уровень | Что подтверждает | Инструмент |
|---------|------------------|------------|
| **A. Автоматические тесты** | Логика работает | `pytest` (`test_package_delivery`) + `control_buy_business.py` → `ALL_OK` |
| **B. Живой UI-проход** | Пользователь оформляет заказ без скрытых проблем | Genesis.exe → зелёный стек → браузер `/order` |
| **C. Артефакт** | ZIP соответствует обещаниям выбранного пакета | Открытый `index.html` + `README_PUBLISH.txt` из **скачанного** ZIP |

**Hold at Gate 1:** см. канон HOLD выше — доступность стека → путь → решение. Без смены критериев.

### Gate 1 Business — критерии живого прохода (B + C)

- [ ] `/order` полностью на немецком (включая pay / status / ошибки)
- [ ] заказ Business оформляется без ошибок
- [ ] платёжный сценарий (sandbox или Stripe test) проходит корректно
- [ ] после оплаты доступен Download ZIP
- [ ] в `index.html` есть:
  - [ ] `wa.me/...`
  - [ ] Google Maps iframe
  - [ ] блок отзывов с пометкой `Beispieltexte`
  - [ ] `<img src="assets/logo.png">`
  - [ ] Open Graph и Schema.org `LocalBusiness`
- [ ] **нет** Premium-функций: Analytics (`G-XXXXXXXXXX`) и Rechner (`#calculator`)
- [ ] `README_PUBLISH.txt` ясно объясняет ручные шаги (logo, Domain, Analytics ID, отзывы)

### Gate 1 — статус слоёв (факт)

| Слой | Статус (2026-07-18) |
|------|---------------------|
| A. Автотесты + control-buy | ✅ `7 passed` · `ALL_OK True` |
| B. Живой UI | ❌ стек `:8000`/`:3000` down — проход не выполнен |
| C. ZIP из живого Download | ❌ нет (C через control-buy sandbox ✅, но **не** заменяет B+C из UI) |

**Итог Gate 1:** ❌ **не PASS** — A есть, B и живой C нет.

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
| Gate 1 | **HOLD** — A ✅ · B ❌ · C (живой Download) ❌; критерии не менять |
| Gate 2 | 🔄 после Gate 1 PASS |
| Коммерческое доказательство | ⏳ первый немецкий клиент + postmortem |

**Вердикт:** Gate 1 = **HOLD**. Следующее доказательство — зелёный стек и живой путь Business, не новый коммит фич.
