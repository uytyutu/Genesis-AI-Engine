# RC1 Certification (Owner)

**Status: NOT CERTIFIED** — engineering sprint ≠ PASS.

Do not soften: architecture, pytest green, or Provider Gateway scaffold **do not** make RC1 PASS.  
P0 Image Provider + Media QA (live adapters) starts only after **RC1 A/B/C/D PASS**.

Fill dates only after real use. Agent must not mark PASS.

| Certificate | Window | Owner result | Date | Notes |
| --- | --- | --- | --- | --- |
| **RC1-A Stability** | 24h continuous | ☐ PASS / ☐ FAIL | | Launcher · Backend · Frontend · Farm · RAM · CPU |
| **RC1-B First Customer** | one blind journey | ☐ PASS / ☐ FAIL | | Interview → site → Workspace → edit → Publish |
| **RC1-C Owner Day** | 6–8h workday | ☐ PASS / ☐ FAIL | | Morning open → evening still healthy |
| **RC1-D Recovery** | deliberate faults | ☐ PASS / ☐ FAIL | | Kill FE · Kill BE · offline · restore |

## RC1 PASS when

All four rows = **PASS** (Owner-signed).

Then: `commit RC1 Stability` → freeze → Website Control Owner Test → commit Website Control.

## RC1-B path (checklist)

```text
Enter → choose product → Interview → receive site
→ Business Workspace → change Hero → replace photo
→ add service → Publish → open finished site
```

No developer help. Any stuck step = FAIL (record where).

## RC1-D faults (checklist)

| Fault | Expected | Observed |
| --- | --- | --- |
| Kill Frontend | soft restart FE only | |
| Kill Backend | repair BE; FE not massacred | |
| Offline briefly | honest status; recover on reconnect | |
| Restore all | Health green without “magic” | |

## Log evidence

- `launcher/logs/launcher_crash.log`
- `launcher/logs/genesis_launcher.log`
- `launcher/logs/backend.log` / `frontend.log`
