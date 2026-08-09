"""Virtus Core Provider Gateway — Creative Production Pipeline foundation.

Architecture (Owner 2026-08-08): Virtus = brain/orchestrator. Specialized models
do heavy work. Clients never see which provider ran.

Order of build (do not jump ahead):
  RC1 → Website Control → Store → Chatbot
  → Provider Gateway (this package)
  → Image Pipeline + Media QA
  → Video Pipeline
  → 3D Experience
  → Social

This module is the **contract**. Full Connect UI / live API calls come later.

P0 Image: `media_qa.py` + `image_pipeline.py` (Generate → QA → retry → hard fail).
Live HTTP adapters only after RC1 PASS.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    THREE_D = "three_d"


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    modality: Modality
    label: str
    env_aliases: tuple[str, ...] = ()
    notes: str = ""


# Catalog — connect UI will use this; keys stored via CredentialVault, not only .env
PROVIDER_CATALOG: tuple[ProviderSpec, ...] = (
    ProviderSpec("openai_chat", Modality.TEXT, "OpenAI", ("OPENAI_API_KEY",)),
    ProviderSpec("anthropic", Modality.TEXT, "Anthropic", ("ANTHROPIC_API_KEY",)),
    ProviderSpec("xai_grok", Modality.TEXT, "xAI / Grok", ("XAI_API_KEY", "GROK_API_KEY")),
    ProviderSpec("groq", Modality.TEXT, "Groq", ("GROQ_API_KEY",)),
    ProviderSpec("openai_images", Modality.IMAGE, "OpenAI Images", ("OPENAI_API_KEY",)),
    ProviderSpec("fal_flux", Modality.IMAGE, "FAL / FLUX", ("FAL_KEY", "FAL_API_KEY")),
    ProviderSpec("google_veo", Modality.VIDEO, "Google Veo", ("GOOGLE_API_KEY", "VEO_API_KEY")),
    ProviderSpec("runway", Modality.VIDEO, "Runway", ("RUNWAY_API_KEY",)),
    ProviderSpec("kling", Modality.VIDEO, "Kling", ("KLING_API_KEY",)),
)


# Preferred fallback order per modality (first available wins)
FALLBACK_CHAINS: dict[Modality, tuple[str, ...]] = {
    Modality.TEXT: ("groq", "openai_chat", "anthropic", "xai_grok"),
    Modality.IMAGE: ("openai_images", "fal_flux"),
    Modality.VIDEO: ("google_veo", "runway", "kling"),
    Modality.VOICE: (),
    Modality.THREE_D: (),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str) -> str:
    return re.sub(r"[^\w\-]", "_", (value or "").strip())[:64] or "unknown"


@dataclass
class ProviderStatus:
    provider_id: str
    modality: str
    connected: bool
    label: str
    detail: str = ""
    last_test_at: str | None = None
    last_error: str | None = None


class CredentialVault:
    """Secure-ish local store for provider keys (memory dir). Not world-readable .env edits."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "provider_gateway"
        self._root.mkdir(parents=True, exist_ok=True)
        self._path = self._root / "credentials.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"version": 1, "providers": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "providers": {}}
        if not isinstance(data, dict):
            return {"version": 1, "providers": {}}
        providers = data.get("providers")
        if not isinstance(providers, dict):
            data["providers"] = {}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _now()
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        try:
            self._path.chmod(0o600)
        except OSError:
            pass

    def set_key(self, provider_id: str, api_key: str) -> None:
        data = self._load()
        providers = data.setdefault("providers", {})
        providers[_safe_id(provider_id)] = {
            "api_key": (api_key or "").strip(),
            "updated_at": _now(),
        }
        self._save(data)

    def get_key(self, provider_id: str) -> str | None:
        data = self._load()
        row = (data.get("providers") or {}).get(_safe_id(provider_id))
        if isinstance(row, dict):
            key = str(row.get("api_key") or "").strip()
            return key or None
        return None

    def clear_key(self, provider_id: str) -> None:
        data = self._load()
        providers = data.setdefault("providers", {})
        providers.pop(_safe_id(provider_id), None)
        self._save(data)

    def has_key(self, provider_id: str) -> bool:
        return bool(self.get_key(provider_id))


class ProviderGateway:
    """Orchestration surface: pick provider, fallback, status. No fake Connect success."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = Path(memory_dir)
        self.vault = CredentialVault(self.memory_dir)

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": p.id,
                "modality": p.modality.value,
                "label": p.label,
                "env_aliases": list(p.env_aliases),
                "notes": p.notes,
            }
            for p in PROVIDER_CATALOG
        ]

    def _env_key(self, spec: ProviderSpec) -> str | None:
        import os

        for name in spec.env_aliases:
            val = (os.getenv(name) or "").strip()
            if val:
                return val
        return None

    def resolve_key(self, provider_id: str) -> str | None:
        vault_key = self.vault.get_key(provider_id)
        if vault_key:
            return vault_key
        for spec in PROVIDER_CATALOG:
            if spec.id == provider_id:
                return self._env_key(spec)
        return None

    def status_board(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        by_mod: dict[str, list[str]] = {}
        for spec in PROVIDER_CATALOG:
            key = self.resolve_key(spec.id)
            connected = bool(key)
            rows.append(
                asdict(
                    ProviderStatus(
                        provider_id=spec.id,
                        modality=spec.modality.value,
                        connected=connected,
                        label=spec.label,
                        detail="Connected" if connected else "Not connected",
                    )
                )
            )
            by_mod.setdefault(spec.modality.value, []).append(spec.id)

        ready = {
            "text": any(
                r["connected"] for r in rows if r["modality"] == Modality.TEXT.value
            ),
            "images": any(
                r["connected"] for r in rows if r["modality"] == Modality.IMAGE.value
            ),
            "video": any(
                r["connected"] for r in rows if r["modality"] == Modality.VIDEO.value
            ),
        }
        return {
            "ok": True,
            "title": "AI Provider Gateway",
            "providers": rows,
            "fallback_chains": {
                m.value: list(FALLBACK_CHAINS.get(m) or []) for m in Modality
            },
            "ready": ready,
            "infrastructure": (
                "READY"
                if ready["text"] and ready["images"]
                else "PARTIAL"
                if ready["text"] or ready["images"]
                else "NOT_READY"
            ),
            "law_ru": (
                "Virtus = оркестратор. Клиент не видит имена моделей. "
                "Сначала Image Pipeline + Media QA, потом Video, потом 3D."
            ),
            "updated_at": _now(),
        }

    def select_provider(self, modality: Modality | str) -> dict[str, Any]:
        """Pick first connected provider in fallback chain. Honest if none."""
        mod = Modality(modality) if isinstance(modality, str) else modality
        chain = FALLBACK_CHAINS.get(mod) or ()
        for pid in chain:
            if self.resolve_key(pid):
                spec = next((p for p in PROVIDER_CATALOG if p.id == pid), None)
                return {
                    "ok": True,
                    "modality": mod.value,
                    "provider_id": pid,
                    "label": spec.label if spec else pid,
                    "source": "fallback_chain",
                }
        return {
            "ok": False,
            "modality": mod.value,
            "provider_id": None,
            "error": "no_provider_connected",
            "message": f"No {mod.value} provider connected — open AI Providers and Connect.",
            "chain": list(chain),
        }

    def test_connection(self, provider_id: str) -> dict[str, Any]:
        """
        Soft test: key present. Live HTTP probe comes when Image/Text adapters land.
        Never reports Connected without a key.
        """
        spec = next((p for p in PROVIDER_CATALOG if p.id == provider_id), None)
        if spec is None:
            return {"ok": False, "error": "unknown_provider", "provider_id": provider_id}
        key = self.resolve_key(provider_id)
        if not key:
            return {
                "ok": False,
                "connected": False,
                "provider_id": provider_id,
                "label": spec.label,
                "error": "missing_api_key",
                "message": "Insert API key and Test Connection.",
            }
        # Key shape sanity only (no network yet — avoids fake success)
        if len(key) < 8:
            return {
                "ok": False,
                "connected": False,
                "provider_id": provider_id,
                "error": "key_too_short",
                "message": "API key looks invalid.",
            }
        return {
            "ok": True,
            "connected": True,
            "provider_id": provider_id,
            "label": spec.label,
            "modality": spec.modality.value,
            "message": "Key stored — live probe lands with Image/Text pipeline.",
            "probe": "key_present",
            "tested_at": _now(),
        }

    def connect(self, provider_id: str, api_key: str) -> dict[str, Any]:
        spec = next((p for p in PROVIDER_CATALOG if p.id == provider_id), None)
        if spec is None:
            return {"ok": False, "error": "unknown_provider"}
        key = (api_key or "").strip()
        if len(key) < 8:
            return {"ok": False, "error": "key_too_short"}
        self.vault.set_key(provider_id, key)
        return self.test_connection(provider_id)


def pipeline_stages() -> list[dict[str, str]]:
    """Documented Creative Production Pipeline for CEO / docs."""
    return [
        {"id": "interview", "label": "Client Interview"},
        {"id": "business_intelligence", "label": "Business Intelligence"},
        {"id": "brand_visual_identity", "label": "Brand / Visual Identity"},
        {"id": "creative_director", "label": "Creative Director"},
        {"id": "provider_gateway", "label": "Provider Gateway (Text / Image / Video / 3D)"},
        {"id": "media_pipeline", "label": "Media / Experience Pipeline"},
        {"id": "factory_renderer", "label": "Factory Renderer"},
        {"id": "browser_qa", "label": "Browser QA"},
        {"id": "client_workspace", "label": "Client Workspace"},
    ]
