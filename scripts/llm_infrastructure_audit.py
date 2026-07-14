"""LLM infrastructure audit — development stage (free/local models)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.llm_router.audit import audit_infrastructure, infrastructure_report_table
from app.env_loader import load_local_env


def main() -> int:
    load_local_env()
    memory = BACKEND / "memory"
    report = audit_infrastructure(memory_dir=memory, force_probe=True)
    print(infrastructure_report_table(report))
    print()
    import os
    pin = os.environ.get("GENESIS_LLM_PROOF_PROVIDER", "").strip()
    if pin:
        print(f"Proof pin active: GENESIS_LLM_PROOF_PROVIDER={pin}")
    else:
        print(
            "Reproducible proof: set GENESIS_LLM_PROOF_PROVIDER=groq|gemini|ollama "
            "(dev, restart backend, no code change)."
        )
    print()
    if report.get("ready_for_architecture_proof"):
        print("OK: >=1 LLM responds — architecture proof can proceed.")
        return 0
    print("WAIT: no responding LLM now (rate limits / keys). Architecture unchanged — retry later.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
