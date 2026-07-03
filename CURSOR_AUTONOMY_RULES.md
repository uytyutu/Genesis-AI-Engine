# Genesis Development Rules v1.0

Genesis is a **fully separate project** from Perfect Pallet.  
All development happens inside `D:\Games\Genesis-AI-Engine` unless the owner explicitly says otherwise.

---

## 1. Check the foundation first

Before starting a new phase:

- Run all Kernel tests (`pytest -v`)
- Confirm docs match code
- Report scaling risks — do not rewrite architecture silently
- Fix only **safe** bugs without owner approval
- **Never change architecture** without explaining why and waiting for confirmation

---

## 2. Autonomy boundaries

### Allowed automatically

- Write code
- Create new files and folders
- Refactor within the current phase scope
- Run tests
- Fix errors found by tests
- Update documentation to match code

### Requires owner confirmation

- Delete files
- Change architecture (new layers, moving modules, breaking Kernel API)
- Run dangerous shell commands
- Install external services (Redis, PostgreSQL, Docker, cloud APIs)
- Any action outside the Genesis project folder
- Any financial action (payments, ads spend, domain purchase)
- Any feature that may violate law or platform ToS (see `WHY.md` compliance section)

---

## 2b. Legal compliance (mandatory)

> **Genesis acts only through lawful means, respects platform rules, and never performs actions that violate law or third-party terms of service.**

Never implement: spam, ToS bypass, unauthorized account access, moving others' money, publishing without permission where prohibited, copyright violation.

When in doubt — stop and ask the owner.

## 2c. Product Delivery mode (active)

**Documents:** No new documents without a good reason. **Priority — code, tests, and owner UX.** Create or update docs only when they genuinely help the project move forward.

**Keep current:** `WHY.md`, `PROJECT_STATE.md`, `README.md`, `CHANGELOG.md`, and existing `docs/` when code changes require it.

**Filter:** Every change must make Genesis **simpler for the owner** and **stronger as a platform** (`WHY.md`).

**GUI-first rule:**

> **Every Genesis capability must be reachable through the graphical interface. Terminal is for development and diagnostics only.**

**Current focus:** Mission Control → Factory «Создать продукт» → first Landing in Sandbox.

**Time split:** **80%** code, tests, UX, first users · **20%** architecture and new ideas.

**Two-week focus (no new major modules):** only improve Factory / Improve / UX / real owner feedback.

**Daily question:** *Сделал ли Genesis сегодня продукт, за который человек готов заплатить?*

**Factory success criterion:** owner says *«Я готов отправить этот сайт первому клиенту»* — not pytest green alone.

**Cursor directive (frozen):**

> Следующие две недели запрещено добавлять новые большие системы. Каждый день улучшайте только три вещи: качество Landing Page, удобство интерфейса и скорость создания продукта. После каждой итерации показывайте результат реальному человеку и собирайте обратную связь.

---

## 3. Report after every phase

**Never reply with only "Done."** Always use this format:

```
━━━━━━━━━━━━━━━━━━
Что сделано
Что изменилось
Что проверено
Что не проверено
Есть ли риски
Что предлагается дальше
━━━━━━━━━━━━━━━━━━
```

Plus the three owner questions:

1. What can Genesis do now?
2. What can it not do yet?
3. What is the next step?

Use **facts** (test count, durations, limitations) — not subjective scores.

**After every phase:** update `PROJECT_STATE.md` with current version, module status, last test results, and next step.

---

## 3b. Tests before next module

Each module must have its own tests **before** starting the next module:

```
Kernel  → tests pass → Brain  → tests pass → Command Center → tests pass → …
```

Do not begin Brain until Kernel tests pass.  
Do not begin Factory until Brain tests pass.  
And so on.

---

## Sandbox rule (Factory — mandatory)

All Factory work defaults to **🟢 Sandbox mode**:
- builds only under `sandbox/` locally
- no internet, payments, or real publish
- Publisher is stub until owner enables Production

See `docs/FACTORY_FRAMEWORK_ARCHITECTURE_v0.1.md`.

---

## 4. Build bottom-up — do not skip phases

```
Kernel
  ↓
Brain
  ↓
Command Center
  ↓
Factory
  ↓
Opportunity Engine
  ↓
Revenue AI
  ↓
Capital Engine
  ↓
World Model
  ↓
CEO AI
  ↓
Evolution Engine
```

Do not jump ahead. World Model and CEO AI are **not** next.

---

## 5. New large modules

Before building any major module:

1. Explain why it is needed **now**
2. Show pros and cons
3. Wait for owner confirmation
4. For Brain: **design first**, then implement in small versions (v0.1 → v0.2 → v1.0)

---

## 6. Think like an architect

- Do not add features "for the future" if they are not needed for the next phase
- Do not add Redis, PostgreSQL, Docker, async, or Kubernetes until the current layer proves it needs them
- Each module must deliver **real value** on top of what already works
- **Kernel must stay stable** — Brain uses Kernel as API, does not modify Kernel internals

---

## 7. Kernel completion gate

Kernel is **done** only when:

- [ ] All tests pass locally (`11 passed, 0 failed`)
- [ ] Documentation matches code
- [ ] No known critical bugs
- [ ] Owner has seen demo output

**Only then** does Brain development begin.

---

## 8. Reference documents

| Document | Purpose |
|----------|---------|
| `WHY.md` | Constitution — why Genesis exists |
| `docs/NORTH_STAR.md` | Vision in one page |
| `docs/BUILD_ORDER.md` | Phase order |
| `docs/OWNER_GUIDE.md` | Plain language for the owner |
| `VERSION` | Current version and phase |
| `CHANGELOG.md` | History of changes |
| `PROJECT_STATE.md` | Live snapshot — update after every phase |
