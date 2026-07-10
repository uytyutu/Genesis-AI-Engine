# Vector — живой паспорт способностей

**Источник правды** для команды, тестировщиков и CEO.

## Правила развития

1. **Одна способность = законченная ценность**
2. **Пирамида ценности** — roadmap по уровням полезности
3. **Один merge — одна способность**
4. **Capability must compose** — стандартный `CapabilityResult` + артефакты как строительные блоки для следующих capability
5. **Product Truth** — проверка только через `/site`
6. **Human Gate** — Commit N+1 не начинать, пока Commit N не проверен человеком на beta

## KPI

> **Сколько часов реальной работы Virtus Core заменяет?**

| Commit | Способность | Экономия |
|--------|-------------|----------|
| 1 | Документы | ~5–15 мин |
| 2 | Сайты | ~30–120 мин |
| 3 | Анализ бизнес-документов | ~2–8 ч *(цель)* |
| 4 | Engineering | ~1–4 ч |

---

## Roadmap vNext

| Commit | Способность | Статус |
|--------|-------------|--------|
| 1 | Создавать документы | ✅ READY |
| 2 | Создавать сайты | ✅ READY |
| 3 | **Анализировать бизнес-документы** | 🔄 HUMAN GATE |
| 4 | Engineering (исправить ошибку) | ⬜ |
| 5 | Git | ⬜ |
| 6 | Browser | ⬜ |
| 7 | Docker | ⬜ |
| 8 | Workspace Intelligence | ⬜ |
| 9 | Multi-Step | ⬜ |
| 10 | Autonomous Jobs | ⬜ |

---

## ✅ Commit 3 — Documents Intelligence

**Способность:** Vector умеет **анализировать бизнес-документы** (не «PDF Analysis»).

**Фраза:** `Проанализируй мой бизнес-план` + PDF (или документ).

**Артефакты:**
- `executive_summary.md`
- `report.md` (SWOT, риски, рынок, финансы, рекомендации, вопросы)
- `document_structure.json` — building block для CRM / Proposal / Multi-Step
- `uploads/` — копия исходника

**Чат:** краткий итог + кнопки **Открыть отчёт** / **Открыть Executive Summary**.

**Capability:** `analyze_business_document` → `CapabilityResult`

**Статус:** 🔄 HUMAN GATE (ждёт проверки CEO на beta)

### Human Gate checklist

- [ ] Загрузить PDF на `/site`
- [ ] Написать «Проанализируй мой бизнес-план»
- [ ] Открыть оба отчёта
- [ ] Убедиться, что анализ ссылается на содержимое **вашего** файла

---

## Примеры для тестировщиков

| Фраза | Статус |
|-------|--------|
| `Создай README` | ✅ READY |
| `Создай сайт стоматологии` | ✅ READY |
| `Проанализируй мой бизнес-план` + PDF | 🔄 HUMAN GATE |
| `Привет` | ✅ READY (диалог) |

---

## Composable output (`analyze_business_document`)

```json
{
  "workspace_id": "ws-…",
  "artifact_id": "doc-…",
  "files": ["uploads/plan.pdf", "executive_summary.md", "report.md", "document_structure.json"],
  "document_type": "business_plan",
  "preview_url": "/api/public/execution/workspace/{id}/files/report.md",
  "status": "completed"
}
```

`document_structure.json` → Proposal Generator, Presentation, Multi-Step без переписывания анализа.

---

*Обновлено: 2026-07-10 — Commit 3 в ветке, Human Gate pending.*
