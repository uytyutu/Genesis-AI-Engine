# Genesis — Build Order (bottom-up)

Do not build top-down. Each layer must prove the layer below works.

| Order | Layer | Proof |
|-------|-------|-------|
| 0 | **Kernel** | Task → plan → agent → result (11 tests) |
| 1 | **Brain** | Queue + log → Kernel API |
| 2 | **Command Center** | Live UI + Integration Layer | ✅ Done (owner browser gate pending) |
| 2b | **Guardian** | Safety Monitor — budgets, Dry Run, emergency brake (**not in Kernel**) | 📋 Design only |
| 3 | **Factory** | Sandbox framework → Landing Skill first | 📋 Design only |
| 4 | **Opportunity Engine** | Explainable score cards |
| 5 | **Revenue AI** | Portfolio recommendations |
| 6 | **Capital Engine** | Budget allocation proposals |
| 7 | **World Model** | Curated signals feed Opportunity |
| 8 | **Coordinator / CEO AI** | Routes roles — **last**; owner still decides 🔴 | 📋 After Analyst |
| 9 | **Evolution Engine** | Library proposals (approve to apply) |

**Role implementation phases (practical):** `docs/ROLES.md` — Factory+Validator → Publisher+Finance → Analyst → Coordinator.

**Current phase:** Integration Layer + Launcher + Owner UX done. **Owner browser gate** → Factory Skill v0.1.

**Operating system:** `docs/COMPANY_OS.md` · **Roles:** `docs/ROLES.md` · **Lifecycle:** `docs/LIFECYCLE.md` · **Safety:** `docs/GUARDIAN.md`

**Factory:** see `docs/FACTORY_FRAMEWORK_ARCHITECTURE_v0.1.md` — Sandbox only, no code yet.

**Repository:** `D:\Games\Genesis-AI-Engine` — independent from Perfect Pallet.
