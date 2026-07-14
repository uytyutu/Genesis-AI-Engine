#!/usr/bin/env python3
"""Package portable swarm workers for remote VPS / cloud function deploy.

Usage (from repo root):
  py scripts/deploy_swarm_worker.py
  py scripts/deploy_swarm_worker.py --list-only

On the remote server (after copy):
  cd /opt/genesis-worker
  py -3.12 -m pip install httpx fastapi uvicorn
  set FARM_WORKER_ROLE=pool
  py -3.12 -m uvicorn dashboard.backend.app.main:app --host 0.0.0.0 --port 8100

Then in laptop .env.local:
  FARM_EXECUTION_MODE=remote
  FARM_WORKER_POOL_URL=http://YOUR_VPS_IP:8100
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PORTABLE_PATHS = [
    "swarm",
    "scripts/deploy_swarm_worker.py",
    "dashboard/backend/app/integration/swarm_bridge.py",
    "dashboard/backend/app/integration/micro_farm_service.py",
    "dashboard/backend/app/integration/engine_ai_service.py",
    "dashboard/backend/app/integration/opportunity_service.py",
    "dashboard/backend/app/integration/finance_service.py",
    "dashboard/backend/app/integration/business_mode_service.py",
    "dashboard/backend/requirements.txt",
]


def manifest() -> dict:
    files = []
    for rel in PORTABLE_PATHS:
        path = ROOT / rel
        if path.is_file():
            files.append(rel)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    files.append(str(child.relative_to(ROOT)).replace("\\", "/"))
    return {
        "package": "genesis-swarm-worker",
        "root": str(ROOT),
        "files": files,
        "deploy_hint": (
            "scp -r swarm user@vps:/opt/genesis-worker/ && "
            "rsync dashboard/backend user@vps:/opt/genesis-worker/"
        ),
        "run_hint": (
            "На VPS: uvicorn dashboard.backend.app.main:app --host 0.0.0.0 --port 8100"
        ),
        "laptop_env": {
            "FARM_EXECUTION_MODE": "remote",
            "FARM_WORKER_POOL_URL": "http://YOUR_VPS:8100",
            "FARM_WORKER_POOL_TOKEN": "optional-shared-secret",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genesis swarm worker deploy manifest")
    parser.add_argument("--list-only", action="store_true", help="Print JSON manifest only")
    parser.add_argument("--out", type=Path, help="Write manifest to JSON file")
    args = parser.parse_args()

    data = manifest()
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"Manifest written: {args.out}")
    else:
        print(text)

    if not args.list_only:
        print("\n--- One-command copy (edit user@vps) ---")
        print(data["deploy_hint"])
        print("\n--- Laptop .env.local ---")
        for key, value in data["laptop_env"].items():
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
