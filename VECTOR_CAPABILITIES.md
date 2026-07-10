# Vector — живой паспорт способностей

**Среда выполнения работы** — завершённые workflow, не качество ответа в чате.

## ⛔ Дисциплина сейчас

> **Ни одной новой capability и ни одной строки архитектуры**, пока не подтверждён **Workflow Completion = 1**.

1. 🔄 Human Gate 3  
2. 🔄 Human Gate Reuse (+ Rule №6 Zero Context)  
3. ✅ Workflow Completion = 1  
4. ⬜ Commit 4  

---

## Правила

| # | Правило |
|---|---------|
| 1 | Одна способность = законченная ценность |
| 2 | Пирамида ценности |
| 3 | Один merge — одна способность |
| 4 | Capability must compose |
| 5 | **Capability Graph** — Produces / Consumes (`capability_graph.py`) |
| 6 | **Zero Context Reuse** — артефакты workspace переживают закрытие браузера |
| 7 | **Explain Reuse** — показать *что* использовано, не только score |
| 8 | **Trust Before Automation** — план → предпросмотр → подтверждение → применение *(Commit 4+)* |
| — | Product Truth — только `/site` |
| — | Human Gate |

---

## KPI

| KPI | Вопрос |
|-----|--------|
| **Hours Saved** | Сколько часов работы снято? |
| **Reuse Score** | Сколько capability переиспользовано? |
| **Workflow Completion** | Цепочка без ручного копирования? |

**Workflow Completion = 1** = Gate 3 ✅ + Reuse Gate ✅ (включая Rule №6).

---

## Rule №6 — Zero Context Reuse (тест)

```
День 1: PDF → анализ → report.md → закрыл браузер
Через час: открыл снова → «Создай сайт»
```

**PASS если:**
- Тот же `visitor_id` (localStorage `genesis_visitor_id`) → тот же workspace  
- Vector: «Использую ранее проанализированный бизнес-план из этого Workspace»  
- **Не** спрашивает нишу / клиента / услуги заново  

**FAIL если:** снова нужен контекст из головы пользователя.

---

## Rule №7 — Explain Reuse (в чате)

Не только `Reuse Score: 2`, а:

```text
Использую ранее проанализированный бизнес-план из этого Workspace.

Использовано:
✓ document_structure.json
✓ executive_summary.md

Не потребовалось повторно описывать:
• услуги
• аудиторию
• рынок
```

---

## Rule №8 — Trust Before Automation (Commit 4)

```
План → Предпросмотр → Подтверждение → Применение
```

Пример: «Исправь ошибку» → diff + тесты → **Применить изменения?** → только потом правка.

---

## Human Gate checklists

### Gate 3
- [ ] PDF → анализ по **вашему** файлу, не шаблон  
- [ ] `report.md` + `executive_summary.md`  

### Reuse Gate (+ Rule №6)
- [ ] Анализ → «Создай сайт» → Reuse Score ≥ 1  
- [ ] Explain Reuse в ответе  
- [ ] Закрыть браузер → снова «Создай сайт» → тот же reuse без вопросов  

---

## Capability Graph

Канон: `dashboard/backend/app/execution/capability_graph.py`

```text
📄 PDF → 📊 report.md + document_structure.json → 🌐 site_manifest.json
                                              ↘ 📈 presentation (planned)
                                              ↘ 💼 proposal (planned)
```

---

## Статус кирпичей

| Кирпич | Статус |
|--------|--------|
| Документы | ✅ READY |
| Сайты | ✅ READY |
| Анализ | 🔄 Gate 3 |
| Reuse wiring | 🔄 Gate Reuse |
| Dev projects | ⬜ после WC=1 |

---

*Обновлено: 2026-07-10 — Rules 6–8; стоп до Workflow Completion = 1.*
