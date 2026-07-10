"""Stable Release v3 — history, rollback, release notes, CEO display."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from launcher.deps import frontend_build_integrity, frontend_build_ready, frontend_build_stale
from launcher.log_util import append_log
from launcher.paths import find_project_root, frontend_dir, memory_dir

ReleaseStatus = Literal["development", "candidate", "stable_release", "rollback_available"]

STATUS_DEVELOPMENT = "development"
STATUS_CANDIDATE = "candidate"
STATUS_STABLE_RELEASE = "stable_release"
STATUS_ROLLBACK_AVAILABLE = "rollback_available"

STATUS_LABELS = {
    STATUS_DEVELOPMENT: "Development",
    STATUS_CANDIDATE: "Candidate",
    STATUS_STABLE_RELEASE: "Stable Release",
    STATUS_ROLLBACK_AVAILABLE: "Rollback Available",
}


@dataclass
class ReleaseRecord:
    release_id: str
    label: str
    title: str
    git_commit: str
    build_id: str
    version: str
    product_blocks: list[str] = field(default_factory=list)
    approved_by: str = "CEO PASS"
    activated_at: str = ""
    superseded_at: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ReleaseRecord:
        blocks = data.get("product_blocks") or []
        if isinstance(blocks, str):
            blocks = [b.strip() for b in blocks.split(",") if b.strip()]
        return cls(
            release_id=str(data.get("release_id") or ""),
            label=str(data.get("label") or ""),
            title=str(data.get("title") or ""),
            git_commit=str(data.get("git_commit") or ""),
            build_id=str(data.get("build_id") or ""),
            version=str(data.get("version") or ""),
            product_blocks=list(blocks),
            approved_by=str(data.get("approved_by") or "CEO PASS"),
            activated_at=str(data.get("activated_at") or ""),
            superseded_at=str(data.get("superseded_at") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "release_id": self.release_id,
            "label": self.label,
            "title": self.title,
            "git_commit": self.git_commit,
            "build_id": self.build_id,
            "version": self.version,
            "product_blocks": self.product_blocks,
            "approved_by": self.approved_by,
            "activated_at": self.activated_at,
            "superseded_at": self.superseded_at,
        }


def manifest_path(root: Path | None = None) -> Path:
    return memory_dir(root) / "stable_release.json"


def history_path(root: Path | None = None) -> Path:
    return memory_dir(root) / "stable_release_history.json"


def display_path(root: Path | None = None) -> Path:
    return memory_dir(root) / "stable_release_display.json"


def releases_root(root: Path | None = None) -> Path:
    return memory_dir(root) / "stable_releases"


def snapshot_dir(root: Path | None = None) -> Path:
    return releases_root(root) / "current"


def archive_dir(release_id: str, root: Path | None = None) -> Path:
    return releases_root(root) / "archives" / release_id


def read_build_id(root: Path | None = None) -> str | None:
    path = frontend_dir(root) / ".next" / "BUILD_ID"
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def read_git_commit_short(root: Path | None = None) -> str:
    try:
        repo = find_project_root(root)
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def read_active_release(root: Path | None = None) -> ReleaseRecord | None:
    path = manifest_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not data.get("release_id") and not data.get("build_id"):
        # migrate v2 manifest
        if data.get("build_id"):
            data["release_id"] = data.get("build_id", "")[:12] or "legacy"
            data.setdefault("title", data.get("label", ""))
            data.setdefault("git_commit", "")
            data.setdefault("version", "")
            data.setdefault("product_blocks", [])
        else:
            return None
    return ReleaseRecord.from_dict(data)


def read_release_history(root: Path | None = None) -> list[ReleaseRecord]:
    path = history_path(root)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = data if isinstance(data, list) else data.get("releases") or []
    return [ReleaseRecord.from_dict(item) for item in items if isinstance(item, dict)]


def write_release_history(records: list[ReleaseRecord], root: Path | None = None) -> None:
    path = history_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([r.to_dict() for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def release_snapshot_ready(root: Path | None = None, *, release_id: str | None = None) -> bool:
    snap = archive_dir(release_id, root) if release_id else snapshot_dir(root)
    return (snap / "BUILD_ID").is_file() and (snap / "routes-manifest.json").is_file()


def working_matches_active_release(root: Path | None = None) -> bool:
    release = read_active_release(root)
    if release is None:
        return False
    if not frontend_build_integrity(root):
        return False
    return read_build_id(root) == release.build_id


def _copy_next_snapshot(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _archive_release_snapshot(release_id: str, source: Path, root: Path | None) -> None:
    dest = archive_dir(release_id, root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _copy_next_snapshot(source, dest)


def _deploy_snapshot_to_working(release_id: str | None, root: Path | None) -> tuple[bool, str]:
    snap = archive_dir(release_id, root) if release_id else snapshot_dir(root)
    if not release_snapshot_ready(root, release_id=release_id):
        return False, "снимок релиза недоступен"
    target = frontend_dir(root) / ".next"
    _copy_next_snapshot(snap, target)
    if release_id:
        _copy_next_snapshot(snap, snapshot_dir(root))
    return True, "ok"


def compute_release_status(root: Path | None = None) -> dict:
    """Four launcher states — CEO always sees where the product is."""
    active = read_active_release(root)
    history = read_release_history(root)
    rollback_ready = bool(
        active
        and history
        and any(h.release_id != active.release_id and release_snapshot_ready(root, release_id=h.release_id) for h in history)
    )

    if active and working_matches_active_release(root):
        status = STATUS_ROLLBACK_AVAILABLE if rollback_ready else STATUS_STABLE_RELEASE
        return {
            "status": status,
            "status_label": STATUS_LABELS[status],
            "rollback_available": rollback_ready,
        }

    if frontend_build_integrity(root) and (active is None or frontend_build_stale(root)):
        return {
            "status": STATUS_CANDIDATE,
            "status_label": STATUS_LABELS[STATUS_CANDIDATE],
            "rollback_available": rollback_ready,
        }

    return {
        "status": STATUS_DEVELOPMENT,
        "status_label": STATUS_LABELS[STATUS_DEVELOPMENT],
        "rollback_available": rollback_ready,
    }


def build_display_payload(root: Path | None = None) -> dict:
    active = read_active_release(root)
    history = read_release_history(root)
    status = compute_release_status(root)
    activated_display = ""
    if active and active.activated_at:
        try:
            dt = datetime.fromisoformat(active.activated_at.replace("Z", "+00:00"))
            activated_display = dt.astimezone().strftime("%d.%m.%Y")
        except ValueError:
            activated_display = active.activated_at[:10]

    return {
        "brand": "Virtus Core",
        "stable_release": {
            "active": active.to_dict() if active else None,
            "label": active.label if active else None,
            "title": active.title if active else None,
            "git_commit": active.git_commit if active else None,
            "build_id": active.build_id if active else None,
            "activated_display": activated_display,
            "approved_by": active.approved_by if active else None,
            "product_blocks": active.product_blocks if active else [],
        },
        "history": [
            {
                "label": r.label,
                "title": r.title,
                "git_commit": r.git_commit,
                "activated_at": r.activated_at,
                "release_id": r.release_id,
            }
            for r in history[:12]
        ],
        "release_status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_display_payload(root: Path | None = None) -> Path:
    payload = build_display_payload(root)
    path = display_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_display_payload(root: Path | None = None) -> dict:
    path = display_path(root)
    if not path.is_file():
        return build_display_payload(root)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return build_display_payload(root)


def activate_stable_release(
    root: Path | None = None,
    *,
    label: str | None = None,
    title: str = "",
    version: str = "",
    product_blocks: list[str] | None = None,
    approved_by: str = "CEO PASS",
) -> tuple[bool, str]:
    """Development → Build → Tests → CEO PASS → Activate Stable Release."""
    if not frontend_build_integrity(root):
        return False, "Нельзя активировать релиз — production не готов."

    build_id = read_build_id(root)
    if not build_id:
        return False, "BUILD_ID не найден — сначала сборка в режиме «Разработка»."

    stamp = datetime.now(timezone.utc)
    release_label = label or stamp.astimezone().strftime("%Y.%m.%d")
    release_id = f"rel-{stamp.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    git_commit = read_git_commit_short(root)
    source = frontend_dir(root) / ".next"

    current = read_active_release(root)
    history = read_release_history(root)

    if current:
        current.superseded_at = stamp.isoformat()
        if release_snapshot_ready(root):
            _archive_release_snapshot(current.release_id, snapshot_dir(root), root)
        history.insert(0, current)

    _archive_release_snapshot(release_id, source, root)
    _copy_next_snapshot(source, snapshot_dir(root))

    record = ReleaseRecord(
        release_id=release_id,
        label=release_label,
        title=title or release_label,
        git_commit=git_commit,
        build_id=build_id,
        version=version,
        product_blocks=product_blocks or [],
        approved_by=approved_by,
        activated_at=stamp.isoformat(),
    )
    manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
    manifest_path(root).write_text(
        json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_release_history(history, root)
    write_display_payload(root)
    append_log(
        f"Stable Release activated: {release_label} · {title} · commit={git_commit} · build={build_id}"
    )
    return True, f"Стабильный релиз {release_label} активирован"


def rollback_to_previous_release(root: Path | None = None) -> tuple[bool, str]:
    """Rollback — switch active release only; dev source tree untouched."""
    active = read_active_release(root)
    history = read_release_history(root)
    if not history:
        return False, "История релизов пуста — откат невозможен."

    previous = None
    for entry in history:
        if active and entry.release_id == active.release_id:
            continue
        if release_snapshot_ready(root, release_id=entry.release_id):
            previous = entry
            break

    if previous is None:
        return False, "Предыдущий стабильный релиз недоступен (снимок отсутствует)."

    ok, detail = _deploy_snapshot_to_working(previous.release_id, root)
    if not ok:
        return False, f"Не удалось развернуть релиз: {detail}"

    if active and release_snapshot_ready(root):
        _archive_release_snapshot(active.release_id, snapshot_dir(root), root)
        active.superseded_at = datetime.now(timezone.utc).isoformat()
        if not any(h.release_id == active.release_id for h in history):
            history.insert(0, active)

    manifest_path(root).write_text(
        json.dumps(previous.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_release_history(history, root)
    write_display_payload(root)
    append_log(f"Rollback to Stable Release: {previous.label} · {previous.title}")
    return True, f"Откат на релиз {previous.label} — {previous.title}"


def restore_active_release(root: Path | None = None) -> tuple[bool, str]:
    release = read_active_release(root)
    if release is None:
        return False, "Активный стабильный релиз не зарегистрирован."
    ok, detail = _deploy_snapshot_to_working(release.release_id, root)
    if not ok:
        ok2, detail2 = _deploy_snapshot_to_working(None, root)
        if not ok2:
            return False, detail2
    write_display_payload(root)
    append_log(f"Stable Release restored: {release.label}")
    return True, f"Восстановлен стабильный релиз {release.label}"


def ensure_active_release_deployed(root: Path | None = None) -> tuple[bool, str]:
    release = read_active_release(root)
    if release is None:
        if frontend_build_integrity(root):
            write_display_payload(root)
            return True, "рабочая сборка (релиз ещё не активирован)"
        return False, "стабильный релиз не активирован"

    if working_matches_active_release(root):
        write_display_payload(root)
        return True, f"стабильный релиз {release.label}"

    if release_snapshot_ready(root, release_id=release.release_id):
        ok, msg = _deploy_snapshot_to_working(release.release_id, root)
        if ok:
            write_display_payload(root)
            return True, f"развёрнут релиз {release.label}"
        return False, msg

    return restore_active_release(root)


def release_label_for_ui(root: Path | None = None) -> str:
    release = read_active_release(root)
    if release and release.label:
        return release.label
    return "не активирован"


def format_release_info_lines(root: Path | None = None) -> list[str]:
    """Launcher / CEO panel — human-readable release block."""
    active = read_active_release(root)
    status = compute_release_status(root)
    lines = [f"Статус продукта: {status['status_label']}"]
    if not active:
        lines.append("Stable Release: не активирован")
        return lines

    activated = ""
    if active.activated_at:
        try:
            dt = datetime.fromisoformat(active.activated_at.replace("Z", "+00:00"))
            activated = dt.astimezone().strftime("%d.%m.%Y")
        except ValueError:
            activated = active.activated_at[:10]

    lines.extend(
        [
            "",
            "Virtus Core",
            "Stable Release",
            active.label,
            f"Build {active.git_commit or (active.build_id[:12] if active.build_id else '—')}",
        ]
    )
    if activated:
        lines.append(f"Activated {activated}")
    if active.title:
        lines.append(active.title)
    if status.get("rollback_available"):
        lines.append("")
        lines.append("↩ Rollback Available")
    return lines


def format_history_lines(root: Path | None = None, *, limit: int = 5) -> list[str]:
    history = read_release_history(root)
    if not history:
        return ["История релизов пуста"]
    lines: list[str] = []
    for entry in history[:limit]:
        title = entry.title or entry.label
        lines.append(f"{entry.label} — {title}")
    return lines

