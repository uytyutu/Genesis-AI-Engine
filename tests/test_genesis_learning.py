"""Genesis Learning knowledge base tests."""

from launcher.genesis_learning import (
    LearningIncident,
    find_similar,
    load_kb,
    record_incident,
)


def test_record_and_find_similar(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "launcher.genesis_learning.paths.memory_dir",
        lambda root=None: tmp_path,
    )
    monkeypatch.setattr("launcher.genesis_learning._seed_kb_if_needed", lambda root=None: None)
    inc = LearningIncident(
        id="test-ctkimage",
        symptom="Не удалось запустить Genesis",
        root_cause="CTkImage str path",
        fix="PIL.Image.open",
        files=["launcher/app.py"],
        date="2026-07-04",
        version="0.5.0",
        verify="double-click Genesis.exe",
        regression="tests/test_launcher_brand_image.py",
        tags=["launcher", "ctkimage"],
    )
    record_incident(inc)
    kb = load_kb()
    assert len(kb["incidents"]) == 1
    hits = find_similar("CTkImage light_image must be instance")
    assert any(h["id"] == "test-ctkimage" for h in hits)
