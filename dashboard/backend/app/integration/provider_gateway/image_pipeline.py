"""Image Provider Pipeline — Generate → Media QA → regenerate → hard failure.

P0 contract (Owner):
  - No export until Media QA PASS
  - FAIL → regenerate (max attempts, default 3)
  - Exhausted attempts → hard failure (never infinite / never Repair Loop)
  - Factory talks only to this pipeline / ProviderGateway — not raw OpenAI/FAL APIs
  - Credentials never appear in logs, frontend payloads, or ZIP

Live HTTP adapters land after RC1 PASS. Until then, inject a Generator for tests.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from app.integration.provider_gateway import Modality, ProviderGateway
from app.integration.provider_gateway.media_qa import MediaQaReport, run_image_media_qa

DEFAULT_MAX_ATTEMPTS = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ImageBrief:
    """Creative brief for one image slot — provider-agnostic."""

    project_id: str
    role: str = "hero"
    niche: str = ""
    prompt: str = ""
    prompt_version: str = "v1"
    width: int = 1920
    height: int = 1080
    fingerprint: str = ""


@dataclass
class GenerationAttempt:
    attempt: int
    provider_id: str | None
    model: str | None
    prompt_version: str
    qa_ok: bool
    qa_failure_reason: str | None
    status: str  # generated | qa_pass | qa_fail | provider_error | timeout | hard_failure
    detail: str = ""
    path: str | None = None
    at: str = field(default_factory=_now)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ImageGenerator(Protocol):
    """Adapter interface — concrete OpenAI/FAL classes implement this later."""

    def generate(self, brief: ImageBrief, *, out_path: Path, api_key: str) -> dict[str, Any]:
        """
        Write image to out_path. Return metadata:
          ok, model, path, error?, timeout?
        Must never echo api_key into return values.
        """
        ...


class ImagePipelineHardFailure(Exception):
    """All attempts exhausted or unrecoverable provider state — stop, do not Repair Loop."""

    def __init__(self, report: "ImagePipelineReport"):
        self.report = report
        super().__init__(report.failure_reason or "IMAGE_PIPELINE_HARD_FAILURE")


@dataclass
class ImagePipelineReport:
    ok: bool
    export_allowed: bool
    path: str | None
    provider_id: str | None
    attempts: list[GenerationAttempt] = field(default_factory=list)
    failure_reason: str | None = None
    qa: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "export_allowed": self.export_allowed,
            "path": self.path,
            "provider_id": self.provider_id,
            "failure_reason": self.failure_reason,
            "attempts": [a.as_dict() for a in self.attempts],
            "qa": self.qa,
            "max_attempts": DEFAULT_MAX_ATTEMPTS,
        }


def _redact(obj: Any) -> Any:
    """Strip accidental credential-looking fields from logged structures."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if any(x in lk for x in ("api_key", "apikey", "authorization", "secret", "token")):
                out[k] = "***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _append_log(log_path: Path | None, row: dict[str, Any]) -> None:
    if log_path is None:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_redact(row), ensure_ascii=False) + "\n")


def run_image_pipeline(
    *,
    gateway: ProviderGateway,
    brief: ImageBrief,
    out_path: Path,
    generator: ImageGenerator | None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    log_path: Path | None = None,
    known_fingerprints: set[str] | None = None,
    raise_on_hard_failure: bool = False,
) -> ImagePipelineReport:
    """
    Full P0 loop. If generator is None → clear FAIL (no live adapter) without spinning.
    """
    attempts: list[GenerationAttempt] = []
    selected = gateway.select_provider(Modality.IMAGE)
    if not selected.get("ok"):
        report = ImagePipelineReport(
            ok=False,
            export_allowed=False,
            path=None,
            provider_id=None,
            attempts=attempts,
            failure_reason="no_provider_connected",
        )
        _append_log(
            log_path,
            {
                "event": "hard_failure",
                "reason": "no_provider_connected",
                "project_id": brief.project_id,
                "at": _now(),
            },
        )
        if raise_on_hard_failure:
            raise ImagePipelineHardFailure(report)
        return report

    provider_id = str(selected["provider_id"])
    api_key = gateway.resolve_key(provider_id)
    if not api_key:
        report = ImagePipelineReport(
            ok=False,
            export_allowed=False,
            path=None,
            provider_id=provider_id,
            attempts=attempts,
            failure_reason="missing_api_key",
        )
        _append_log(
            log_path,
            {
                "event": "hard_failure",
                "reason": "missing_api_key",
                "provider_id": provider_id,
                "project_id": brief.project_id,
                "at": _now(),
            },
        )
        if raise_on_hard_failure:
            raise ImagePipelineHardFailure(report)
        return report

    if generator is None:
        report = ImagePipelineReport(
            ok=False,
            export_allowed=False,
            path=None,
            provider_id=provider_id,
            attempts=attempts,
            failure_reason="no_image_adapter",
        )
        _append_log(
            log_path,
            {
                "event": "hard_failure",
                "reason": "no_image_adapter",
                "provider_id": provider_id,
                "message": "Image adapter not wired — after RC1 PASS",
                "at": _now(),
            },
        )
        if raise_on_hard_failure:
            raise ImagePipelineHardFailure(report)
        return report

    last_qa: MediaQaReport | None = None
    limit = max(1, min(int(max_attempts), 5))

    for n in range(1, limit + 1):
        attempt_path = out_path if n == 1 else out_path.with_name(
            f"{out_path.stem}_try{n}{out_path.suffix}"
        )
        try:
            gen = generator.generate(brief, out_path=attempt_path, api_key=api_key)
        except TimeoutError as exc:
            row = GenerationAttempt(
                attempt=n,
                provider_id=provider_id,
                model=None,
                prompt_version=brief.prompt_version,
                qa_ok=False,
                qa_failure_reason="timeout",
                status="timeout",
                detail=str(exc)[:200],
            )
            attempts.append(row)
            _append_log(log_path, {"event": "attempt", **row.as_dict()})
            continue
        except Exception as exc:  # noqa: BLE001 — adapter boundary
            row = GenerationAttempt(
                attempt=n,
                provider_id=provider_id,
                model=None,
                prompt_version=brief.prompt_version,
                qa_ok=False,
                qa_failure_reason="provider_error",
                status="provider_error",
                detail=str(exc)[:200],
            )
            attempts.append(row)
            _append_log(log_path, {"event": "attempt", **row.as_dict()})
            continue

        if not gen.get("ok"):
            reason = str(gen.get("error") or "provider_error")
            if gen.get("timeout"):
                reason = "timeout"
            row = GenerationAttempt(
                attempt=n,
                provider_id=provider_id,
                model=str(gen.get("model") or "") or None,
                prompt_version=brief.prompt_version,
                qa_ok=False,
                qa_failure_reason=reason,
                status="timeout" if reason == "timeout" else "provider_error",
                detail=str(gen.get("message") or reason)[:200],
                path=str(gen.get("path") or attempt_path),
            )
            attempts.append(row)
            _append_log(log_path, {"event": "attempt", **row.as_dict()})
            continue

        written = Path(str(gen.get("path") or attempt_path))
        # Niche vision check is opt-in via brief metadata later; do not FAIL
        # solely because the filename omits the niche token (no vision model yet).
        qa = run_image_media_qa(
            written,
            role=brief.role,
            niche=brief.niche,
            duplicate_fingerprint=brief.fingerprint or None,
            known_fingerprints=known_fingerprints,
        )
        last_qa = qa
        if qa.ok:
            # Promote to canonical out_path
            if written.resolve() != out_path.resolve():
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(written.read_bytes())
            row = GenerationAttempt(
                attempt=n,
                provider_id=provider_id,
                model=str(gen.get("model") or "") or None,
                prompt_version=brief.prompt_version,
                qa_ok=True,
                qa_failure_reason=None,
                status="qa_pass",
                path=str(out_path),
            )
            attempts.append(row)
            _append_log(log_path, {"event": "attempt", **row.as_dict()})
            return ImagePipelineReport(
                ok=True,
                export_allowed=True,
                path=str(out_path),
                provider_id=provider_id,
                attempts=attempts,
                qa=qa.as_dict(),
            )

        row = GenerationAttempt(
            attempt=n,
            provider_id=provider_id,
            model=str(gen.get("model") or "") or None,
            prompt_version=brief.prompt_version,
            qa_ok=False,
            qa_failure_reason=qa.failure_reason,
            status="qa_fail",
            detail=qa.failure_reason or "qa_fail",
            path=str(written),
        )
        attempts.append(row)
        _append_log(log_path, {"event": "attempt", **row.as_dict()})

    report = ImagePipelineReport(
        ok=False,
        export_allowed=False,
        path=None,
        provider_id=provider_id,
        attempts=attempts,
        failure_reason="max_attempts_exhausted",
        qa=last_qa.as_dict() if last_qa else None,
    )
    _append_log(
        log_path,
        {
            "event": "hard_failure",
            "reason": "max_attempts_exhausted",
            "provider_id": provider_id,
            "attempts": len(attempts),
            "at": _now(),
        },
    )
    if raise_on_hard_failure:
        raise ImagePipelineHardFailure(report)
    return report
