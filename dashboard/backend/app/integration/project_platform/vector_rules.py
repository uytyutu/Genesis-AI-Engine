"""Vector rules — Project Platform PM behavior."""

from __future__ import annotations

from app.integration.project_platform.mode import project_mode_rules_for_vector


def project_platform_rules_for_vector() -> str:
    return project_mode_rules_for_vector()
