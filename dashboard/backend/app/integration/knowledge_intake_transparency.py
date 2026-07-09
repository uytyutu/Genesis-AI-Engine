"""Knowledge Intake — Transparency slice.

User outcome: they understand what Vector can and cannot do with uploaded files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.attachment_policy import AttachmentPolicy, resolve_attachment_tier
from app.integration.feature_registry import FeatureRegistry
from app.integration.locale_service import localized_service_copy, resolve_locale


def transparency_enabled(memory_dir: Path | None = None) -> bool:
    return FeatureRegistry(memory_dir=memory_dir).is_enabled("attachment_transparency")


def analyzed_kinds(memory_dir: Path | None = None) -> list[str]:
    """Parse kinds currently available for this deployment (feature flags + policy)."""
    if not transparency_enabled(memory_dir):
        return []
    policy = AttachmentPolicy(memory_dir=memory_dir)
    tier = resolve_attachment_tier()
    limits = policy.limits_for(tier)
    out: list[str] = []
    for kind in sorted(limits.parse_kinds_allowed):
        mime = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt_csv": "text/plain",
            "vision": "image/png",
            "audio": "audio/mpeg",
            "zip": "application/zip",
        }.get(kind, kind)
        if policy.check_parse(tier=tier, content_type=mime).allowed:
            out.append(kind)
    return out


def upload_policy_snapshot(
    memory_dir: Path | None = None,
    *,
    visitor_id: str | None = None,
) -> dict[str, Any]:
    tier = resolve_attachment_tier(visitor_id=visitor_id)
    policy = AttachmentPolicy(memory_dir=memory_dir)
    limits = policy.limits_for(tier)
    return {
        "transparency_enabled": transparency_enabled(memory_dir),
        "tier": tier,
        "upload": {
            "max_file_bytes": limits.max_file_bytes,
            "max_files_per_message": limits.max_files_per_message,
            "max_uploads_per_day": limits.max_uploads_per_day,
            "accepted": sorted(limits.allowed_upload_mimes),
        },
        "analyze": {
            "available_kinds": analyzed_kinds(memory_dir),
            "stored_only": not analyzed_kinds(memory_dir),
        },
    }


def build_brain_attachment_note(
    files: list[dict[str, Any]],
    *,
    memory_dir: Path | None = None,
    locale: str | None = None,
) -> str:
    """Internal note for Brain — never claim content was read unless parse succeeded."""
    if not files:
        return ""
    loc = resolve_locale(locale)
    if not transparency_enabled(memory_dir):
        lines = [f"• {f.get('filename', 'file')} ({f.get('content_type', '')})" for f in files]
        return localized_service_copy("attachment_brain_legacy", loc) + "\n" + "\n".join(lines)

    policy = AttachmentPolicy(memory_dir=memory_dir)
    tier = resolve_attachment_tier()
    parsed_any = False
    file_lines: list[str] = []
    for f in files:
        ctype = str(f.get("content_type") or "")
        name = str(f.get("filename") or "file")
        parse = policy.check_parse(tier=tier, content_type=ctype)
        if parse.allowed and f.get("parsed_excerpt"):
            parsed_any = True
            file_lines.append(f"• {name} — {localized_service_copy('attachment_brain_parsed', loc)}")
        else:
            file_lines.append(f"• {name} ({ctype}) — {localized_service_copy('attachment_brain_stored_only', loc)}")

    header = localized_service_copy(
        "attachment_brain_parsed_header" if parsed_any else "attachment_brain_stored_header",
        loc,
    )
    return header + "\n" + "\n".join(file_lines)


def build_user_attachment_ack(
    files: list[dict[str, Any]],
    *,
    memory_dir: Path | None = None,
    locale: str | None = None,
) -> str:
    if not files or not transparency_enabled(memory_dir):
        return localized_service_copy("attachment_ack", locale) if files else ""

    loc = resolve_locale(locale)
    names = ", ".join(str(f.get("filename") or "file") for f in files[:3])
    if len(files) > 3:
        names += "…"
    policy = AttachmentPolicy(memory_dir=memory_dir)
    tier = resolve_attachment_tier()
    any_parse = any(
        policy.check_parse(tier=tier, content_type=str(f.get("content_type") or "")).allowed
        and f.get("parsed_excerpt")
        for f in files
    )
    if any_parse:
        return localized_service_copy("attachment_ack_parsed", loc).replace("{{files}}", names)
    return localized_service_copy("attachment_ack_stored_only", loc).replace("{{files}}", names)
