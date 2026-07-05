# Genesis Intelligence — Layered Architecture v1

**Date:** 2026-07-04  
**Status:** Direction frozen — **build in layers**, do **not** train a ChatGPT-class LLM  
**Language:** Genesis uses **AI Providers**, not vendor brand names in product UI

---

## Principle

Genesis is not «another ChatGPT».

Genesis owns **laws, process, memory, routing, and specialized intelligence**.

External models are **swappable engines**. Today: Provider A/B/C. Tomorrow: Genesis Planner. User should not notice the swap.

---

## Own intelligence layers (build order)

### 1. Genesis Planner
**Does not write code.**

| Capability | Source today | Own layer target |
|------------|--------------|------------------|
| Build plan from natural language | Rule-based + handoff | Project-aware planner |
| Break tasks into steps | AI Hub `create_task` | Persistent plan templates |
| Understand project context | Dev Workspace files/docs | Project Memory |

**Code:** `ai_hub/ai_hub_service.py` (Stage 1 rules) → Planner service (Stage 2)

---

### 2. Genesis Memory
**Stores what generic LLMs forget.**

| Stores | Location today | Target |
|--------|----------------|--------|
| Decisions · Stories | docs, milestones JSON | Project Memory panel |
| Tasks · handoffs | `ai_hub_tasks.json`, cursor tasks | Timeline |
| Architecture | PROJECT_STATE, North Star | Per-project brain |
| Errors · lessons | verify logs, journal | Memory index |

**Horizon:** `Genesis_Dev_Studio_Stage2_Panels_v1.md` § Project Memory

---

### 3. Genesis Reviewer
**Quality gate — not generation.**

| Today | Target |
|-------|--------|
| `cursor_handoff.verify_task` (pytest) | Reviewer scores + explain |
| System check | Release readiness % |

**Horizon:** AI Team role «Reviewer»

---

### 4. Genesis Routing Engine
**Picks provider + tool per task.**

| Input | Router decides |
|-------|----------------|
| Task type | capability: chat / code / document / image |
| Tier | free / pro / ceo |
| Cost · speed · quality | policy (TBD after usage data) |
| Development | Development Provider → Cursor \| alternate |

**Code:** `ai_hub/provider_registry.py` (scaffold) → Router (Stage 2)

---

## What we do NOT build now

- Custom LLM training at ChatGPT scale  
- «Genesis uses GPT» in UI — say **AI Providers**  
- Replacing providers before dogfood month (6–8 h/day in Genesis)

---

## Evolution path

```
2026  External AI Providers + Genesis rules/Memory scaffold
2027  Project Memory + Timeline from real CEO usage
2028  Genesis Planner / Reviewer as first-class local modules
2029+ External providers for edge cases only
```

Training data: **own code, docs, tests, decisions** — comply with provider ToS.

---

## Related

- `Genesis_Hybrid_AI_Strategy_v1.md`  
- `Genesis_AI_Hub_Architecture_v1.md`  
- `Genesis_One_Window_Roadmap_v1.md`

---

*Genesis Intelligence v1 · own layers, swappable engines*
