# Genesis Learning v1

**Status:** Active · **Does not auto-fix code**

## Cycle (mandatory)

```
Detect → Analyze → Recommend → Approve → Fix → Verify → Remember
```

Memory **speeds up analysis** — never skips Approve or Verify.

## Implementation

| Piece | Path |
|-------|------|
| API | `launcher/genesis_learning.py` |
| Knowledge base | `dashboard/backend/app/memory/genesis_learning.json` (runtime) |
| Seed incidents | `dashboard/backend/app/memory/genesis_learning_incidents_seed.json` |
| Regression | `tests/test_launcher_brand_image.py`, `tests/test_genesis_learning.py` |

## Usage (Cursor)

```python
from launcher.genesis_learning import find_similar, record_incident, LearningIncident

hits = find_similar("CTkImage")
# use past fix as hint — still analyze and verify

record_incident(LearningIncident(...))  # after verified fix
```

## First incident (2026-07-04)

**Symptom:** «Не удалось запустить Genesis»  
**Cause:** `CTkImage` got `str` path instead of `PIL.Image`  
**Fix:** `load_mark_pil_image()` in `launcher/branding.py`
