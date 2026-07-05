# Mission 1.5 — Business Acquisition Studio Foundation

**Статус:** 🔄 ACTIVE (параллельно Mission 1)  
**Дата:** 2026-07-04  
**Закон:** Genesis Law №1 — Plan → Approve → Act · Law №4 — Evidence Before Automation

---

## Цель

Genesis **выполняет весь цикл продаж**, кроме действий, требующих подтверждения CEO:

```
Найти → Анализировать → КП → Цена → Письмо → [Approve] → Отправка / CRM → Учиться
```

Не «сам зарабатывает». **Сам готовит — CEO подтверждает необратимое.**

---

## Что Studio умеет (Foundation)

| # | Функция | Авто? | CEO |
|---|---------|-------|-----|
| 1 | Журнал возможностей + сегменты дня | Ручной поиск | Добавляет лиды |
| 2 | Анализ сайта (HTTPS, mobile, SEO hints) | По запросу | — |
| 3 | Черновик КП + письма (DE, партнёрский тон) | Да | Редактирует |
| 4 | Рекомендация цены из пакетов | Да | Approve |
| 5 | Очередь одобрения | — | **Approve / Reject** |
| 6 | CRM (статусы, interactions, отказы) | Запись | Обновляет |
| 7 | Evidence report | После данных | Читает insights |

**API:** `/api/acquisition/*` · UI: `/acquisition` · Журнал: `/opportunities`

---

## Пять источников (горизонт, не все автоматизированы)

1. **Слабый сайт** — ручной поиск Maps / Gelbe Seiten → журнал  
2. **Запросы на площадках** — только официальные API (выкл. до EL3)  
3. **Входящие** — `/order`, email → журнал `inbound`  
4. **Повторные клиенты** — после первых проектов  
5. **Партнёры** — тип `partner` в журнале  

---

## Что Genesis НЕ делает

❌ Автопоиск компаний (спам-бот)  
❌ Автоотправка без `Approve`  
❌ Автоизменение цены  
❌ Договор / Stripe / публикация без CEO  

**Отправка email:** только при `GENESIS_OUTREACH_ENABLED=true` **и** Approve.  
**До Gewerbe:** готовить черновики, отправлять **вручную** (Bürgergeld).

---

## Каталог услуг

```
Genesis умеет → dogfood → успешные проекты → публичный каталог → Studio предлагает
```

Сейчас в каталоге: Landing Basic / Business / Premium (Factory).

---

## Evidence

После **30–50** реальных контактов — insights по сегментам и ценам.  
Тогда — настоящая Sales Studio automation (Horizon).

---

## Definition of Done (Foundation)

- [x] API prepare / approve / CRM / evidence  
- [x] UI очередь Approve  
- [x] Mission Control: «Одобрить письмо»  
- [ ] CEO: 5 лидов/день через Studio (ручной поиск)  
- [ ] Первый Approve → отправка (вручную или Resend)  
- [ ] Story #5 — первый незнакомый клиент (EL3)

---

**См. также:** `First_Customer_Plan_v1.md` · `Genesis_Laws.md` Story #1 · `Genesis_Company_OS_Maturity_v1.md`
