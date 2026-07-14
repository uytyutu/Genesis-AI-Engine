"""Website executor — site-specific co-design; uses existing site generation."""

from __future__ import annotations

import re
from typing import Any

from app.integration.product_line import SERVICE_WEBSITE
from app.integration.project_platform.mode import detect_deliverable_intent

from app.execution.project_executors.base import ProjectExecutor, ProjectRouteContext

_SITE_TOPIC = re.compile(
    r"(?:сайт|site|landing|лендинг|веб-страниц|web\s*site|greenline)",
    re.IGNORECASE,
)
_SITE_CREATE = re.compile(
    r"(?:создай|создать|сделай|make|create|build|хочу)\s+.{0,32}(?:сайт|site|landing|лендинг)",
    re.IGNORECASE,
)


class WebsiteProjectExecutor:
    service_id = SERVICE_WEBSITE

    def matches(self, service_id: str) -> bool:
        return service_id == SERVICE_WEBSITE

    def detect_new_request(self, goal: str) -> bool:
        if _SITE_CREATE.search(goal) or _SITE_TOPIC.search(goal):
            return True
        intent = detect_deliverable_intent(goal)
        return bool(intent and intent["service_id"] == SERVICE_WEBSITE)

    def preview_open_label(self) -> str:
        return "🌐 Открыть сайт"

    def workspace_title(self) -> str:
        return "Site project"

    def try_route(self, ctx: ProjectRouteContext) -> dict[str, Any] | None:
        from app.execution import bridge as site_bridge

        goal = ctx.goal
        visitor_id = ctx.visitor_id
        memory_dir = ctx.memory_dir
        files = ctx.attachment_files
        history = ctx.history

        revised = site_bridge._try_site_revision(
            goal, visitor_id=visitor_id, memory_dir=memory_dir
        )
        if revised:
            return revised

        ws_id = site_bridge._existing_workspace_id(memory_dir, visitor_id)
        if ws_id and site_bridge._workspace_has_site_preview(memory_dir, ws_id):
            if not site_bridge._is_site_revision_request(goal):
                return None

        site_goal = site_bridge._parse_site_request(goal)
        if not site_goal and not site_bridge._existing_workspace_id(memory_dir, visitor_id):
            if not self.detect_new_request(goal):
                return None
            site_goal = goal

        if site_goal:
            try:
                from app.integration.project_platform.service import ProjectPlatformService

                ProjectPlatformService(memory_dir).bootstrap_from_message(visitor_id, site_goal)
            except Exception:
                pass
            if site_bridge._site_brief_insufficient(site_goal):
                ws_id = site_bridge._existing_workspace_id(memory_dir, visitor_id)
                if ws_id and site_bridge._workspace_has_business_context(memory_dir, ws_id):
                    pass
                else:
                    return site_bridge._site_journey_step_response(
                        "company",
                        combined=site_goal,
                        visitor_id=visitor_id,
                        memory_dir=memory_dir,
                        goal=goal,
                    )
            gated = site_bridge._maybe_gate_site_concept(
                site_goal,
                visitor_id=visitor_id,
                memory_dir=memory_dir,
                goal=goal,
                attachment_files=files,
                history=history,
            )
            if gated:
                return gated
            return site_bridge._run_generate_site(
                site_goal, visitor_id=visitor_id, memory_dir=memory_dir
            )

        follow = site_bridge._try_site_from_project_brief(
            goal,
            visitor_id=visitor_id,
            memory_dir=memory_dir,
            history=history,
        )
        if follow:
            return follow
        return None
