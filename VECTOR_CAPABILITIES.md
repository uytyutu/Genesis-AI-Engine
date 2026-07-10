# Vector — RC1 (Release Candidate 1)

**Разработка на паузе.** Главная задача — подтвердить, что способности работают для обычного пользователя на `/site`.

Ценность = **завершённые workflow**, не архитектура и не «умный чат».

---

## RC1 — пять Gate (пользовательский опыт)

| Gate | Сценарий | PASS критерий | Статус |
|------|----------|---------------|--------|
| **1 — Documents** | `Создай README` | Настоящий файл в workspace | ✅ PASS |
| **2 — Sites** | `Создай сайт стоматологии` | Workspace + файлы + Preview | ✅ PASS |
| **3 — Analysis** | PDF бизнес-плана → анализ | Executive Summary + Report + `document_structure.json`; выводы из **вашего** документа | 🔄 ждёт CEO |
| **4 — Reuse** | После анализа: только `Создай сайт` | Использует артефакты анализа; Explain Reuse (что взято, что не спрашивал) | 🔄 ждёт CEO |
| **5 — Zero Context** | Закрыть браузер → снова `Создай сайт` | Тот же workspace, reuse без повторных вопросов (Rule №6) | 🔄 ждёт CEO |

### RC1 complete = Workflow Completion = 1

> Все пять Gate пройдены CEO на [beta `/site`](https://beta.genesis-ai-engine.com/site) без терминала и Owner API.

**До WC=1:** ни Commit 4, ни новых capability, ни архитектуры.

---

## Процесс разработки (после RC1)

```
Идея → Capability → Human Gate → Workflow → READY → следующая capability
```

**READY** — обязательный этап между кодом и новой функциональностью.

---

## Правила (компакт)

1. Одна способность = законченная ценность  
2. Пирамида ценности  
3. Capability Graph (Produces / Consumes)  
4. Reuse — артефакты workspace  
5. **Explain Reuse** — показать что использовано  
6. **Zero Context** — переживает закрытие браузера  
7. **Trust Before Automation** — подтверждение перед изменениями *(Commit 4+)*  
8. Product Truth — только `/site`  

## KPI

| KPI | Вопрос |
|-----|--------|
| Hours Saved | Сколько часов снято? |
| Reuse Score | Сколько capability переиспользовано? |
| **Workflow Completion** | Сколько цепочек end-to-end без копирования? |

---

## Истории для пользователя (не архитектура)

Пользователю не нужны «Executive Brain», «Planner», «Capability Graph».

Ему нужны истории:

1. **«Загрузил бизнес-план → получил анализ → создал сайт.»** ← RC1 Gate 3–5  
2. «Открыл проект → Vector нашёл ошибку → diff → подтвердил → исправление.» ← после Commit 4  
3. «Попросил презентацию → получил файл.» ← horizon  

---

## Capability Graph (внутренний, для команды)

`dashboard/backend/app/execution/capability_graph.py`  
Owner: `GET /api/owner/execution/capabilities` → `capability_graph`

```text
📄 PDF → 📊 report.md + document_structure.json → 🌐 site
```

---

## Способности RC1

| Capability | Commit | Gate | READY |
|------------|--------|------|-------|
| Создавать документы | 1 | Gate 1 | ✅ |
| Создавать сайты | 2 | Gate 2 | ✅ |
| Анализировать бизнес-документы | 3 | Gate 3 | 🔄 |
| Reuse (site ← analysis) | merge | Gate 4–5 | 🔄 |

---

## CEO checklist — RC1 verification

### Gate 3
- [ ] Открыть beta `/site`  
- [ ] Загрузить **реальный** PDF бизнес-плана  
- [ ] «Проанализируй мой бизнес-план»  
- [ ] Открыть **Отчёт** и **Executive Summary**  
- [ ] Убедиться: формулировки из **вашего** файла, не шаблон  

### Gate 4
- [ ] В том же чате/workspace: только «Создай сайт»  
- [ ] Сайт отражает данные анализа  
- [ ] В ответе: Explain Reuse (файлы + «не спрашивал услуги/аудиторию/рынок»)  

### Gate 5
- [ ] Закрыть браузер полностью  
- [ ] Снова открыть beta `/site`  
- [ ] Только «Создай сайт»  
- [ ] Reuse снова работает, вопросов о бизнесе нет  

### После всех PASS
- [ ] Зафиксировать: **Workflow Completion = 1**  
- [ ] Обновить статусы Gate 3–5 → ✅ в этом файле  
- [ ] Тогда — обсуждение Commit 4  

---

*RC1 объявлен: 2026-07-10. Разработка: стоп до WC=1.*
