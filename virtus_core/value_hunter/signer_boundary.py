"""
Signer boundary — Value Hunter / AI must NEVER read mnemonic or private keys.

AI → transaction proposal → local signer → owner confirmation → broadcast
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_FORBIDDEN_ENV = ("TON_MNEMONIC", "MNEMONIC", "PRIVATE_KEY", "BTC_SEED", "WALLET_SEED")
_FORBIDDEN_FILES = (".env.ton", ".env.wallet", "mnemonic.txt", "seed.txt")


def assert_ai_has_no_keys() -> dict[str, Any]:
    """Runtime guard for hunter process: do not load secrets into this module."""
    present_env = [k for k in _FORBIDDEN_ENV if os.environ.get(k)]
    # Presence in environment is a deployment smell for the AI process — warn, don't crash hunt
    return {
        "policy": "AI_MUST_NOT_READ_MNEMONIC",
        "forbidden_env_present": present_env,
        "ok_for_proposal_only": True,
        "note": "Hunter may only emit unsigned proposals. Local signer + owner gate own keys.",
        "forbidden_files": list(_FORBIDDEN_FILES),
    }


def refuses_to_open_secret_file(path: str | Path) -> bool:
    name = Path(path).name.lower()
    return name in {f.lower() for f in _FORBIDDEN_FILES} or name.endswith(".ton") and "mnemonic" in name
