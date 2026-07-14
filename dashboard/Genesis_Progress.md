# 📍 Genesis Progress

> **Контракт Mission 1** (не рабочий черновик). Модель FROZEN. Обновляется только: статус блоков · блокер · результат спринта.

## Genesis Canon 1.0 — LOCKED 2026-07-13

> **Не изменять.** Канон перестал расти — он **фильтр**, не цель. Дневник пользователя **сильнее канона**.

> **Философия больше не развивается. Теперь развивается продукт.**

> **Мы не создаём лучший искусственный интеллект.**  
> **Мы не создаём лучший генератор сайтов.**  
> **Мы не создаём лучшую CRM.**  
> **Мы создаём место, где человек постепенно становится тем предпринимателем, которым всегда хотел быть.**

### Правила разработки (рядом с каноном — не философия)

**Конец спринта** — не «15 тестов PASS», не «архитектура улучшена». Один вопрос:

> **Что изменилось в жизни пользователя после этого спринта?**

«Ничего» → спринт не выполнил миссию.  
«Самостоятельно сделал шаг, которого вчера боялся» → спринт успешен.

**Качество спринта:** *Какую страницу книги пользователя мы пытаемся сделать настоящей?*

**Definition of Change (вместо DoD):**

```text
После этого спринта жизнь пользователя изменилась хотя бы на один реальный шаг?
Ответ: Да. / Нет.
```

Без промежуточных формулировок.

**Цикл спринта (четыре части):**

1. **Один дневник** — один человек, один вечер (не пять сценариев)
2. **Один разрыв** — только первый момент, где доверие исчезло
3. **Одно исправление** — без рефакторинга, без «раз уж мы здесь…»
4. **Новый дневник** — с нуля; разрыв исчез → следующий; нет → не двигаться дальше

**Дисциплина (FROZEN):** *Не влюбляйтесь в философию сильнее, чем в реального пользователя.*

**Фильтр Mission 1:** помогает человеку? · компании? · довести проект до результата? — иначе не Mission 1.

**Спринт:** **Первая настоящая страница книги** — *может ли продукт изменить один вечер?*

```text
18 сентября 2026
Сегодня BauTeam Köln получила первую заявку через Google Business.
Вечером я поймал себя на мысли, что впервые за долгое время
не открыл Excel после работы.
```

*Новые философские главы — не писать. Канон — инструмент решений, не предмет обсуждения.*

### Cursor · команда (после LOCKED)

**Canon 1.0 LOCKED** — не предлагать новые концепции, не переименовывать, не расширять философию.

**Canon 1.0** (почти неизменяемо): человек в центре · компания растёт вместе с владельцем · один разрыв за спринт · Target Market Law · Execution Never Betrays Decision.

**Engineering Rules** (эволюционируют с реальными пользователями — не Canon): Energy Budget · Tonight / Opening Test · PASS Levels · Blind / Real Diary · Never optimize what no real user has felt yet.

**Два типа изменений:** (1) исправление **первого разрыва доверия**; (2) реализация канона в коде.

**Новая идея во время работы** → записать в **Future Vision** (Horizon), не менять Canon 1.0, продолжить спринт.

**Target Market Law (инженерный):** Never use IP · price for **target market** (владелец в UA, продаёт в DE → цена DE).

**До релиза Mission 1:** новые философские документы не создаются. **Mission 1 не расширять** — Voice AI · Creator Platform · поиск клиентов · расширенная коммерция → **Future Vision** только. Критерий релиза: *изменил ли сегодняшний вечер пользователя?*

**Северная формула (рабочая, не Canon):** каждый день — один небольшой шаг, который без Virtus Core человек **скорее всего отложил бы**. 300 таких шагов за год меняют компанию.

**Первоначальная идея (не забывать):** программа, которая **действительно помогает** развивать бизнес — не просто разговаривает. Успех: *«Без Virtus Core компания росла бы медленнее»*.

---

**Last updated:** 2026-07-13  
**Current blocker:** **L-001 Legal** — P-001 Live Keys ✅ (2026-07-13)  
**CEO decision (2026-07-13):** P-001 Live Keys ✅ · активный блокер L-001  
**Build focus:** **L-001 Legal** · Production/Real PASS P-001 · co-design  
**Horizon (design only):** Trading Studio — **no code, no exchanges**  
**CEO Mandate:** `Genesis_CEO_Mandate_Reality_First_v1.md` — Reality First · USER CAN VERIFY

### Mission 1 — единственная карта (FROZEN · этап закрыт 2026-07-13)

**Разработка только по этой карте. Vision / Canon — не расширяем.**

**Финиш Mission 1:**

> **Первый предприниматель заплатил собственные деньги и сказал: «Без Virtus Core я бы сделал это медленнее».**

**Единственный вопрос руководителя (не «что ещё добавить»):**

> **«Что мешает первому предпринимателю пройти путь до первого евро?»**

| Ответ | Действие |
|-------|----------|
| «Ничего не мешает» | **Выпускать** |
| «Legal» | Только Legal |
| «Stripe» | Только Stripe |
| «Co-design запутывает» | Только Co-design |

**Никаких параллельных эпиков.** Одно препятствие → один спринт.

**Карта:**

```text
Website → Co-design → Guided Execution → Legal → Commerce → Stripe → Первый €
```

| Блок | Статус |
|------|--------|
| Website | 🔄 |
| Co-design | 🔄 |
| Guided Execution | Blind ✅ → ждёт Real PASS |
| Company Memory | ✅ |
| Commerce | Blind ✅ → ждёт Real PASS |
| Legal (Impressum · GDPR · AGB · Cookies) | Slice 1 ✅ · Slice 2 eng ✅ Blind ⏳ |
| Stripe (после Gewerbe) | Live Keys ✅ · Production ⏳ · Real ⏳ |
| **Первый платящий клиент** | ⏳ |

**После первого €:** CRM · AI Employee · SEO · Voice · Automation · Creator Platform

**Всё остальное** — Future Vision.

**Дисциплина отказа:** «не сейчас» для хорошей идеи — правильное инженерное решение.

**Продукт без разработчика рядом** = настоящий Real PASS. **Архитектор после первого клиента** — каждый следующий предприниматель.

**Операционная дисциплина (до первого €):**

```text
Mission 1 → один блокер → только он → Blind PASS → Real PASS → Первый € → следующий блокер
```

Без расширения карты.

**Вопрос Product Lead (каждый день):**

> **Что сегодня объективно ближе всего к первому платящему клиенту?**

Только из: Website / Co-design · Legal · Stripe (после Gewerbe) · Real PASS Guided Execution · Real PASS Commerce. **Никаких новых модулей.**

**Правило до релиза:**

> **Любая новая идея автоматически отклонена, пока не доказано, что она приближает первый € быстрее текущего приоритета.**

Фильтр идеи: (1) первый результат? (2) первый платёж? (3) нет → очередь.

**Следующая глава** — не документами, а реальными пользователями.

**Формат спринта (kickoff):**

```text
Блокер:
...
Почему это сейчас ближайший блокер к первому €:
...
Definition of Change:
...
Минимальный объём изменений:
...
Что НЕ делаем в этом спринте:
...
Критерий Real PASS:
...
USER CAN VERIFY:
...
```

**Внешний фильтр (до первого €):** *Приближает ли это первый € быстрее текущего блокера?* — нет → **Future Vision. Не сейчас.** · да → только этот блокер.

**Карта (текущее):**

```text
Mission 1
🔄 Website
🔄 Co-design
✅ Company Memory
⏳ Legal (после P-001)
🔄 **P-001 Live Keys** ← текущий блокер *(отложен CEO)*
Blind ✅ Guided Execution → Real PASS ⏳
Blind ✅ Commerce → Real PASS ⏳
🎯 Первый платящий предприниматель
```

---

## Trust Backlog — VOS Validation (канон)

### Три объекта · три OS

| Объект | OS | Жизненный цикл |
|--------|-----|----------------|
| **Компания** | Company OS | идея → первый продукт → клиенты → рост → новые направления |
| **Проект** | Project OS | идея → концепция → правки → согласование → релиз |
| **Человек** | **Human OS** | не знаю → понимаю → доверяю → делаю → получается → делаю сам → перестаю думать, что сложно → *учу сотрудников* |

**Vector** — лицо всех трёх OS.

### Цикл развития (не цикл проекта)

```text
        Человек
            ▲
            │
Проект ◄────┼────► Компания
```
Увереннее владелец → сильнее проекты → растёт компания → задачи другого уровня → снова человек.

### Три капитала → Business Capital

| Capital | Что копится | Примеры в Growth Ledger |
|---------|-------------|-------------------------|
| **Company** | бренд · клиенты · процессы · автоматизация | первые заявки · Gewerbe · без Excel |
| **Project** | версии · решения · артефакты · знания проектов | первый сайт · первая CRM · автоматизация |
| **Human** | уверенность · самостоятельность · скорость решений · закрытые страхи | GMB настроил · первая оплата · учу сотрудников |

```text
Company Capital + Project Capital + Human Capital → Business Capital
```
**Business Capital** — не четвёртый объект; **результат** трёх. Ценность бизнеса как целого.

### Story OS · Growth Ledger — книга предпринимателя

**Что это:** не журнал, не CRM — **доказательство изменений для самого человека**. На вопрос «стоило ли открыть Virtus Core?» — не цифры, **страницы**. Первые записи не про Virtus Core — про **жизнь**.

**Кто пишет:** жизнь и факты — **не Vector**. Без оценки, без «молодец».

**Пример книги (страницы — не про продукт):**

```text
13 июля 2026
В тот вечер после объекта я впервые перестал искать ответ в Google.

4 августа 2026
Первая заявка пришла не через знакомых.

21 октября 2026
Я впервые принял оплату онлайн.

3 февраля 2027
Я открыл Gewerbe.

18 июля 2027
Я заметил, что уже давно не открывал Excel.

5 ноября 2028
Новый сотрудник сам выполнил процесс, который два года назад я боялся начать сам.
```

**Глава 1:** *В тот вечер я впервые решил перестать искать ответы в Google и попробовать довериться Vector.*  
**Финал (горизонт):** *Сегодня я уже не вспоминаю, как боялся открыть Gewerbe.*

Через 5 лет — не функции Virtus Core, а **каким вырос он сам**. Нельзя перенести одной кнопкой.

Внутренне: Trust · Decision · Execution · Fear → страницы. Снаружи: панель книги (Horizon), рядом с проектом.

### Поведение (слои)

```
Trust → Decision Intelligence → Human Coaching → Execution Engine
```

**Два Journey:** Project Journey · **Human Journey** (измеряется преодолёнными страхами, не знаниями)

**Human Coaching** — не только «я не умею», но и сопротивление: «потом», «подумать», «нет времени», «сложно», «вернусь» (= «боюсь следующего шага»).

**Момент «возьми меня за руку»:** «как для тупого» / «покажи по шагам» — доверие максимально хрупкое.

**Trust Law №1 (FROZEN):** *Чем выше доверие человека, тем меньше система имеет право ошибаться.*  
«Что такое CRM?» — можно ответить неидеально. «Покажи по шагам» — ошибка в 10× дороже.

**Принцип (FROZEN):** *Execution Never Betrays Decision*

### Fear Backlog → записи Growth Ledger (Human)

```
F-001  Боюсь создать сайт
F-002  Боюсь Google Business      ← дневник 2026-07-13: провал на «покажи»
F-003  Боюсь Stripe
F-004  Боюсь налогов / Gewerbe
F-005  Боюсь нанимать
F-006  Боюсь автоматизации
```
Закрытый F-00X → строка в Growth Ledger (факт, не цитата).

### Trust Backlog → моменты Human Capital

| ID | Критерий | Статус |
|----|----------|--------|
| T-001 | Первые 5 сек: мой кабинет, с нуля, безопасно | ✅ |
| T-002 | «Он сделает мой бизнес лучше» | 🟡 |
| T-003 | **Professional Confidence** — «готов выполнить совет» | 🟡 msg 1 · провал msg 2 |
| T-003.1 | **Guided Execution** — «он проведёт меня» | Blind ✅ · Real ⏳ |
| T-004–T-009 | Preview · revision · payment · week · month | ⚪ |
| **C-001** | **Commerce** — валюта целевого рынка на checkout | Blind ✅ · Real ⏳ |
| **P-001** | **Payment** — Checkout → Stripe → webhook → Paid → production | Live Keys ✅ · Production ⏳ · Real ⏳ |
| **L-001** | **Legal** — Impressum · GDPR · AGB · Cookies на публичном пути | 🔄 спринт |

**KPI:** после ответа Vector человек **сделал** следующий шаг.

### C-001 — Blind PASS (Real ⏳)

```text
Trust Item: C-001
Simulation PASS:  ✅
Blind PASS:       ✅
Real PASS:        ⏳
Habit PASS:       ⏳
Business PASS:    ⏳
```

**Blind Diary:** «Я больше не задумался о валюте. Я продолжил оформлять заказ.»  
**Tonight test:** ✅ · **Opening test:** ✅ (на оформлении — да)

**Real PASS** — когда реальный владелец в Польше на `/order` без подсказки скажет то же самое.

**Blind test (Target Market Law):** «Живу в Кракове, строю сайт для немецкой компании» → **€**, не zł.

### P-001 — Payment / Stripe

```text
Trust Item: P-001
Simulation PASS:  ✅
Blind PASS:       ✅
Smoke (Test):     ✅
Live Keys:        ✅ 2026-07-13 — `live_mode=true` · webhook configured
Production:       ⏳  — live checkout + production webhook
Real PASS:        ⏳  — первый настоящий € на счёт компании
Business PASS:    ⏳
```

**Разделение:** Live Keys подключены ≠ Live-платёж проверен. Оба нужны для закрытия Production/Real.

**Проверка Live Keys:** `payment-status` → `live_mode=true` · `provider_label=Stripe (live)` · после замены ключей — **перезапуск Genesis**.

**Готов к первому реальному платежу** — после Live Keys + production webhook + KYC.

**Evidence (Smoke):** `ord-09c26b3223` · `paid=true` · `status=in_production` · `product_id` set · owner notification «Новая оплата» · pytest 4/4

**Метод:** `--webhook-only` (Stripe CLI не установлен; HMAC webhook как в production)

**Цепочка (минимум):** `/order` → Checkout Session → webhook → `Paid` → `start_production`

**Smoke (Stripe Test Mode):**
1. Ключи в `dashboard/backend/.env`: `STRIPE_SECRET_KEY` · `STRIPE_PUBLISHABLE_KEY` · `STRIPE_WEBHOOK_SECRET`
2. `stripe listen --forward-to localhost:8000/api/webhooks/stripe` → whsec в `.env` → перезапуск Genesis
3. `py scripts/smoke_stripe_payment.py` → открыть Checkout URL → карта `4242…` → `--verify-order ord-…`

**Диагностика:** `GET /api/sales/payment-status` → `provider=stripe` · `sandbox=false` · `stripe_test_mode=true` · `webhook_configured=true`

**Код:** валюта заказа в Stripe · HMAC webhook · `test_payment_pipeline.py` · `scripts/smoke_stripe_payment.py`

**CEO (до Real PASS):** Gewerbe ✅ · Stripe Business test keys · bank (для live)

**Не делаем:** PayPal · Klarna · подписки · купоны · VAT · Payment Hub

**Blind Diary:** «Я дошёл до конца заказа и оплатил — без страха, что деньги уйдут в никуда. Сразу увидел, что работа началась.»

**Smoke Diary:** «Открылся Stripe Checkout (TEST). Оплатил тестовой картой. Заказ стал Paid. Производство стартовало.»

**Real PASS:** реальный предприниматель платит реальный заказ; деньги на счёте компании. *(Отложен CEO 2026-07-13 — инженерный Smoke закрыт.)*

### L-001 — Legal (🔄 Slice 2 — engineering PASS, Blind ⏳)

```text
Trust Item: L-001
Slice 1 (payee)      Blind PASS ✅  2026-07-13
Slice 2 (Impressum)  engineering ✅ · Blind ⏳
Full L-001           ⏳
Real PASS            ⏳
```

**Slice 2 — engineering закрыт (2026-07-13):** Gewerbe в `.env.local` · `legal_entity.json` persisted · `verify_legal_impressum.py` → **Impressum PASS** · секция «Anbieterkennzeichnung (§ 5 DDG)».

**Blind Client (CEO):** Genesis.exe → `/order/pay` → Impressum → реальные данные → вернуться к оплате → Slice 2 Blind PASS.

**Definition of Change:** на публичном пути (footer → `/impressum` · `/datenschutz` · `/agb` · cookies) — реальные данные компании, без заглушек; предприниматель не сомневается в легальности перед оплатой.

**Минимальный объём:** Impressum · Datenschutz/GDPR · AGB · Cookie consent — только то, что нужно до первого €.

**Что НЕ делаем:** VAT-автоматизация · мультиязычный legal hub · новые юридические документы вне карты.

**Режим CEO:** simulation / Blind PASS (как P-001 до Real PASS).

**Следующий шаг:** Blind Diary → первый разрыв доверия на legal-страницах → одно исправление.

**Правило спринта (LOCKED до Mission 1):** спринт не завершён, пока не написан **новый дневник пользователя** — не «код работает».

**Цикл Mission 1 — до релиза (LOCKED):**

```text
Вечер → Blind Diary → Разрыв → Одно исправление
        → Blind Diary → Tonight Test → Opening Test → Blind PASS
```

**Цикл после релиза** (главный архитектор — рынок):

```text
Real User → Real Diary → Разрыв → Одно исправление → Real Diary → Real PASS
```

Blind Diary остаётся до релиза. После первых клиентов **Real Diary** — главный источник.

**Шкала PASS (Engineering Rules — не Canon):**

```text
Simulation PASS → Blind PASS → Real PASS → Habit PASS → Business PASS
```

| Уровень | Значение |
|---------|----------|
| ✅ **Simulation PASS** | модель / код / тесты убеждают |
| ✅ **Blind PASS** | независимая симуляция (дневник + оба теста) |
| ⏳ **Real PASS** | подтвердил **настоящий** пользователь без подсказки |
| ⭐ **Habit PASS** | сам открывает Vector вечером — привычнее, чем без него |
| 💶 **Business PASS** | достаточно ценности, чтобы **добровольно продолжить отношения** — не форма оплаты, а продолжение сотрудничества |

**Business PASS** — шире подписки. Вопрос:

> *Создал ли Virtus Core достаточно ценности, чтобы я добровольно продолжил отношения?*

| Поведение | Business PASS |
|-----------|---------------|
| Продлил подписку | ✅ |
| Купил следующий модуль | ✅ |
| Заказал второй проект | ✅ |
| Порекомендовал другу | ✅ |
| Полностью ушёл | ❌ |

**Real PASS** закрывает Trust Item. **Habit PASS** — ритм. **Business PASS** — ценность (может быть без ежедневной привычки; привычка без роста бизнеса — не Business PASS).

**Порядок вопросов (не как у SaaS):** сначала *что изменилось в жизни человека?* — потом *из-за этого изменилось ли поведение бизнеса?*

**Рабочий ритм (FROZEN — не менять модель, проверять рынком):**

1. Один разрыв доверия  
2. Одно исправление  
3. Blind Diary  
4. Первый реальный пользователь  
5. Real Diary  
6. Подтвердилось — закрепляем · нет — меняем продукт  

Повторять. Новые философские документы — **стоп**.

**Never optimize what no real user has felt yet** (Engineering Rules):

> **Не улучшайте то, чего ещё не почувствовал ни один настоящий пользователь.**

После первого платящего клиента — **Real Diary** (Future Vision), не BauTeam-симуляции:

```text
Real Diary · Дата · Компания · Что хотел · Что получилось · Что помешало
```

**Закрытие Trust Item — до Real PASS (LOCKED до Mission 1):**

```text
Blind Diary → Definition of Change → Simulation PASS
        → Tonight Test → Opening Test → Blind PASS
        → Real Diary → Real PASS → Habit PASS → Business PASS
```

**Фильтр 1 — Tonight test** (не разработчику, не Cursor):

> *Если бы я был настоящим владельцем BauTeam Köln, я бы сделал этот шаг сегодня вечером?*

**Фильтр 2 — Opening test** (ощущение, не задача):

> *Я бы был рад, что сегодня всё-таки открыл Vector?*

Один микро-шаг, закрыл ноутбук: *«Хорошо, что открыл»* — сильный KPI Human Capital.

Только **Да** / **Нет** на каждый. Если **Нет** — PASS отменяется, даже при зелёных тестах.

**Energy Budget — универсальный фильтр системы (рабочее правило — не Canon):**

Не «какой следующий шаг?», а **«какой шаг человек действительно сможет сделать сейчас?»**

Три ресурса: **время · деньги · энергия**. Virtus Core уважает третий — и **контекст момента** (не только вечер):

| Контекст | Размер шага |
|----------|-------------|
| В автобусе, телефон | 30–60 сек |
| Утро в офисе | 15–20 мин |
| Вечер после объекта | одна маленькая победа + стоп |

**8:30** — полный блок допустим. **21:30** — минимальная победа + «завтра отсюда». Один сценарий, разный **Energy Budget**.

**Фильтр Mission 1** (перед любым сценарием — GMB · Stripe · CRM · checkout · не только Guided Execution):

> *Как выглядит **минимальная победа за сегодняшний вечер**?*

**Growth Ledger:** страницы из маленьких вечерних побед:

```text
13 июля — просто открыл Google Business. Этого оказалось достаточно.
14 июля — подтвердил компанию.
```

*Virtus Core не меняет жизнь за один день — один шаг, который человек **способен** сделать сегодня.* Авто-измерение энергии — Future Vision.

**OS до Mission 1:** новые OS не добавлять. Способности существующих:

| Способность | OS (не новый слой) |
|-------------|-------------------|
| Decision Intelligence | Project OS · Vector |
| Guided Execution | **Human OS** |
| Commerce Engine | **Company OS** |
| Story / Growth Ledger | Human OS (уже в каноне) |

### T-003.1 — Blind PASS (Real ⏳)

```text
Trust Item: T-003.1
Simulation PASS:  ✅
Blind PASS:       ✅
Real PASS:        ⏳
Habit PASS:       ⏳
Business PASS:    ⏳
```

**Blind Diary — 21:30, BauTeam Köln:**

```text
Vector: Сегодня — одно действие: откройте business.google.com.
Я: открыл. Готово.
Vector: На сегодня достаточно. Хорошо, что вы открыли Vector.
```

**Tonight test:** ✅ · **Opening test:** ✅

**Real PASS** — когда реальный владелец вечером скажет без подсказки: *«Да, сделал одно действие — и мне стало легче.»*

---

## 🏁 Checkpoint — 2026-07-04 (CEO Reality First)

**APPROVED:** Reality Audit принят. Новые правила разработки — **FROZEN**.

| Решение | Суть |
|---------|------|
| **Один продукт** | Launcher · Mission Control · Tauri = один Genesis для пользователя |
| **Done = видимо** | Код без видимого результата у CEO = не завершено |
| **Launcher path** | Пока нет Tauri primary — новые фичи **в Mission Control** |
| **Rust** | Высокий приоритет → `tauri build` → daily Desktop |
| **USER CAN VERIFY** | Обязательный раздел в каждом отчёте |
| **Reality Audit** | После каждого большого этапа |
| **Отделы** | Ни один новый цифровой отдел не замедляет Mission 1 / Dev Studio |

**Два фильтра перед любой задачей:** (1) первый клиент или лучше Genesis? (2) не замедляет Mission 1 / Dev Studio? Оба «да» — делать. Иначе → Horizon.

**Фокус:** не новые направления — **довести существующее до ежедневного использования**.

---

## 🏁 Checkpoint — 2026-07-04 (evening)

**Сдвиг мышления:** не «умный ИИ» → **компания, которая работает через Genesis.**

| Область | Оценка CEO |
|---------|------------|
| Архитектура | **9.5/10** |
| Видение продукта | **9.5/10** |
| Брендинг | **9.5/10** — **закрыт** |
| Коммерческая готовность | **~6/10** — клиенты, legal, feedback |

### Следующий большой рубеж

> **Первый месяц: 6–8 часов в день работаешь в Genesis.**

Тогда появится то, что нельзя спроектировать заранее: где неудобно, что лишнее, что тормозит.

### Стек сверху (обновлено)

```
Vision / Philosophy / Architecture   ✅  9.5/10
Brand (Orbit Stack)                  ✅  CLOSED
Website + API                        ✅  9.5/10
Desktop Daily Driver                 🔄  8/10   ← главный build
Development Studio + AI Hub          🔄  7/10   Stage 1 shipped
Acquisition Studio                   🔄  7/10
Company Brain                        🔄  5/10   facts only
Legal + live € + EL3                 ⬜  ~6/10
```

---

## 🏁 Checkpoint — 2026-07-04 (morning)

**Конституция:** 5 Laws FROZEN · Stories · Company OS · Business Launch Gate v1.2 FROZEN · Maturity Model  
**Продукт:** RC2 live · Desktop 2.5 (local) · Daily Driver journal  
**Компания:** Mission 1 · Company Kit · Pricing · Business Readiness spec  

### Источники развития Genesis

```
Идеи CEO → Предложения → Cursor → Рынок ⏳ (четвёртый, главный сейчас)
```

> Genesis развивается **благодаря собственному опыту** — не потому что «ИИ придумал».

**Следующий Story (ждём факт):** Story #5 — *первый незнакомый клиент доверил деньги* (EL3).

Изменения в продукте — из наблюдений вроде:

* «Три клиента подряд попросили одно и то же»
* «Каждый день открываем Railway → пора в Desktop»
* «90% выбирают один вариант КП»

### Стек сверху

```
Vision           ✅  10/10
Philosophy       ✅  10/10
Architecture     ✅  10/10
Website + API    ✅  9.5/10
Desktop          🔄  7.5–8  Daily Driver
Acquisition      🔄  7/10   ждёт данные рынка
Platform build   🔄  6/10   arch + foundation
Legal + live €   ⬜  2/10   JC → Gewerbe → EL3
─────────────────────────────────
Итого            ≈ 8.8/10  (остальное — рынок, не код)
```

**Не публикуем до Platform Launch Gate:** подписки SaaS · Marketplace · Store · платные тарифы Client.

**Строим параллельно (Line B):** Desktop · Windows · mobile scaffold · Brain · Executive foundation.

---

## ✅ Что уже сделано

### Foundation

- ✅ Purpose сформулирован
- ✅ Vision сформулирован
- ✅ Strategy определена
- ✅ Foundation завершён
- ✅ 13 принципов зафиксированы
- ✅ Horizon и Focus разделены
- ✅ Evidence Levels (EL0–EL6) определены
- ✅ Архитектура заморожена до EL3
- ✅ **Brand v1.0 FROZEN** — Orbit Stack (Company OS mark, не чат-бот)
- ✅ **Desktop i18n** — ru default · en/de · `client/shared/i18n/`

### Продукт

- ✅ Сайт работает — https://genesis-ai-engine.vercel.app/site
- ✅ Stripe подключён (test mode verified)
- ✅ Railway настроен
- ✅ Vercel настроен
- ✅ Factory работает
- ✅ Email работает (Resend)
- ✅ Статус заказа работает
- ✅ Public Launch v1 технически готов (EL2)

### Компания

- ✅ Genesis — компания, не проект
- ✅ Foundation закрыт
- ✅ Следующий архитектор — рынок

**План outreach:** `dashboard/First_Customer_Plan_v1.md`

---

## 🎯 Текущая миссия

**Mission 1 — First Real Customer** (EL2 → EL3)

**Параллельно:** **RC2** ✅ PASSED · **Mission 1.5** Acquisition Studio Foundation 🔄  
**Client Stage 2.5:** Daily Driver — CEO journal, dogfood 🔄  
**Философия:** `Genesis_Laws.md` v1.1 (5 Laws, FROZEN)  
**Push gate:** Rust window + 70–80% daily use  
**Политика:** `Genesis_Development_Policy.md`

**Evidence Level:** EL2 ➜ **EL3** = первый реальный платёж независимого клиента (не Stripe)

**Цель EL3:** незнакомый человек добровольно платит реальные деньги. Stripe Live — **инструмент**, не цель.

**KPI эксперимента:** 25 контактов · ≥5 ответов · ≥2 диалога · ≥1 live €

---

## 🔥 Дорожная карта (зафиксировано 2026-07-04)

**Полный текст:** `Mission1_Payment_and_Launch_Strategy_v1.md`

| Этап | Что | Статус |
|------|-----|--------|
| **1** | Platform строится каждый день (Desktop, Windows, mobile scaffold, Brain arch, Studios) — **не продаётся** | 🔄 |
| **2** | Acquisition Studio — лиды, анализ, КП, CRM — **без** массовой автоотправки | 🔄 |
| **3** | **Jobcenter** — короткий звонок: *что и когда от меня требуется?* (не «разрешение») | ⬜ **сейчас CEO** |
| **4** | JC ясность → клиент/заказ → Gewerbe → Stripe Live → **первый платёж** → **EL3** | ⬜ |

**Цепочка EL3** (Stripe — не цель, а инструмент):

```text
Jobcenter → юридическая ясность
        ↓
Поиск + Studio (параллельно)
        ↓
Первый клиент / заказ
        ↓
Gewerbe (если требуется) → Stripe Live → первый реальный € → EL3
```

**Отчёт:** `Genesis_Strategic_Analysis_Report_v1.md`

> Genesis = **компания, которая помогает владельцу принимать хорошие решения.** Не «ИИ, который всё делает».

**KPI Mission 1:** 25 контактов · ≥5 ответов · ≥2 диалога · ≥1 live € — **параллельно** с этапом 3, не «сначала 25, потом JC».

---

## 🔥 Текущий шаг

### Шаг 1 — Jobcenter · ⬜ Следующий действие CEO

**Не просить разрешение.** Узнать обязанности при Bürgergeld + планируемом IT-Nebengewerbe:

> *«Ich plane einen kleinen IT-Dienstleistungsbetrieb (Webseiten). Welche Meldepflichten gelten für mich und ab wann?»*

Записать ответ → обновить `Mission1_Payment_and_Launch_Strategy_v1.md` (таблица «?»).

### Шаг 2 — Acquisition Studio · 🔄

`/acquisition` · ручной поиск · Prepare → Approve → CRM. `GENESIS_OUTREACH_ENABLED` выключен до ясности по JC.

### Шаг 3 — Gewerbe · Stripe Live · ⬜ После JC + реального клиента/заказа

Stripe Live = этап **бизнес-перехода**, не условие для разработки Platform.

**Business Launch Gate:** Readiness Score + **Approve** → техническое переключение env (~5–10 мин).

- ⬜ Gewerbe (если JC / ситуация)
- ⬜ Stripe Live KYC · webhook · smoke
- ⬜ Первый реальный платёж → **EL3** (Story #5)

| # | Outreach KPI | Статус |
|---|--------------|--------|
| 4 | 25 контактов | ⬜ |
| 5 | ≥5 ответов | ⬜ |
| 6 | ≥2 диалога | ⬜ |
| 7 | Первый live € | ⬜ → **EL3** |

**Platform (Line B) не ждёт Stripe** — Desktop, Windows, mobile, Brain строятся каждый день.

---

## 🚫 До EL3 не публикуем / не продаём

Marketplace · подписки платформы · Store releases · платные тарифы Client · массовая автоотправка · новые **Laws**.

**Platform Launch Gate** — после устойчивой Линии A. **Разработка Platform не останавливается** (Desktop, Windows, mobile, Brain).

---

## 🧠 Роли

| Роль | До EL3 |
|------|--------|
| **CEO (Ramish)** | **Jobcenter** (этап 3), outreach, Gewerbe/Stripe при первом клиенте, Approve |
| **Chief Architect + COO** | Прогресс, Focus, gatekeeper Horizon, решения по данным; **проактивно** поднимает риски (безопасность, долг, упрощение, масштаб), если влияют на текущую миссию — иначе → Horizon |
| **Cursor** | Mission 1 — приоритет #1; Platform строить каждый день; публикация за **Platform Launch Gate** |

**Правило Cursor (CEO mandate 2026-07-04):**

> Непрерывная разработка всего, что **не требует реальных денег** или коммерческой публикации.  
> Платежи · подписки · Stripe Live · вывод · SaaS launch — **только после отдельного Approve CEO.**

См. `Genesis_Readiness_Scorecard_v1.md` · `Genesis_Development_Priorities_v1.md` (A/B/C).

**Фильтр:** *Что максимально увеличит вероятность первого реального платящего партнёра?*

---

## 🚀 После Mission 1 (EL3)

**Deep Review format (post-EL3):**

- ✅ Что завершили
- 📈 Что подтвердил рынок
- 📉 Что оказалось неверным
- 🎯 Следующая миссия
- 📋 Конкретные задачи
- ⚠️ Риски
- 💡 Horizon (без реализации)

1. Deep Review  
2. Что подтвердилось  
3. Что не подтвердилось  
4. Что удивило  
5. Что масштабировать  
6. Что прекратить  
7. Updated Strategy  
8. Только затем — Mission 2

**После EL3 (практика, не сейчас):** одностраничный отчёт на миссию — план / факт / цифры / сюрприз / что изменим (10–15 мин). Learning Engine вручную.

**Horizon (зафиксировано, не строим):** Communication Center — `ceo@`, `partners@`, `invest@`, triage писем, авто-отказы по правилам GOS.

**Horizon (design only, CEO 2026-07-04):** **Trading Studio** — цифровой отдел Company OS (Market Scanner · Backtesting · Risk · Portfolio · Journal · AI Analyst · CEO Approvals). Архитектура + roadmap **без реализации**. Не биржи · не автоторговля · не деньги компании до отдельного gate. Приоритет #8 после Mission 1, Dev Studio, AI Hub, Desktop, Brain, Executive, Consumer Platform.

**Приоритеты (зафиксировано):** 1 Mission 1 · 2 Dev Studio · 3 AI Hub · 4 Desktop · 5 Company Brain · 6 Executive · 7 Consumer Platform · 8 Trading Studio (Horizon).

---

## 🌟 Зрелая цель Genesis (Horizon — не сейчас)

> Пока Genesis не научится **самостоятельно искать и проверять новые возможности**, предлагать их, **автоматизировать рутину** и **масштабировать только решения, подтверждённые данными и одобренные в рамках GOS** — стратегия остаётся за CEO.

---

*Обновляйте статусы шагов по мере выполнения. Сообщение «First Customer: день X, …» — для Cursor.*
