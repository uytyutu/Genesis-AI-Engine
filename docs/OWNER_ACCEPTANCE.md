# Owner Acceptance — Genesis ABOS

**Status:** BLOCKING — no Factory code until you complete this checklist and answer UX questions.

You are the **first user** of Genesis. If it is not comfortable for you, it will not be comfortable for anyone else.

---

## Before you start

Install **Node.js 20+** from https://nodejs.org/

```powershell
# Terminal 1
cd D:\Games\Genesis-AI-Engine\dashboard\backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000

# Terminal 2
cd D:\Games\Genesis-AI-Engine\dashboard\frontend
npm install
npm run dev
```

Open http://localhost:3000

**Tip:** Click **Demo Mode** on Overview — Genesis creates 5 tasks and runs them automatically (~10 seconds). Then complete the checklist below.

---

## First launch

| # | Check | Done |
|---|-------|------|
| 1 | Command Center opened | ☐ |
| 2 | Kernel shows green (online) | ☐ |
| 3 | Brain shows green (online) | ☐ |
| 4 | Queue shows counts (Pending, Running, Completed…) | ☐ |

---

## Work with tasks

| # | Check | Done |
|---|-------|------|
| 5 | Created a task (Tasks → Create task) | ☐ |
| 6 | Ran a task (Tasks → Run next) | ☐ |
| 7 | Saw UUID (task ID column) | ☐ |
| 8 | Saw status `running` (briefly) or `queued` | ☐ |
| 9 | Saw status `completed` | ☐ |

---

## Control

| # | Check | Done |
|---|-------|------|
| 10 | Pause works (Overview → Pause) | ☐ |
| 11 | Resume works (Overview → Resume) | ☐ |
| 12 | Cancel works (Tasks → Cancel on queued task) | ☐ |

---

## Journal

| # | Check | Done |
|---|-------|------|
| 13 | Recent events visible (Overview → Activity) | ☐ |
| 14 | Execution time visible (Tasks → Duration) | ☐ |
| 15 | Result visible (Tasks → Result: ok / failed) | ☐ |

---

## UX — answer honestly

| # | Question | Yes / No |
|---|----------|----------|
| 1 | Is it understandable **without being a programmer**? | ☐ |
| 2 | Did you find the button you needed within **10 seconds**? | ☐ |
| 3 | Do you understand what **Brain** does? | ☐ |
| 4 | Do you understand the **system state** (green / yellow / red)? | ☐ |
| 5 | Do you **want to use it again**? | ☐ |

**Rule:** If any answer is **No** — Factory is postponed. Tell Cursor what to fix first.

---

## When you are satisfied

Write to Cursor:

> **Owner Acceptance passed.** I am comfortable using Genesis. Approve Factory Framework Step 1.

Or if something failed:

> **Owner Acceptance failed.** [describe what was confusing or broken]

---

## What happens next (only after acceptance)

1. Factory Framework Step 1 — **Landing Page** template in Sandbox (not Telegram)
2. Builder → Validator → Packager → show you the result → STOP

No publish. No payments. No internet.

---

*You are the main tester now. Genesis must please you first.*
