"""Task Planner v2 — goals to ExecutionPlan (no prompt hints)."""

from __future__ import annotations

import uuid
from typing import Any

from app.execution.capabilities import ExecutionCapabilityRegistry
from app.execution.models import ExecutionPlan, ExecutionStep, RollbackStrategy, VerificationRule
from app.execution.permissions import union_permissions


class TaskPlannerV2:
    """Map user goals to structured execution plans using the capability catalog."""

    def __init__(self, registry: ExecutionCapabilityRegistry | None = None) -> None:
        self._registry = registry or ExecutionCapabilityRegistry()

    def plan(self, goal: str, *, workspace_id: str = "", context: dict[str, Any] | None = None) -> ExecutionPlan:
        g = goal.strip()
        lower = g.lower()
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        steps: list[ExecutionStep] = []
        perms: list[frozenset[str]] = []

        if self._looks_like_site_goal(lower):
            steps, perms = self._site_plan(g, workspace_id)
        elif self._looks_like_document_goal(lower):
            steps, perms = self._document_plan(g, workspace_id, lower)
        elif self._looks_like_deploy_goal(lower):
            steps, perms = self._deploy_plan(g, workspace_id)
        else:
            steps = [
                ExecutionStep(
                    id="step-1-clarify",
                    capability_id="task_queue",
                    title="Clarify goal before execution",
                    inputs={"task_type": "clarify_goal", "payload": {"goal": g, "context": context or {}}},
                    verification=VerificationRule(
                        id="vr-clarify",
                        description="Clarification task enqueued",
                        required_output_keys=("task_id",),
                    ),
                )
            ]
            perms.append(frozenset({"write"}))

        return ExecutionPlan(
            plan_id=plan_id,
            goal=g,
            workspace_id=workspace_id,
            steps=tuple(steps),
            required_permissions=union_permissions(*perms) if perms else frozenset({"read"}),
            rollback=RollbackStrategy.REVERT_LAST_STEP,
        )

    def _looks_like_site_goal(self, lower: str) -> bool:
        return any(w in lower for w in ("сайт", "site", "landing", "лендинг", "стоматолог", "клиник"))

    def _looks_like_document_goal(self, lower: str) -> bool:
        return any(w in lower for w in ("pdf", "документ", "бизнес-план", "docx", "презентац", "excel"))

    def _looks_like_deploy_goal(self, lower: str) -> bool:
        return any(w in lower for w in ("deploy", "деплой", "docker", "запусти", "опублик"))

    def _site_plan(self, goal: str, workspace_id: str) -> tuple[list[ExecutionStep], list[frozenset[str]]]:
        steps = [
            ExecutionStep(
                id="step-1-brief",
                capability_id="filesystem_write",
                title="Save project brief",
                inputs={"path": "brief.md", "content": goal, "workspace_id": workspace_id},
                verification=VerificationRule(
                    id="vr-brief",
                    description="Brief file written",
                    required_output_keys=("path",),
                ),
            ),
            ExecutionStep(
                id="step-2-generate",
                capability_id="generate_site",
                title="Generate site from brief",
                inputs={"brief": goal, "workspace_id": workspace_id},
                depends_on=("step-1-brief",),
                verification=VerificationRule(
                    id="vr-site",
                    description="Site artifact produced",
                    required_output_keys=("artifact_id",),
                ),
            ),
            ExecutionStep(
                id="step-3-preview",
                capability_id="deployment",
                title="Publish preview",
                inputs={"artifact_id": "{{step-2-generate.artifact_id}}", "target": "preview"},
                depends_on=("step-2-generate",),
                verification=VerificationRule(
                    id="vr-preview",
                    description="Preview URL available",
                    required_output_keys=("url",),
                ),
            ),
        ]
        perms = [
            frozenset({"write", "filesystem"}),
            frozenset({"write", "filesystem", "network"}),
            frozenset({"deployment", "network", "external_api"}),
        ]
        return steps, perms

    def _document_plan(
        self, goal: str, workspace_id: str, lower: str
    ) -> tuple[list[ExecutionStep], list[frozenset[str]]]:
        cap = "analyze_pdf" if "pdf" in lower or "бизнес" in lower else "analyze_docx"
        steps = [
            ExecutionStep(
                id="step-1-read",
                capability_id="filesystem_read",
                title="Load document from workspace",
                inputs={"path": "uploads/document", "workspace_id": workspace_id},
            ),
            ExecutionStep(
                id="step-2-analyze",
                capability_id=cap,
                title="Analyze document",
                inputs={"path": "uploads/document", "goal": goal},
                depends_on=("step-1-read",),
                verification=VerificationRule(
                    id="vr-analyze",
                    description="Analysis summary produced",
                    required_output_keys=("summary",) if cap == "analyze_pdf" else ("text",),
                ),
            ),
        ]
        perms = [frozenset({"read", "filesystem"}), frozenset({"read", "filesystem", "external_api"})]
        return steps, perms

    def _deploy_plan(self, goal: str, workspace_id: str) -> tuple[list[ExecutionStep], list[frozenset[str]]]:
        steps = [
            ExecutionStep(
                id="step-1-build",
                capability_id="docker_build",
                title="Build container",
                inputs={"workspace_id": workspace_id, "tag": "virtus-preview"},
            ),
            ExecutionStep(
                id="step-2-run",
                capability_id="docker_run",
                title="Run container",
                inputs={"image_id": "{{step-1-build.image_id}}", "workspace_id": workspace_id},
                depends_on=("step-1-build",),
            ),
            ExecutionStep(
                id="step-3-deploy",
                capability_id="deployment",
                title="Expose deployment URL",
                inputs={"artifact_id": "{{step-2-run.container_id}}", "target": "preview"},
                depends_on=("step-2-run",),
                verification=VerificationRule(id="vr-url", description="URL returned", required_output_keys=("url",)),
            ),
        ]
        perms = [
            frozenset({"terminal", "filesystem", "deployment"}),
            frozenset({"terminal", "deployment", "network"}),
            frozenset({"deployment", "network", "external_api"}),
        ]
        return steps, perms
