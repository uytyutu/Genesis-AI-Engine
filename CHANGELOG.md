# Changelog

All notable changes to Genesis AI Engine are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [0.2.1] — 2026-07-03

### Genesis OS — owner product

### Added
- **Onboarding wizard** — welcome, name, goals, product interests
- **Owner dashboard** — greeting, revenue metrics, events, load %
- Pages: `/projects`, `/revenue`, `/ai`, `/dev` (technical mode separate)
- Launcher shows live business metrics from API

---

### Product Delivery

### Added
- **Genesis Platform** branding — Launcher simplified (`Genesis.exe`), business Dashboard
- Dashboard: revenue, products, queue — no Kernel/Brain on main screen
- **Создать продукт** wizard (`/create`) — Landing Page intent saved to `factory_intents.jsonl`
- Marketplace placeholder (`/marketplace`)
- GUI-first rule in `CURSOR_AUTONOMY_RULES.md`

### Changed
- Moratorium on new architecture `.md` files — ship UI first
- Developer details behind «Для разработчика» (Launcher + Dashboard)

---

### Phase 0 — Kernel

### Added
- Independent repository at `D:\Games\Genesis-AI-Engine`, separated from Perfect Pallet
- **Kernel**: accept task → plan → run agents → return result
- **AgentRegistry** — plug-in agents without changing kernel
- **SimplePlanner** — single-step and multi-step pipelines
- **Goal** — universal goal types (revenue, leads, traffic, users, downloads, subscribers)
- **StepContext** — pass output from previous step to next step (Package B)
- **Metrics** — `duration_ms` and timestamps on tasks, steps, and audit log (Package A)
- **EchoAgent** — test agent for wiring and context chain
- 11 automated tests in `tests/test_kernel.py`
- Demo script `examples/run_kernel_demo.py`
- Docs: `NORTH_STAR.md`, `BUILD_ORDER.md`, `KERNEL_FLOW.md`, `OWNER_GUIDE.md`, `SEPARATION.md`, `WHY.md`
- Placeholder folders: `brain/`, `factories/`, `dashboard/`, `memory/`
- `CURSOR_AUTONOMY_RULES.md` — development discipline for Cursor
- `VERSION` file

### Not included (by design)
- Brain, Command Center, Factory
- Database, Redis, Docker, async, Event Bus
- Opportunity Engine, Revenue AI, Capital Engine, CEO AI, World Model, Evolution Engine

### Gate passed — 2026-07-02

- Python 3.14.6 on owner machine
- `11 passed in 0.12s`
- Demo `run_kernel_demo.py` — success
- **Kernel Frozen** — Phase 0 officially closed
- Owner authorized Brain v0.1 design phase

---

## [Unreleased]

### Launcher Process Management Fix (2026-07-08)

- Fixed launcher hanging when backend `git_commit` differs from repository HEAD.
- Idle status polling no longer attempts to restart backend.
- Added reconnect mutex to prevent concurrent restart attempts.
- Added verified `taskkill` result handling.
- Prevented false "Freed port" log messages.
- Improved backend restart validation before launching a new instance.

### Implemented — Brain Step 1 (2026-07-02)

- `QueueStorage` protocol + `JsonQueueStorage`
- `TaskLifecycle`, `QueuedTaskRecord`, `BrainEventType`, `make_brain_event`
- 18 tests in `tests/test_queue_storage.py`
- Kernel unchanged (Frozen)

### Implemented — Brain Step 2 (2026-07-03)

- `AuditStorage` protocol + `JsonlAuditStorage` (append-only)
- `read_all()` for tests and future Dashboard
- 8 tests in `tests/test_audit_storage.py`
- `docs/FUTURE_LAYERS.md` — evolution, crypto, security (planned, not built)
- Total test suite: **37 passed**

### Implemented — Brain v0.1 complete (2026-07-03)

- `Brain` facade: enqueue, run_next, run_all, cancel, pause, resume
- `TaskQueue`, `BrainConfig`, `BrainRunResult`
- Integration tests: Queue → Brain → Kernel → Audit
- `docs/BRAIN_FLOW.md`, `examples/run_brain_demo.py`
- **47 tests passed** — Kernel unchanged (Frozen)

### Command Center v0.1 scaffold (2026-07-03)

- Legal compliance rule in `WHY.md` + `CURSOR_AUTONOMY_RULES.md`
- `docs/COMMAND_CENTER_ARCHITECTURE_v0.1.md`
- FastAPI mock API (`dashboard/backend/`) — 5 tests
- Next.js + Tailwind UI shell (`dashboard/frontend/`) — requires Node.js
- **Not connected to Brain** — v0.2

### Next

- Owner installs Node.js, verifies UI
- v0.2: `brain_adapter.py` connects Command Center to real Brain
- Task queue
- Persistent audit log (file-based)
- Submit tasks to Kernel via Brain API
