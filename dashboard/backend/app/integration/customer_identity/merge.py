"""Merge anonymous visitor data into customer platform identity."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from app.integration.project_platform.service import bind_visitor_workspace


def _safe_id(raw: str, *, max_len: int = 64) -> str:
    return re.sub(r"[^\w\-]", "_", raw)[:max_len] or "anonymous"


def merge_visitor_identity(memory_dir: Path, *, from_visitor: str, to_visitor: str) -> dict[str, Any]:
    """Preserve pre-registration work: projects, memory, chats, uploads."""
    from_vid = (from_visitor or "").strip()[:64]
    to_vid = (to_visitor or "").strip()[:64]
    if not from_vid or not to_vid or from_vid == to_vid:
        return {"merged": False, "reason": "same_or_empty"}

    stats = {
        "workspace": False,
        "projects": 0,
        "brain_memory": False,
        "chat_sessions": 0,
        "attachments": 0,
    }

    stats["workspace"] = _merge_workspace_map(memory_dir, from_vid, to_vid)
    stats["projects"] = _merge_project_records(memory_dir, from_vid, to_vid)
    stats["brain_memory"] = _merge_brain_user_file(memory_dir, from_vid, to_vid)
    stats["chat_sessions"] = _merge_chat_sessions(memory_dir, from_vid, to_vid)
    stats["attachments"] = _merge_attachment_meta(memory_dir, from_vid, to_vid)

    return {"merged": True, "from": from_vid, "to": to_vid, "stats": stats}


def _merge_workspace_map(memory_dir: Path, from_vid: str, to_vid: str) -> bool:
    path = memory_dir / "execution" / "visitor_workspaces.json"
    if not path.is_file():
        return False
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if from_vid not in mapping:
        return False
    ws_id = mapping[from_vid]
    if to_vid not in mapping:
        mapping[to_vid] = ws_id
        bind_visitor_workspace(memory_dir, to_vid, ws_id)
    elif mapping.get(to_vid) != ws_id:
        bind_visitor_workspace(memory_dir, to_vid, mapping[to_vid])
    del mapping[from_vid]
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def _merge_project_records(memory_dir: Path, from_vid: str, to_vid: str) -> int:
    count = 0
    projects_root = memory_dir / "projects"
    if not projects_root.is_dir():
        return 0
    for proj in projects_root.glob("*/project.json"):
        try:
            data = json.loads(proj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("visitor_id") == from_vid:
            data["visitor_id"] = to_vid
            proj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            count += 1
    return count


def _merge_brain_user_file(memory_dir: Path, from_vid: str, to_vid: str) -> bool:
    root = memory_dir / "genesis_brain" / "users"
    from_path = root / f"{_safe_id(from_vid)}.json"
    to_path = root / f"{_safe_id(to_vid)}.json"
    if not from_path.is_file():
        return False
    if not to_path.is_file():
        shutil.move(str(from_path), str(to_path))
        try:
            data = json.loads(to_path.read_text(encoding="utf-8"))
            data["visitor_id"] = to_vid
            to_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass
        return True
    try:
        old = json.loads(from_path.read_text(encoding="utf-8"))
        cur = json.loads(to_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        from_path.unlink(missing_ok=True)
        return False
    for key in ("facts", "milestones", "exchanges"):
        if isinstance(old.get(key), list):
            cur.setdefault(key, [])
            if isinstance(cur[key], list):
                cur[key] = (cur[key] + old[key])[-50:]
    if not cur.get("name") and old.get("name"):
        cur["name"] = old["name"]
    cur["visit_count"] = int(cur.get("visit_count") or 0) + int(old.get("visit_count") or 0)
    to_path.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    from_path.unlink(missing_ok=True)
    return True


def _merge_chat_sessions(memory_dir: Path, from_vid: str, to_vid: str) -> int:
    sessions_dir = memory_dir / "genesis_brain" / "sessions"
    index_dir = memory_dir / "genesis_brain" / "session_index"
    from_index = index_dir / f"{_safe_id(from_vid)}.json"
    to_index = index_dir / f"{_safe_id(to_vid)}.json"
    if not from_index.is_file():
        return 0

    try:
        from_rows = json.loads(from_index.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    if not isinstance(from_rows, list):
        return 0

    to_rows: list[dict[str, Any]] = []
    if to_index.is_file():
        try:
            raw = json.loads(to_index.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                to_rows = [r for r in raw if isinstance(r, dict)]
        except (json.JSONDecodeError, OSError):
            to_rows = []

    merged_ids = {r.get("session_id") for r in to_rows}
    moved = 0
    for row in from_rows:
        if not isinstance(row, dict):
            continue
        sid = row.get("session_id")
        if sid and sid not in merged_ids:
            to_rows.append(row)
            merged_ids.add(sid)
        session_path = sessions_dir / f"{_safe_id(str(sid))}.json"
        if session_path.is_file():
            try:
                session = json.loads(session_path.read_text(encoding="utf-8"))
                session["visitor_id"] = to_vid
                session_path.write_text(
                    json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                moved += 1
            except (json.JSONDecodeError, OSError):
                continue

    to_index.write_text(json.dumps(to_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    from_index.unlink(missing_ok=True)
    return moved


def _merge_attachment_meta(memory_dir: Path, from_vid: str, to_vid: str) -> int:
    meta_path = memory_dir / "public_chat_uploads" / "index.json"
    if not meta_path.is_file():
        return 0
    try:
        items = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    if not isinstance(items, list):
        return 0
    count = 0
    for m in items:
        if isinstance(m, dict) and m.get("visitor_id") == _safe_id(from_vid):
            m["visitor_id"] = _safe_id(to_vid)
            count += 1
    if count:
        meta_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    from_quota = memory_dir / "public_chat_uploads" / "upload_quotas" / f"{_safe_id(from_vid)}.json"
    to_quota = memory_dir / "public_chat_uploads" / "upload_quotas" / f"{_safe_id(to_vid)}.json"
    if from_quota.is_file() and not to_quota.is_file():
        shutil.move(str(from_quota), str(to_quota))
    return count
