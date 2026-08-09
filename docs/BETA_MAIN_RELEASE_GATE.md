# GATE: Beta → Main Release

**Status:** PASS обязателен по **всем** пунктам.  
**Среда проверки:** развёрнутая **beta** (не только localhost).  
**Правило:** merge в `main` разрешён только при полном PASS. Один FAIL → релиз откладывается.

Проверяет: владелец (CEO) или агент по поручению CEO. Отчёт — факты PASS/FAIL, без «должно работать».

---

## 0. STOP BREAKING THE BUILD (обязательно для агента / разработки)

**Репозиторий всегда должен оставаться deployable.** Не оставлять ветку в broken build.

Запрещённый цикл: изменить → push → Vercel упал → чинить → push снова.  
Правильный цикл: изменить → локально `typecheck` + `lint` + **`npm run build`** GREEN → commit → push → Vercel GREEN.

- Изменения `dashboard/frontend` (или того, что собирает Vercel): **без локального GREEN `npm run build` — нет commit.**
- Если Vercel RED после push: **стоп фич** → лог → починить build → только потом снова продукт.
- Cursor rule (локально): `.cursor/rules/deployable-build.mdc` (+ `git-workflow.mdc`).

---

## 1. Deployment

- [ ] Vercel build — GREEN
- [ ] Production build без ошибок
- [ ] Нет runtime errors
- [ ] Нет hydration errors

## 2. Commercial flow

### Website

- [ ] `/site`
- [ ] выбор услуги
- [ ] форма
- [ ] подтверждение
- [ ] оплата
- [ ] success

### AI Digital Employee

- [ ] выбор пакета
- [ ] понятный следующий шаг
- [ ] Workspace создаётся по текущему сценарию
- [ ] Stripe открывается

### Website Repair

- [ ] форма
- [ ] подтверждение
- [ ] оплата

### Free Website Check

- [ ] бесплатно
- [ ] нигде не появляется 149 €
- [ ] нет Stripe

### Coming Soon

- [ ] только Interest Form
- [ ] оплаты нет

## 3. Localization

### DE

- [ ] русский отсутствует
- [ ] английский отсутствует там, где должен быть немецкий
- [ ] Cookie Banner
- [ ] Footer
- [ ] Order
- [ ] Repair
- [ ] AI Employee

## 4. Security

- [ ] CEO Dashboard недоступен без авторизации
- [ ] `/owner`
- [ ] `/finance`
- [ ] `/business`
- [ ] `/projects`
- [ ] API → 401/403
- [ ] Google не видит внутренние страницы

## 5. Owner

- [ ] владелец входит без проблем
- [ ] refresh не разлогинивает
- [ ] Mission Control работает

## 6. Payments

- [ ] Stripe открывается
- [ ] Success page корректна
- [ ] письмо отправляется
- [ ] заказ создаётся

## 7. UX

- [ ] нет тупиков
- [ ] понятно, что будет после оплаты
- [ ] CTA понятны
- [ ] мобильная версия проверена

---

## Release Rule

| Результат | Действие |
|-----------|----------|
| Все разделы PASS | Можно merge в `main` (после явного OK владельца) |
| Хотя бы один FAIL | Релиз откладывается до исправления; повторный прогон Gate |

## Separation Rule (PR / commit)

**Ни один коммит и ни один PR не должен одновременно менять коммерческую логику и безопасность.**

| Тема | Отдельный PR |
|------|----------------|
| Авторизация / owner-gate / API 401 | отдельно |
| Витрина / формы / i18n / каталог | отдельно |
| Stripe / checkout / webhooks | отдельно |

Цель: исправление безопасности не ломает вход владельца и не смешивается с коммерческим сценарием.

См. также: `.cursor/rules/git-workflow.mdc` (one task = one commit).

---

## Release Evidence (перед merge)

Перед merge в `main` сохранить артефакты проверки (факты, не воспоминания):

- [ ] SHA коммита (ветка / tip, который уходит в main)
- [ ] URL beta
- [ ] Скриншоты ключевых экранов:
  - [ ] `/site`
  - [ ] Website order
  - [ ] AI Digital Employee
  - [ ] Free Website Check
  - [ ] Website Repair
  - [ ] Owner Gate
- [ ] Логи успешной сборки Vercel
- [ ] Результат `py scripts/verify_release.py` (локальный smoke)

Хранение: по желанию владельца (issue / заметка / папка вне репо с датой релиза). Без Evidence merge не считается закрытым.

---

## One major theme per release

**Ни один релиз не содержит одновременно более одной крупной темы.**

Примеры (по одному на релиз):

| Release | Тема |
|---------|------|
| A | Коммерческая витрина |
| B | Безопасность |
| C | AI Digital Employee |
| D | CRM |
| E | Stripe |

Цель: меньше регрессий, проще найти причину при FAIL на Gate.
