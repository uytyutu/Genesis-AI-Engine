# Virtus Core

**v0.2.0** — desktop product for owners. Architecture docs in `docs/` (frozen).

## For owners (no terminal)

1. Double-click **Virtus Core** on Desktop (shortcut to `dist\Genesis.exe`)
2. Click **Запустить** in the launcher
3. Click **Открыть Virtus Core** → http://localhost:3000
4. Click **Создать продукт**

Requires Node.js 20+ for Dashboard (Launcher will hint if missing).

## For developers

```powershell
cd D:\Games\Genesis-AI-Engine
python -m pip install -e ".[dev]"
pytest -v
python examples/run_kernel_demo.py
```

## Independence from Perfect Pallet

| Check | Status |
|-------|--------|
| Genesis code inside Perfect Pallet | None |
| Perfect Pallet imports Genesis | None |
| Shared Unity assets or game scripts | None |

## Docs

| File | Purpose |
|------|---------|
| `PROJECT_STATE.md` | **Open this first** — where the project stands right now |
| `WHY.md` | Constitution — why Genesis exists |
| `CURSOR_AUTONOMY_RULES.md` | Rules for Cursor development |
| `docs/NORTH_STAR.md` | Vision |
| `docs/BUILD_ORDER.md` | Phase order |
| `docs/KERNEL_FLOW.md` | How kernel works (20 sec) |
| `docs/OWNER_GUIDE.md` | Plain language for owner |
| `docs/KERNEL_GATE.md` | When Kernel is "done" |
| `docs/OWNER_BROWSER_GATE.md` | **Do this before Factory** |
| `docs/FACTORY_FRAMEWORK_ARCHITECTURE_v0.1.md` | Factory design (Sandbox) |
| `docs/INTEGRATION_LAYER.md` | Integration Layer |
| `docs/BRAIN_ROADMAP.md` | Brain v0.1 → v1.0 roadmap |
| `docs/FOUNDATION_CHECK.md` | Latest architecture review |

## Current phase

**Phase 0 — Kernel** (A + B complete). Brain not started.
