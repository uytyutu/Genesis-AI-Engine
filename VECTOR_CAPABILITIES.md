# Vector — живой паспорт способностей

**Среда выполнения работы** — не чат. Производство артефактов + композиция capability.

## Правила

1. Одна способность = законченная ценность  
2. Пирамида ценности  
3. Один merge — одна способность *(Reuse Merge — исключение: wiring без новой capability)*  
4. Capability must compose  
5. Product Truth — только `/site`  
6. Human Gate  
7. **Rule №4 — Reuse** — использовать артефакты предыдущих capability из workspace  

## KPI (три показателя)

| KPI | Вопрос |
|-----|--------|
| **Hours Saved** | Сколько часов работы снято? |
| **Reuse Score** | Сколько capability переиспользовано? |
| **Workflow Completion** | Прошёл ли пользователь цепочку без ручного копирования? |

### Workflow Completion (целевая цепочка №1)

```
Бизнес-план → Анализ → Сайт → (позже: Презентация → КП)
```

| Шаг | Capability | Статус |
|-----|------------|--------|
| 1. PDF + анализ | Commit 3 | 🔄 Human Gate |
| 2. «Создай сайт» с reuse | Reuse Merge | 🔄 Human Gate Reuse |
| 3. Презентация | Commit 9+ | ⬜ |

**Workflow #1 complete** = шаги 1–2 без копирования данных между чатами.

---

## Порядок сейчас (не Commit 4)

1. **Human Gate Commit 3** — PDF на beta  
2. **Reuse Merge** — `generate_site` ← `document_structure.json` *(код в ветке)*  
3. **Human Gate Reuse** — план → анализ → «Создай сайт»  
4. **Commit 4** — только после связанного фундамента  

---

## Четыре кирпича

| Кирпич | Статус | Reuse |
|--------|--------|-------|
| Документы | ✅ READY | 0 |
| Сайты | ✅ READY | 0 → **1** после Reuse Merge |
| Анализ документов | 🔄 Human Gate | 0 |
| Dev projects | ⬜ после Gate Reuse | цель 2 |

---

## Reuse Merge (не новая capability)

**Сценарий:**
```
PDF → analyze_business_document → document_structure.json
→ «Создай сайт» → generate_site читает артефакты → сайт
```

**Источники:** `document_structure.json`, `executive_summary.md` (если есть).

**Ответ чата:** `Reuse Score: N` — данные не переспрашивались.

**Статус:** 🔄 Human Gate Reuse pending

### Human Gate Reuse checklist

- [ ] Загрузить бизнес-план → анализ  
- [ ] «Создай сайт» (без повторного описания бизнеса)  
- [ ] Сайт отражает данные из анализа (название, услуги, позиционирование)  
- [ ] `brief.md` содержит секцию Reuse  

---

## Reuse Score (актуально)

| Capability | Reuse |
|------------|-------|
| analyze_business_document | 0 |
| generate_site (без анализа) | 0 |
| generate_site (после анализа в том же workspace) | **1–2** |

---

*Обновлено: 2026-07-10 — Reuse Merge + Workflow Completion KPI.*
