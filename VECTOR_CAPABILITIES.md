# Vector — живой паспорт способностей

**Среда выполнения работы** — не чат. Артефакты + **Capability Graph**.

## Правила

1. Одна способность = законченная ценность  
2. Пирамида ценности  
3. Один merge — одна способность *(Reuse Merge — wiring)*  
4. Capability must compose  
5. **Rule №5 — Capability Graph** — каждая capability **объявляет** Produces / Consumes (код: `capability_graph.py`)  
6. Product Truth — только `/site`  
7. Human Gate  
8. Rule №4 — Reuse из workspace  

## KPI

| KPI | Вопрос |
|-----|--------|
| Hours Saved | Сколько часов снято? |
| Reuse Score | Сколько capability переиспользовано? |
| Workflow Completion | Цепочка без ручного копирования? |

**Workflow #1 = 1** только после **обоих** Human Gate (анализ + reuse сайт).

---

## Порядок (Commit 4 — стоп)

1. 🔄 **Human Gate 3** — PDF реальный, не шаблон  
2. 🔄 **Human Gate Reuse** — «Создай сайт» без повторного описания бизнеса  
3. ✅ Workflow Completion = 1  
4. ⬜ Commit 4  

---

## Capability Graph (Rule №5)

Канонический источник: `dashboard/backend/app/execution/capability_graph.py`  
Owner API: `GET /api/owner/execution/capabilities` → `capability_graph`

### analyze_business_document ✅

| | Артефакты |
|---|-----------|
| **Consumes** | uploaded PDF/документ, user.goal |
| **Produces** | `document_structure.json`, `executive_summary.md`, `report.md`, `uploads/*`, `artifacts/doc-*.json` |

*Рынок/риски сейчас внутри `document_structure.json`; отдельные `market_profile.json` / `risk_profile.json` — horizon.*

### generate_site ✅

| | Артефакты |
|---|-----------|
| **Consumes** | user.goal, `document_structure.json` *(opt)*, `executive_summary.md` *(opt)*, `brand_profile.json` *(opt, planned)* |
| **Produces** | `brief.md`, `index.html`, `style.css`, `assets/`, `preview/`, **`site_manifest.json`**, `artifacts/site-*.json` |

**Reuse Score при wiring:** 2

### generate_proposal ⬜ planned

**Consumes:** `report.md`, `executive_summary.md`, `site_manifest.json`  
**Produces:** `proposal.md`, `proposal.pdf`

### generate_presentation ⬜ planned

**Consumes:** `report.md`, `site_manifest.json`  
**Produces:** `presentation.md`

---

## Визуализация (целевая)

```text
📄 business_plan.pdf
        │
        ▼
📊 report.md + document_structure.json
        │
        ├──────────────┐
        ▼              ▼
🌐 website         📈 presentation (planned)
        │              │
        └──────┬───────┘
               ▼
        💼 proposal.pdf (planned)
```

Planner (будущий) строит цепочку по графу, не по промптам:

```text
Нет report.md → Analyze → есть report.md → Generate Site → site_manifest → Proposal
```

---

## Human Gate checklists

### Gate 3
- [ ] PDF на `/site` → анализ основан на **вашем** файле  
- [ ] `report.md` + `executive_summary.md` открываются  

### Reuse Gate
- [ ] После анализа: только «Создай сайт»  
- [ ] Сайт = данные из анализа, Reuse Score ≥ 1  
- [ ] `brief.md` → секция Reuse  

---

## Статус кирпичей

| Кирпич | Gate | Graph node |
|--------|------|------------|
| Документы | ✅ | filesystem_write |
| Сайты | ✅ | generate_site |
| Анализ | 🔄 Gate 3 | analyze_business_document |
| Reuse wiring | 🔄 Gate Reuse | generate_site consumes analyze |
| Dev projects | ⬜ | dev_project (planned) |

---

*Обновлено: 2026-07-10 — Rule №5 Capability Graph. Commit 4 заблокирован до Workflow Completion = 1.*
