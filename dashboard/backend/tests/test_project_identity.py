"""Project identity and progress polish."""

from app.integration.project_platform.identity import (
    build_last_activity,
    build_next_action,
    build_progress,
    build_project_health,
    infer_market,
    status_label,
)
from app.integration.project_platform.schema import ProjectRecord, ProjectVersion


def test_infer_market_berlin():
    assert "Герман" in infer_market("Сайт для кафе в Берлине")


def test_progress_after_first_version():
    record = ProjectRecord(
        project_id="p1",
        workspace_id="w1",
        visitor_id="v1",
        title="Кафе",
        service_id="website",
        mode="project",
        lifecycle_phase="collaboration",
        versions=[
            ProjectVersion(
                version=1,
                label="Version 1",
                created_at="2026-01-01",
                summary="test",
                artifacts=[],
            )
        ],
    )
    prog = build_progress(record)
    assert prog["current_stage_id"] == "design"
    assert prog["percent"] >= 52
    assert status_label(record) == "Совместная доработка"
    health = build_project_health(record)
    assert health["tone"] == "yellow"
    assert build_next_action(record)["kind"] == "review"
    assert "Vector" in build_last_activity(record)["summary"]
