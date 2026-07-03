# Factory Framework Architecture v0.1

**Status:** DESIGN ONLY — no code until:
1. Owner completes `docs/OWNER_BROWSER_GATE.md`
2. Owner approves this document

**Date:** 2026-07-03  
**Kernel:** Frozen  
**Brain:** Dispatcher (unchanged by Factory)

---

## 1. Purpose

**Factory is not "Telegram bot generator" on day one.**

Factory Framework is a **sandbox assembly line** that:

1. Takes an approved **task** from Brain
2. **Builds** an internal product from templates
3. **Validates** structure and quality gates
4. **Packages** artifact for owner review
5. **Stops** — shows result to owner in Command Center
6. Does **not publish**, charge money, or use the internet in v0.1

> **Goal:** Create a product inside Sandbox → show owner → STOP.

Publish comes later, only after owner approves quality.

---

## 2. Sandbox Mode (mandatory)

Every Factory operation runs in one of two modes:

| Mode | Symbol | Behaviour |
|------|--------|-----------|
| **Sandbox** | 🟢 | Default. Build locally, no external APIs, no deploy, no payments |
| **Production** | 🔴 | Disabled in v0.1. Requires explicit owner unlock in future |

```python
# Future config (concept only)
class GenesisMode(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"  # locked until owner enables
```

**v0.1 rule:** `mode == SANDBOX` always. Publisher stub returns `"would publish"` never actually publishes.

Command Center will show mode badge: **🟢 Sandbox**

---

## 3. Position in the stack

```
Command Center
      ↓
Integration Layer
      ↓
Brain (queue, run tasks)
      ↓
Kernel (execute agent steps)
      ↓
Factory Framework          ← NEW (v0.1)
      ↓
Sandbox artifact folder    ← internal product output
      ↓
Owner review in UI         ← STOP (no Publish)
```

**Factory does not replace Brain.** Factory is invoked **as a Brain task pipeline** (multi-step Kernel job) or as a dedicated Factory service called from Integration Layer — see §8.

---

## 4. Framework components (not Telegram yet)

```
Factory Framework
│
├── Template Library      ← reusable product skeletons
├── Builder               ← assembles from template + params
├── Validator             ← quality gates (structure, tests, lint)
├── Packager              ← zip / folder ready for review
├── Publisher             ← STUB — logs "would publish", no action
└── SandboxGuard          ← enforces SANDBOX mode
```

### 4.1 Template Library

**Purpose:** Store versioned templates — Brain/Factory never writes from scratch.

```
factories/
└── templates/
    ├── manifest.json           ← index of all templates
    ├── micro-saas-v1/
    │   ├── template.json       ← metadata, required params
    │   ├── files/              ← skeleton files
    │   └── tests/              ← template self-tests
    └── telegram-bot-v1/        ← added AFTER framework proven
```

| Field (template.json) | Example |
|-----------------------|---------|
| `id` | `micro-saas-v1` |
| `name` | Micro SaaS landing |
| `version` | `1.0.0` |
| `params` | `product_name`, `tagline` |
| `sandbox_only` | `true` |

**v0.1:** One practical template (`landing-page-v1`) — simple company landing with contact form. Not Telegram.

**Why landing first:** easier to verify, show, and closer to what people pay for.

---

### 4.2 Builder

**Purpose:** Copy template + fill parameters → output directory in sandbox.

| Input | Output |
|-------|--------|
| `template_id`, `params`, `product_id` (UUID) | `sandbox/products/{product_id}/` |

**Builder rules:**
- Only writes under `sandbox/` directory
- Never calls network
- Emits `build.started`, `build.completed` events to AuditStorage
- Idempotent: same `product_id` + same params → same structure

**Interface (concept):**

```python
class Builder(Protocol):
    def build(self, request: BuildRequest) -> BuildResult: ...
```

---

### 4.3 Validator

**Purpose:** Quality gates before owner sees product.

| Check | v0.1 |
|-------|------|
| Required files exist | ✅ |
| `manifest.json` valid | ✅ |
| No path traversal / escape sandbox | ✅ |
| Template tests pass | ✅ |
| Custom lint rules | stub |

**Output:** `ValidationReport` — pass/fail + list of issues (explainable for owner).

```python
class Validator(Protocol):
    def validate(self, product_path: Path) -> ValidationReport: ...
```

Failed validation → product status `rejected`, event `product.validation_failed`.

---

### 4.4 Packager

**Purpose:** Prepare artifact for owner review in Command Center.

| Input | Output |
|-------|--------|
| Validated `sandbox/products/{id}/` | `sandbox/packages/{id}.zip` + `package.json` metadata |

Owner sees: name, template, file list, validation summary, **Open folder** / download zip (local only).

---

### 4.5 Publisher (stub)

**Purpose:** Reserve interface for future deploy — **does nothing in v0.1**.

```python
class Publisher(Protocol):
    def publish(self, package_id: str, target: str) -> PublishResult:
        if mode != PRODUCTION:
            return PublishResult(skipped=True, reason="sandbox mode")
        raise NotImplementedError("Production publish not enabled")
```

Events: `publish.skipped` with reason `sandbox_mode`.

---

### 4.6 SandboxGuard

**Purpose:** Central enforcement — all Factory components check mode.

- Blocks any HTTP client usage in Factory code (v0.1: no HTTP imports in `factories/`)
- Blocks writes outside `sandbox/`
- Blocks `Publisher` real actions

---

## 5. Product lifecycle (Factory)

```
task.received
    ↓
build.started
    ↓
build.completed
    ↓
validate.started
    ↓
validate.passed | validate.failed
    ↓
package.ready
    ↓
owner.review_pending    ← STOP in v0.1
    ↓
(future) owner.approved → publish.skipped | publish.done
```

**Product statuses:**

`building → validating → ready_for_review → approved | rejected`

No `live` or `published` in v0.1.

---

## 6. Integration with Brain

Factory work = **multi-step Kernel task** or **Factory Agent** registered in Brain.

### Option A (recommended v0.1): Factory as Kernel pipeline

Brain enqueues task with steps:

```
1. factory.build    → Builder
2. factory.validate → Validator
3. factory.package  → Packager
```

Each step = new Agent plugin (`FactoryAgent`) reading/writing sandbox.

**Kernel stays Frozen** — FactoryAgent implements `Agent.run()` like EchoAgent.

### Option B (v0.2): Factory service + BrainAdapter

Integration Layer calls `FactoryService.run(job)` directly.

**v0.1 choice:** Option A — proves plugin model, reuses Kernel context chain.

---

## 7. Command Center (future Factory UI)

**Not in v0.1 implementation.** Reserved tab:

```
Products (Sandbox)
├── product_id (UUID)
├── template
├── status
├── validation
├── [ View ] [ Approve ] [ Reject ]
```

Approve/Reject = owner only, logs event, **no auto-publish**.

---

## 8. File structure (when approved)

```
factories/
├── __init__.py
├── framework/
│   ├── builder.py
│   ├── validator.py
│   ├── packager.py
│   ├── publisher.py      ← stub
│   ├── sandbox_guard.py
│   └── models.py
├── templates/
│   └── landing-page-v1/
├── agents/
│   └── factory_agent.py  ← Kernel Agent plugin
└── sandbox/              ← gitignored output
    ├── products/
    └── packages/

tests/
└── test_factory_framework.py
```

**Integration Layer** (future):

```python
class FactoryAdapter:  # v0.2
    def list_sandbox_products(self) -> list[ProductSummary]: ...
```

Command Center never imports `factories/` directly.

---

## 9. Implementation steps (after gates)

| Step | Deliverable | Gate |
|------|-------------|------|
| 0 | Owner browser checklist | `OWNER_BROWSER_GATE.md` |
| 1 | `landing-page-v1` template + Builder | tests |
| 2 | Validator + SandboxGuard | tests |
| 3 | Packager | tests |
| 4 | Publisher stub | tests |
| 5 | FactoryAgent + Brain enqueue | integration test |
| 6 | Command Center Products tab | owner review |

**Do not implement Step 1 until Step 0 complete.**

---

## 10. What Factory v0.1 does NOT do

- Telegram bots (that's `telegram-bot-v1` template — **after** framework)
- Internet / HTTP / webhooks
- Payments / Stripe / crypto
- Real Publisher / deploy
- AI-generated code from scratch (templates only)
- Auto-approve products

---

## 11. Path to revenue (honest)

| Stage | Status |
|-------|--------|
| Kernel + Brain + Command Center | ✅ Done (pending owner browser) |
| Factory Framework + Sandbox | 📋 This document |
| Quality templates | Not started |
| Owner approves sandbox products | Not started |
| Publish (where legal) | Not started |
| Real users + feedback | Not started |
| Revenue automation | Not started |

Users prove willingness to pay — not the framework alone.

---

## 12. Approval checklist

- [ ] Owner completed browser gate
- [ ] Sandbox-only v0.1 accepted
- [ ] `landing-page-v1` as first template (company landing + contact form) accepted
- [ ] FactoryAgent via Kernel pipeline (Option A) accepted
- [ ] Owner says: **"Factory Framework approved. Begin Step 1."**

---

*Design only. No Factory code until owner gate + explicit approval.*
