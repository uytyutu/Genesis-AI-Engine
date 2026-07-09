"""Attachment policy — tier limits for upload and parse (Foundation).

Mission 1: all public visitors resolve to tier ``free``.
Parse capabilities require FeatureRegistry flags (all off by default).

Enforcement wiring happens in Transparency / AI-1 slices — this module is the
single source of limits, not a second quota system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AttachmentTier = Literal["free", "studio", "business", "enterprise"]
ParseKind = Literal["pdf", "docx", "txt_csv", "vision", "audio", "zip"]

# MIME groups — aligned with public_chat_attachments._ALLOWED (subset per tier).
_MIME_IMAGES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
_MIME_PDF = frozenset({"application/pdf"})
_MIME_DOCX = frozenset(
    {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)
_MIME_TXT = frozenset({"text/plain", "text/csv"})
_MIME_AUDIO = frozenset({"audio/mpeg", "audio/wav", "audio/webm", "audio/ogg"})
_MIME_ZIP = frozenset({"application/zip", "application/x-zip-compressed"})

_PARSE_KIND_FEATURE: dict[ParseKind, str] = {
    "pdf": "attachment_pdf",
    "docx": "attachment_docx",
    "txt_csv": "attachment_txt_csv",
    "vision": "attachment_vision",
    "audio": "attachment_audio",
    "zip": "attachment_zip",
}

_PARSE_KIND_MIMES: dict[ParseKind, frozenset[str]] = {
    "pdf": _MIME_PDF,
    "docx": _MIME_DOCX,
    "txt_csv": _MIME_TXT,
    "vision": _MIME_IMAGES,
    "audio": _MIME_AUDIO,
    "zip": _MIME_ZIP,
}


@dataclass(frozen=True)
class TierLimits:
    tier: AttachmentTier
    label: str
    upload_enabled: bool
    max_file_bytes: int
    max_files_per_message: int
    max_uploads_per_day: int
    max_parsed_documents_per_day: int
    max_parsed_pages_per_day: int
    allowed_upload_mimes: frozenset[str]
    parse_kinds_allowed: frozenset[ParseKind]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "label": self.label,
            "upload_enabled": self.upload_enabled,
            "max_file_bytes": self.max_file_bytes,
            "max_files_per_message": self.max_files_per_message,
            "max_uploads_per_day": self.max_uploads_per_day,
            "max_parsed_documents_per_day": self.max_parsed_documents_per_day,
            "max_parsed_pages_per_day": self.max_parsed_pages_per_day,
            "allowed_upload_mimes": sorted(self.allowed_upload_mimes),
            "parse_kinds_allowed": sorted(self.parse_kinds_allowed),
        }


# Conservative defaults — CEO can tune via future memory/attachment_policy.json.
TIER_LIMITS: dict[AttachmentTier, TierLimits] = {
    "free": TierLimits(
        tier="free",
        label="Free · /site chat",
        upload_enabled=True,
        max_file_bytes=4 * 1024 * 1024,
        max_files_per_message=2,
        max_uploads_per_day=10,
        max_parsed_documents_per_day=1,
        max_parsed_pages_per_day=5,
        allowed_upload_mimes=_MIME_IMAGES | _MIME_PDF | _MIME_DOCX,
        parse_kinds_allowed=frozenset({"pdf"}),
    ),
    "studio": TierLimits(
        tier="studio",
        label="Virtus Studio (future)",
        upload_enabled=True,
        max_file_bytes=8 * 1024 * 1024,
        max_files_per_message=5,
        max_uploads_per_day=40,
        max_parsed_documents_per_day=20,
        max_parsed_pages_per_day=50,
        allowed_upload_mimes=_MIME_IMAGES | _MIME_PDF | _MIME_DOCX | _MIME_TXT,
        parse_kinds_allowed=frozenset({"pdf", "docx", "txt_csv", "vision"}),
    ),
    "business": TierLimits(
        tier="business",
        label="Business (future)",
        upload_enabled=True,
        max_file_bytes=16 * 1024 * 1024,
        max_files_per_message=10,
        max_uploads_per_day=120,
        max_parsed_documents_per_day=80,
        max_parsed_pages_per_day=200,
        allowed_upload_mimes=(
            _MIME_IMAGES | _MIME_PDF | _MIME_DOCX | _MIME_TXT | _MIME_AUDIO | _MIME_ZIP
        ),
        parse_kinds_allowed=frozenset({"pdf", "docx", "txt_csv", "vision", "audio", "zip"}),
    ),
    "enterprise": TierLimits(
        tier="enterprise",
        label="Enterprise (future)",
        upload_enabled=True,
        max_file_bytes=32 * 1024 * 1024,
        max_files_per_message=20,
        max_uploads_per_day=500,
        max_parsed_documents_per_day=500,
        max_parsed_pages_per_day=1000,
        allowed_upload_mimes=(
            _MIME_IMAGES | _MIME_PDF | _MIME_DOCX | _MIME_TXT | _MIME_AUDIO | _MIME_ZIP
        ),
        parse_kinds_allowed=frozenset({"pdf", "docx", "txt_csv", "vision", "audio", "zip"}),
    ),
}


@dataclass(frozen=True)
class UploadCheckResult:
    allowed: bool
    reason: str = ""
    tier: AttachmentTier = "free"
    limits: TierLimits | None = None


@dataclass(frozen=True)
class ParseCheckResult:
    allowed: bool
    parse_kind: ParseKind | None = None
    reason: str = ""
    feature_id: str = ""


def resolve_attachment_tier(
    *,
    visitor_id: str | None = None,
    subscription_tier: AttachmentTier | None = None,
) -> AttachmentTier:
    """Mission 1: everyone on /site is free. Studio/Business when subscriptions ship."""
    _ = visitor_id
    if subscription_tier and subscription_tier in TIER_LIMITS:
        return subscription_tier
    return "free"


def mime_to_parse_kind(content_type: str) -> ParseKind | None:
    mime = (content_type or "").split(";")[0].strip().lower()
    for kind, mimes in _PARSE_KIND_MIMES.items():
        if mime in mimes:
            return kind
    return None


class AttachmentPolicy:
    """Tier limits + feature-flag gate for parse (read-only checks until wired)."""

    def __init__(self, memory_dir=None) -> None:
        from pathlib import Path

        from app.integration.feature_registry import FeatureRegistry

        self._memory_dir = memory_dir
        self._features = FeatureRegistry(memory_dir=memory_dir if isinstance(memory_dir, Path) else None)

    def limits_for(self, tier: AttachmentTier) -> TierLimits:
        return TIER_LIMITS[tier]

    def check_upload(
        self,
        *,
        tier: AttachmentTier,
        content_type: str,
        size_bytes: int,
        files_in_message: int = 1,
        uploads_today: int = 0,
    ) -> UploadCheckResult:
        limits = self.limits_for(tier)
        if not limits.upload_enabled:
            return UploadCheckResult(False, "uploads disabled for this tier", tier, limits)
        mime = (content_type or "").split(";")[0].strip().lower()
        if mime not in limits.allowed_upload_mimes:
            return UploadCheckResult(
                False,
                f"file type not allowed on {tier} tier",
                tier,
                limits,
            )
        if size_bytes > limits.max_file_bytes:
            return UploadCheckResult(
                False,
                f"file too large (max {limits.max_file_bytes // (1024 * 1024)} MB on {tier})",
                tier,
                limits,
            )
        if files_in_message > limits.max_files_per_message:
            return UploadCheckResult(
                False,
                f"max {limits.max_files_per_message} files per message on {tier}",
                tier,
                limits,
            )
        if uploads_today >= limits.max_uploads_per_day:
            return UploadCheckResult(
                False,
                f"daily upload limit reached ({limits.max_uploads_per_day})",
                tier,
                limits,
            )
        return UploadCheckResult(True, tier=tier, limits=limits)

    def check_parse(self, *, tier: AttachmentTier, content_type: str) -> ParseCheckResult:
        kind = mime_to_parse_kind(content_type)
        if not kind:
            return ParseCheckResult(False, reason="unsupported mime for parse")
        limits = self.limits_for(tier)
        if kind not in limits.parse_kinds_allowed:
            return ParseCheckResult(
                False,
                parse_kind=kind,
                reason=f"{kind} parse not included in {tier} tier",
            )
        feature_id = _PARSE_KIND_FEATURE[kind]
        if not self._features.is_enabled(feature_id):
            return ParseCheckResult(
                False,
                parse_kind=kind,
                reason=f"{feature_id} not enabled",
                feature_id=feature_id,
            )
        return ParseCheckResult(True, parse_kind=kind, feature_id=feature_id)

    def snapshot(self, *, visitor_id: str | None = None) -> dict[str, Any]:
        tier = resolve_attachment_tier(visitor_id=visitor_id)
        limits = self.limits_for(tier)
        return {
            "tier": tier,
            "limits": limits.to_dict(),
            "parse_features": {
                fid: self._features.is_enabled(fid)
                for fid in _PARSE_KIND_FEATURE.values()
            },
            "transparency_enabled": self._features.is_enabled("attachment_transparency"),
        }
