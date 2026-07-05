# Genesis Hybrid AI Strategy v1

**Date:** 2026-07-04  
**Decision:** **Вариант 3 — Гибрид** (CEO approved direction)

---

## Principle

Genesis is **not** “a ChatGPT app” and **not** “a Cursor clone”.

Genesis owns:

- Company Brain · memory · Executive logic  
- Plan → Approve → Act · Laws  
- Factory · Sales Studio · routing  
- **Genesis Development Engine** (planner, reviewer, tester, memory)  
- **Genesis Intelligence** (grows on *your* projects and data)

External LLMs and tools are **replaceable engines**.

---

## Architecture

```text
Genesis OS
    │
    ├── Genesis Intelligence (own — rules → memory → specialized models)
    │
    ├── AI Hub Router (capability-based)
    │
    ├── LLM Providers (swappable)
    │     ├── Provider A (e.g. OpenAI-class)
    │     ├── Provider B (e.g. Anthropic-class)
    │     └── Provider C (e.g. Google-class)
    │
    └── Development Providers (swappable)
          ├── Cursor (today)
          ├── Claude Code / Codex / … (tomorrow)
          └── Genesis Dev Model (horizon)
```

**UI never depends on vendor names** — only capabilities.

---

## If Cursor subscription ends

```
Cursor ❌ → switch Development Provider → Genesis continues
```

Do **not** embed Cursor as core — use `development` kind in `provider_registry.py`.

---

## Evolution timeline (target)

| Year | State |
|------|--------|
| 2026 | Genesis uses external LLMs + Cursor as engines |
| 2027 | Genesis knows your projects better than generic AI |
| 2028 | Specialized Genesis models (Planner, Reviewer, Memory) |
| 2029+ | External models for edge cases only |

**Training data:** own code, docs, tests, decisions — **not** scraping commercial model outputs (ToS).

---

## Consumer vs CEO

| | Consumer | CEO |
|---|----------|-----|
| UI | Simple AI Hub | Full Genesis OS |
| Providers | Routed silently | Full Studio + approve |
| New features | **After** CEO dogfood | **First** |

---

## Commercial tiers

Free / Pro / Business — architecture in `Genesis_AI_Hub_Architecture_v1.md`.  
**Limits TBD** after cost + usage data. **No publish** before Platform Launch Gate.

---

*Hybrid strategy v1 · engines swap, Company OS stays*
