"""CCI architectural standard v1.0 — frozen principles for implementers."""

from __future__ import annotations

# Bump only with intentional ruleset changes (golden tests must follow).
CCI_VERSION = "1.0"
CCI_RULESET = "2026-07"

GOLDEN_RULE = (
    "CCI never optimizes the number of emails sent. "
    "It optimizes the probability of starting a commercial dialogue."
)

# Canon rules (enforce in code + review):
# 1. Deterministic: same input → same Decision (CCI-0).
# 2. Explainability first: no reasons → no Decision.
# 3. Confidence is mathematical (weights), not LLM.
# 4. Contact Confidence ≠ Company Fit (separate fields).
# 5. Auto commercial send MUST pass CCI; direct email pick outside CCI is forbidden.
# 6. Hard vs Soft blocks (learning) — Soft revisitable; Hard never auto (CCI-5+).
