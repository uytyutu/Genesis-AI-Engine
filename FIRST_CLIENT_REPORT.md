# FIRST_CLIENT_REPORT.md

> **First Impression Generation** · Commercial Reality · 2026-08-07  
> Не «как красивее?» — **почему выбрать именно эту компанию?**  
> Не слоган — **история клиента за 10 секунд до клика.**

---

## Стоп-линия RC1

Пока пять Premium не пройдут одновременно:

1. «Я бы купил?»  
2. German Company Test  
3. Portfolio Test  
4. Factory ≥ Virtus Core  
5. **3-SECOND TEST** (без чтения текста)  

→ **не** Stripe / Auth / Workspace / Video / Marketing Studio.

---

## Порядок Factory

```text
Проблема клиента (10 сек до сайта)
  → История
  → Эмоция
  → Доверие
  → Предложение
  → CTA
```

Внутренний этап больше не называется Hero Generation.  
Он называется:

> **First Impression Generation**

Композиция + фото/видео + типографика + свет + воздух + заголовок + движение + кнопка + атмосфера = **одно** впечатление.

---

## Клиентские истории (H1)

| Проект | История (не слоган) |
|--------|---------------------|
| DachKlar | Nach dem Winter ist das Dach voller Moos — und Sie fürchten, die Sanierung kostet Tausende. |
| Psychology | Manchmal reicht ein Gespräch, um wieder Boden unter den Füßen zu spüren. |
| Law | Wenn die Lage schwierig wird, zählt, dass jemand den Weg zur Lösung schon kennt. |
| Restaurant | Hier beginnt der Abend nicht mit der Speisekarte, sondern mit dem Gefühl, schon in Italien zu sein. |
| Beauty | Zeit, die nur Ihnen gehört. |

Идея бренда остаётся как вторичный акцент (`fi-idea`), не как главный H1.

Смотреть: `http://127.0.0.1:3001/package-previews/sites/premium/{dachreinigung|psychology|restaurant|law|beauty}/`

---

## 3-SECOND TEST (обязательный)

```text
Открыть сайт.
Запретить себе читать текст.
Через 3 секунды ответить:

1. Чем занимается компания?
2. Можно ли ей доверять?
3. Она выглядит дешёвой или дорогой?
4. Хочется ли посмотреть дальше?
5. Похожа ли она на шаблон?

Если хотя бы один ответ отрицательный или неопределённый —
REBUILD.
```

Статус по пяти: **PENDING_OWNER**

---

## Дуга First Impression (что должно читаться)

| Шаг | Смысл |
|-----|--------|
| problem | Что переживает клиент до клика |
| story | Сюжет в H1 |
| emotion | Чувство |
| trust | Почему можно верить |
| offer | Что получаешь |
| cta | Следующий шаг |

---

## KPI

| Тест | Статус |
|------|--------|
| «Я бы купил?» ×5 | PENDING_OWNER |
| German Company Test | PENDING_OWNER |
| Portfolio Test | NO до YES владельца |
| Factory ≥ Virtus Core | PENDING_OWNER |
| 3-SECOND TEST | PENDING_OWNER |

Virtus Core продаёт **ощущение настоящего бизнеса**, которому хочется доверить деньги — не HTML и не секции.

---

## Код

- `dashboard/backend/app/factory/first_impression.py`  
- `dashboard/backend/app/factory/renderers/first_impression_dom.py`  
- `first_impression.json` в каждом Premium preview  
- [`RELEASE_BLOCKERS.md`](./RELEASE_BLOCKERS.md)
