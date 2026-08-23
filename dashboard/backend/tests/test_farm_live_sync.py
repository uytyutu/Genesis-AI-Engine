"""Live sync / auto confirmation — no CEO-typed Payment IDs."""

from __future__ import annotations

from swarm.farm_opire_sync import build_platform_confirmation, sync_task_from_platforms


def test_build_platform_confirmation_stable():
    a = build_platform_confirmation(
        opire_reward_id="abc",
        pr_number=12,
        merge_sha="deadbeefcafebabe",
        source="github_merge+opire",
    )
    assert a.startswith("virtus_auto:")
    assert "opire:abc" in a
    assert "pr:12" in a
    assert "sha:deadbeefcafe" in a


def test_sync_sets_auto_confirmation_on_merged(monkeypatch):
    import swarm.farm_opire_sync as sync

    monkeypatch.setattr(
        sync,
        "get_pull",
        lambda *a, **k: {
            "ok": True,
            "pr_number": 7,
            "pr_url": "https://github.com/acme/demo/pull/7",
            "state": "closed",
            "merged": True,
            "merge_sha": "abc1234567890",
            "draft": False,
        },
    )
    monkeypatch.setattr(sync, "find_opire_reward", lambda *_: None)

    task = {
        "id": "opire:rid-1",
        "native_id": "rid-1",
        "repository": "acme/demo",
        "pr_id": "7",
        "status": "pr_submitted",
    }
    out = sync_task_from_platforms(task)
    assert out["ok"] is True
    assert out["task"]["status"] == "payment_available"
    assert out["task"]["merge_sha"] == "abc1234567890"
    assert out["task"]["payment_confirmation_id"].startswith("virtus_auto:")
    assert "auto_confirmation_ready" in out["events"]


def test_ensure_farm_env_reads_keys_without_overwrite(monkeypatch, tmp_path):
    from swarm import farm_env_bootstrap as boot

    monkeypatch.setattr(boot, "_LOADED", False)
    env_file = tmp_path / ".env.local"
    env_file.write_text("GENESIS_GROQ_API_KEY=test-from-file\n", encoding="utf-8")
    monkeypatch.setattr(boot, "_candidate_env_files", lambda: [env_file])
    monkeypatch.delenv("GENESIS_GROQ_API_KEY", raising=False)
    found = boot.ensure_farm_env(force=True)
    assert found.get("GENESIS_GROQ_API_KEY") is True
    assert boot.os.environ.get("GENESIS_GROQ_API_KEY") == "test-from-file"
