"""Tests for visitor → customer merge."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.customer_identity.merge import merge_visitor_identity
from app.integration.project_platform.service import bind_visitor_workspace


def test_merge_preserves_workspace_and_memory(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()

    from_vid = "anon-visitor-abcdef12"
    to_vid = "vc-customer1234567890abcdef12345678"

    ws_dir = memory / "execution"
    ws_dir.mkdir(parents=True)
    (ws_dir / "visitor_workspaces.json").write_text(
        json.dumps({from_vid: "ws-merge-1"}), encoding="utf-8"
    )

    projects = memory / "projects" / "ws-merge-1"
    projects.mkdir(parents=True)
    (projects / "project.json").write_text(
        json.dumps({"visitor_id": from_vid, "title": "Кафе"}),
        encoding="utf-8",
    )

    users = memory / "genesis_brain" / "users"
    users.mkdir(parents=True)
    (users / f"{from_vid}.json").write_text(
        json.dumps({"visitor_id": from_vid, "facts": ["любит кофе"]}),
        encoding="utf-8",
    )

    result = merge_visitor_identity(memory, from_visitor=from_vid, to_visitor=to_vid)
    assert result["merged"] is True
    assert result["stats"]["workspace"] is True
    assert result["stats"]["projects"] == 1
    assert result["stats"]["brain_memory"] is True

    mapping = json.loads((ws_dir / "visitor_workspaces.json").read_text(encoding="utf-8"))
    assert from_vid not in mapping
    assert mapping[to_vid] == "ws-merge-1"

    proj = json.loads((projects / "project.json").read_text(encoding="utf-8"))
    assert proj["visitor_id"] == to_vid

    brain = json.loads((users / f"{to_vid}.json").read_text(encoding="utf-8"))
    assert brain["facts"] == ["любит кофе"]
