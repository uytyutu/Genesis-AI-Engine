# How the Genesis Kernel works

Read this in 20 seconds. No code required.

## The flow

```
Task
 ↓
Planner
 ↓
Kernel
 ↓
Agent (step 1) → Agent (step 2) → …
 ↓
Result
```

## What each part does

| Part | Role |
|------|------|
| **Task** | A job request: name, optional goal (revenue, users, leads…), and instructions |
| **Planner** | Turns instructions into ordered steps: which agent, which action |
| **Kernel** | Runs steps in order, passes context forward, records timing |
| **Agent** | Does one piece of work (search, build, test — later) |
| **Result** | Success or failure, duration, outputs, audit trail |

## Context between steps (Package B)

Step 2 can see what step 1 produced. This is required for a real factory pipeline:

```
analyze market → build product → test product
```

Without context, each step would be blind.

## Metrics (Package A)

Every task and step records:

- **when** it started and finished (timestamp)
- **how long** it took (milliseconds)

Example audit line:

```
[2026-07-02T21:30:00+00:00] agent.done · echo · analyze · 0.42 ms
```

These logs will feed the owner Dashboard later.

## What the kernel does NOT do

- No database
- No queue
- No daily strategy approve
- No money tracking
- No internet

Those come in Brain, Memory, Dashboard — later layers.
