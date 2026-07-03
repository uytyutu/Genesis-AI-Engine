# Owner Guide — Phase 0: Kernel

Plain language. No programming required.

---

## What was created?

**Genesis Kernel** — the heart of the system.

It does exactly four things:

1. **Accept** a task («do this work»)
2. **Plan** which workers run and in what order
3. **Run** those workers (called agents)
4. **Return** a result — success or failure, with timing

Think of it as the engine room of a ship. It does not decide *where* the ship sails. It runs what it is told.

---

## Why do we need this?

Every future part of Genesis — Brain, Factory, Command Center — will send work to the Kernel.

If the heart is unreliable, everything above it breaks.

We built the heart first, on purpose.

---

## How does it work?

### Example: two-step job

1. **Task:** «Analyze warehouse bots, then summarize for owner»
2. **Planner:** Step 1 = analyze, Step 2 = summarize
3. **Kernel:** Runs step 1, passes result to step 2, records time
4. **Result:** Both steps succeeded in ~1 ms total (on a test machine)

### What you would see in a future screen

```
Task: warehouse-bot-pipeline
Status: Success
Duration: 1.2 ms

Step 0: echo.analyze — Success — 0.4 ms
Step 1: echo.summarize — Success — 0.3 ms
  (saw output from step 0)
```

---

## How will you use this as owner?

**Not directly yet.** You will not open the Kernel.

You will open the **Command Center** (built later), which shows:

- income today
- products running
- decisions waiting for your approve

The Kernel works underneath, like an engine under the dashboard of a car.

When something fails, the Kernel's journal will answer: *what ran, how long, where it stopped, and why.*

---

## What is in the project folder?

| Folder | Status | Meaning for you |
|--------|--------|-----------------|
| `kernel/` | **Built** | Heart — runs tasks |
| `agents/` | **Built** | Test worker (echo) |
| `brain/` | Empty | Future: decides when to run |
| `factories/` | Empty | Future: builds products |
| `dashboard/` | Empty | Future: your morning screen |
| `memory/` | Empty | Future: saves history and money |

---

## Separation from Perfect Pallet

Genesis lives in its own folder:

`D:\Games\Genesis-AI-Engine`

Perfect Pallet is only a game. Genesis is a separate product.

If one day Genesis helps build game content, Perfect Pallet becomes a **client** — not a subfolder.

---

## How to verify it works (optional)

If Python 3.11+ is installed:

```powershell
cd D:\Games\Genesis-AI-Engine
python -m pip install -e ".[dev]"
pytest -v
python examples/run_kernel_demo.py
```

Expected: **11 tests pass**, demo prints Success and step durations.

---

## Current limitations (facts, not opinions)

- One task at a time (no queue)
- Journal lives in memory — gone after restart
- Only a test agent (echo), not real product builders
- No screen UI yet
- No connection to money, Telegram, or the internet

---

*Phase 0 complete. Next phase: Brain — only after you confirm Kernel tests pass.*
