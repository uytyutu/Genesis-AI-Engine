"""Foundation — Product Completion feature registry.

Single place to declare future platform capabilities (Workspace, Specialists, …).
All product-completion features default to **disabled** — no public behaviour change.

Optional CEO override via memory/platform_features.json (not shipped by default).
Env override: GENESIS_FEATURE_<ID>=true (internal testing only).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

FeatureLayer = Literal[
    "workspace",
    "co_creation",
    "specialists",
    "subscriptions",
    "marketplace",
    "business_automation",
    "device_continuity",
    "trust_experience",
    "attachment_intelligence",
    "knowledge_intake",
]

REGISTRY_VERSION = "foundation-features-2"

# Product Completion layers — enabled=False until Foundation + CEO gate.
_PRODUCT_FEATURES: dict[str, dict[str, Any]] = {
    "workspace": {
        "label": "Customer Workspace",
        "layer": "workspace",
        "exists": True,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "Shell in docs/VIRTUS_WORKSPACE_ARCHITECTURE_DIRECTIVE.md; no customer UI",
    },
    "co_creation": {
        "label": "Co-Creation / Live Preview",
        "layer": "co_creation",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "Vision only — requires Workspace + tenant routing",
    },
    "specialists": {
        "label": "Specialists / Project Director",
        "layer": "specialists",
        "exists": True,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "LLM workforce infra exists; product roles not shipped",
    },
    "subscriptions": {
        "label": "Paid Subscriptions / Studio",
        "layer": "subscriptions",
        "exists": True,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "Stripe one-time only; Studio blocked in truth catalog",
    },
    "marketplace": {
        "label": "Skills Marketplace",
        "layer": "marketplace",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "docs/SKILLS_PLATFORM.md — architecture only",
    },
    "business_automation": {
        "label": "Business Automation",
        "layer": "business_automation",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "Horizon — after EL3+",
    },
    "device_continuity": {
        "label": "Device Continuity / Updates",
        "layer": "device_continuity",
        "exists": True,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "Launcher manual; Tauri updater stub only",
    },
    "trust_experience": {
        "label": "Trust Experience (Human Test layer)",
        "layer": "trust_experience",
        "exists": True,
        "stable": True,
        "ready": True,
        "enabled": False,
        "notes": "Truth Pass Stages 1–2 done; CEO Verification+ pending",
    },
    # Knowledge Intake — attachment modules first; URL/GitHub/Notion plug into knowledge_intake.py.
    "attachment_transparency": {
        "label": "Knowledge Intake — Transparency (honest UX)",
        "layer": "knowledge_intake",
        "exists": True,
        "stable": True,
        "ready": True,
        "enabled": True,
        "notes": "Honest tooltips + attachment_ack; no false «вижу содержимое»",
    },
    "attachment_pdf": {
        "label": "Parse PDF → text → Brain",
        "layer": "knowledge_intake",
        "exists": True,
        "stable": True,
        "ready": True,
        "enabled": True,
        "notes": "AI-1 — free tier: 1 PDF/day, 5 pages; session follow-up",
    },
    "knowledge_expert_review": {
        "label": "Knowledge Reasoning — Expert Review",
        "layer": "knowledge_intake",
        "exists": True,
        "stable": True,
        "ready": True,
        "enabled": True,
        "notes": "Intent → expert hat → document quality review (source-agnostic)",
    },
    "attachment_docx": {
        "label": "Parse DOCX → text → Brain",
        "layer": "knowledge_intake",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "AI-2",
    },
    "attachment_txt_csv": {
        "label": "Parse TXT/CSV → Brain",
        "layer": "knowledge_intake",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "AI-3",
    },
    "attachment_vision": {
        "label": "Image analysis via vision provider",
        "layer": "knowledge_intake",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "AI-4 — studio+ tier in attachment_policy",
    },
    "attachment_audio": {
        "label": "Audio file → STT → Brain",
        "layer": "knowledge_intake",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "AI-5 — distinct from browser mic STT",
    },
    "attachment_zip": {
        "label": "ZIP unpack → selective parse",
        "layer": "knowledge_intake",
        "exists": False,
        "stable": False,
        "ready": False,
        "enabled": False,
        "notes": "AI-6 — business+ tier",
    },
}


@dataclass(frozen=True)
class FeatureEntry:
    id: str
    label: str
    layer: FeatureLayer
    exists: bool
    stable: bool
    ready: bool
    enabled: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_override(feature_id: str) -> bool | None:
    key = f"GENESIS_FEATURE_{feature_id.upper()}"
    raw = os.getenv(key, "").strip().lower()
    if not raw:
        return None
    return raw in ("1", "true", "yes", "on")


class FeatureRegistry:
    """Product Completion features — all off unless explicitly overridden."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir
        self._overrides = self._load_memory_overrides()

    def _config_path(self) -> Path | None:
        if not self._memory_dir:
            return None
        return self._memory_dir / "platform_features.json"

    def _load_memory_overrides(self) -> dict[str, bool]:
        path = self._config_path()
        if not path or not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        features = data.get("features") if isinstance(data, dict) else None
        if not isinstance(features, dict):
            return {}
        return {str(k): bool(v) for k, v in features.items()}

    def list_features(self) -> list[FeatureEntry]:
        out: list[FeatureEntry] = []
        for fid, meta in _PRODUCT_FEATURES.items():
            default_enabled = bool(meta.get("enabled"))
            enabled = default_enabled
            if fid in self._overrides:
                enabled = self._overrides[fid]
            else:
                env = _env_override(fid)
                if env is not None:
                    enabled = env
            out.append(
                FeatureEntry(
                    id=fid,
                    label=str(meta.get("label") or fid),
                    layer=meta["layer"],
                    exists=bool(meta.get("exists")),
                    stable=bool(meta.get("stable")),
                    ready=bool(meta.get("ready")),
                    enabled=enabled,
                    notes=str(meta.get("notes") or ""),
                )
            )
        return out

    def is_enabled(self, feature_id: str) -> bool:
        row = self.get(feature_id)
        return bool(row and row.enabled)

    def get(self, feature_id: str) -> FeatureEntry | None:
        for row in self.list_features():
            if row.id == feature_id:
                return row
        return None

    def snapshot(self) -> dict[str, Any]:
        features = self.list_features()
        enabled = [f for f in features if f.enabled]
        return {
            "version": REGISTRY_VERSION,
            "generated_at": _utc_now(),
            "summary": {
                "total": len(features),
                "enabled": len(enabled),
                "any_product_feature_enabled": any(
                    f.enabled
                    for f in features
                    if f.layer
                    in (
                        "workspace",
                        "co_creation",
                        "specialists",
                        "subscriptions",
                        "marketplace",
                        "business_automation",
                        "device_continuity",
                    )
                ),
            },
            "features": [f.to_dict() for f in features],
        }
