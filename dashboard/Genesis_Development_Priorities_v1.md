# Genesis Development Priorities v1

**Дата:** 2026-07-04 · **Статус:** FROZEN до EL3 review  
**Связано:** `Genesis_Readiness_Scorecard_v1.md` · `Genesis_Development_Policy.md`

---

## Правило выбора задачи

Не «всё подряд». Каждую задачу — через **два фильтра** (CEO mandate 2026-07-04):

| # | Вопрос | Нет → |
|---|--------|-------|
| 1 | Приближает **первого клиента** или **улучшает текущий Genesis**? | **Horizon** |
| 2 | **Не замедлит** Mission 1 или Development Studio? | **Horizon** |

> **Ни один новый цифровой отдел** (Trading Studio, Marketplace, Executive, Digital Employees, …) **не должен замедлять Mission 1 или Development Studio.**

Классический фильтр (сохраняется):

> **Эта функция приближает первый доход или повышает качество продукта?**

| Ответ | Действие |
|-------|----------|
| **Да** + оба фильтра выше | Делать (в порядке 1 → 8) |
| «Будет круто когда-нибудь» | **Horizon** — не сейчас |

**Reality First:** задача **не done**, пока CEO не может **увидеть** изменение. Отчёт без `USER CAN VERIFY` — неполный. См. `Genesis_CEO_Mandate_Reality_First_v1.md`.

**Коммерция OFF** до CEO Approve: live pay · подписки · Stripe Live · вывод · SaaS publish.

---

## Horizon (не делать без CEO)

| Область | Примеры |
|---------|---------|
| **Brand / visual identity** | новый логотип, цвета, «сделать красивее» |
| **Trading Studio** (код) | биржи, live data, ордера, автоторговля — **design OK:** `Genesis_Trading_Studio_*_v1.md` |
| Marketplace publish | Store, подписки |
| Custom LLM training | ChatGPT-scale model |

**Trading Studio gate:** Gewerbe · продажи услуг · daily Genesis · Company Brain · Executive → затем CEO Approve на build. До gate: только архитектура, roadmap, UI spec, API draft, paper-trading flow на бумаге.

**Приоритет #8** (после Consumer Platform): Mission 1 → Dev Studio → AI Hub → Desktop → Brain → Executive → Consumer → Trading.

---

## 🔴 Priority A — первый €

*Максимальный фокус Cursor, когда нет явной задачи CEO.*

| Область | Примеры |
|---------|---------|
| Сайт | UX, скорость, доверие, `/site` |
| Заказ | `/order`, checkout test, статус |
| Acquisition Studio | анализ, КП, Approve, Evidence |
| CRM | opportunities, interactions |
| Аналитика | сегменты, reply rate |
| Desktop | Daily Driver — то, что CEO открывает каждый день |
| Factory | скорость, качество лендинга |

---

## 🟠 Priority B — Genesis Company работает лучше

*После A или параллельно. **Post-brand build focus.***

| Область | Примеры |
|---------|---------|
| **Development Studio** | Handoff, Workspace, Stage 2 panels |
| **AI Hub** | Providers, routing, Planner scaffold |
| **Desktop Daily Driver** | 6–8 h/day CEO dogfood |
| **Company Brain** | **только на фактах** |
| Consumer Platform | i18n, chat attachments, CEO-first |
| Executive Dashboard | spec + foundation |
| Локальные AI-модули | assistant, handoff |
| Автоматизация | то, что dogfood уже доказал |

---

## 🔵 Priority C — будущее Platform

*Строить поэтапно. Не публиковать до Platform Launch Gate.*

| Область | Примеры |
|---------|---------|
| Windows Client | Tauri native |
| Android / iOS | scaffold |
| Linux / macOS | horizon |
| Marketplace | архитектура |
| Digital Employees | spec |
| API SDK · Enterprise | horizon |

---

## Genesis Weekly Progress (шаблон)

**Каждую неделю** — короткий отчёт в `dashboard/weekly/Genesis_Weekly_YYYY-MM-DD.md`:

```markdown
# Genesis Weekly — YYYY-MM-DD

## Сделано (максимум 5 пунктов)
- …

## Следующая самая полезная задача
→ …

## Причина
Это увеличивает вероятность первого клиента / качество продукта, потому что …

## Метрики (если есть)
- Лидов: … · Ответов: … · Desktop dogfood: …
```

Не список из 200 коммитов — **что даст максимальную пользу сейчас**.

---

*CEO mandate + priorities — обязательны для Cursor.*
