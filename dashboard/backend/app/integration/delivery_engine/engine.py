"""Delivery Engine — orchestrates universal service lifecycle."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.integration.delivery_engine.handoff import build_purchase_ctas, build_order_href
from app.integration.delivery_engine.messages import (
    agreement_acknowledgement,
    concept_completion_message,
    consultation_intro,
)
from app.integration.delivery_engine.phases import (
    STAGE_AGREEMENT,
    STAGE_CONCEPT,
    STAGE_CONSULTATION,
    STAGE_DELIVERY,
    STAGE_PRELIMINARY_ESTIMATE,
    STAGE_PROJECT,
    STAGE_PURCHASE,
    STAGE_REVISION,
    STAGE_SUPPORT,
    DELIVERY_STAGES,
    delivery_stage_label_ru,
    infer_delivery_stage,
)
from app.integration.delivery_engine.service_registry import (
    execution_profile,
    service_display,
    service_for_capability,
)
from app.integration.delivery_engine.store import DeliveryEvent, DeliveryState, DeliveryStore, _utc_now
from app.integration.global_pricing import format_preliminary_after_approval
from app.integration.market_context import resolve_market_context
from app.integration.product_line import (
    LIFECYCLE_APPROVAL,
    LIFECYCLE_CHOICE,
    LIFECYCLE_COLLABORATION,
    LIFECYCLE_HANDOFF,
    LIFECYCLE_SUBSCRIPTION,
    SERVICE_WEBSITE,
    universal_approved_purchase_options,
)
from app.integration.project_platform.service import ProjectPlatformService

_APPROVAL_INTENT = re.compile(
    r"(?:"
    r"согласован|утвержд|подтвержд|да,?\s*(так|именно|всё|все|подходит)|"
    r"оформля|готов\s+(?:покуп|заказ)|всё\s+устраивает|устраивает"
    r")",
    re.IGNORECASE,
)
_PURCHASE_ONE_TIME = re.compile(r"(?:разов|единоразов|one.?time|купить\s+раз)", re.IGNORECASE)
_PURCHASE_SUBSCRIPTION = re.compile(r"(?:подписк|subscription|pro\b)", re.IGNORECASE)
_REVISION_INTENT = re.compile(
    r"(?:переделай|измени|добавь|убери|исправь|другой\s+цвет|другая\s+структур)",
    re.IGNORECASE,
)


class DeliveryEngine:
    VERSION = "delivery-engine-v1"

    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._store = DeliveryStore(memory_dir)

    def get_public_state(self, visitor_id: str, *, locale: str = "ru") -> dict[str, Any]:
        vid = (visitor_id or "anonymous").strip()[:64]
        state = self._sync_from_project(vid)
        project = ProjectPlatformService(self._memory).get_for_visitor(vid, locale=locale)
        stages = self._stage_progress(state.stage)
        svc = service_display(state.service_id or SERVICE_WEBSITE)
        return {
            "version": self.VERSION,
            "visitor_id": vid,
            "stage": state.stage,
            "stage_label": delivery_stage_label_ru(state.stage),
            "stages": stages,
            "service": svc,
            "purchase_type": state.purchase_type,
            "workspace_id": state.workspace_id,
            "has_project": project.get("has_project", False),
            "events": [e.to_dict() for e in state.events[-8:]],
            "lifecycle": [
                {"id": sid, "label": label} for sid, label in DELIVERY_STAGES
            ],
        }

    def note_consultation(self, visitor_id: str, *, service_id: str, goal: str = "") -> None:
        state = self._store.ensure(visitor_id[:64])
        state.service_id = service_id
        if goal:
            state.goal_summary = goal[:180]
        self._advance(
            state,
            STAGE_CONSULTATION,
            event_type="consultation",
            label="Консультация",
            detail=service_display(service_id)["label_ru"],
        )

    def try_handle_message(
        self,
        visitor_id: str,
        text: str,
        *,
        locale: str = "ru",
    ) -> dict[str, Any] | None:
        """Handle agreement / purchase choice — before generic Brain."""
        vid = (visitor_id or "anonymous").strip()[:64]
        t = (text or "").strip()
        if len(t) < 3:
            return None

        state = self._sync_from_project(vid)
        if state.version_count < 1 and not _APPROVAL_INTENT.search(t):
            return None

        service_id = state.service_id or SERVICE_WEBSITE

        if _PURCHASE_SUBSCRIPTION.search(t) and state.stage in (
            STAGE_PRELIMINARY_ESTIMATE,
            STAGE_PURCHASE,
            STAGE_AGREEMENT,
        ):
            return self._on_purchase_selected(
                state, service_id=service_id, purchase_type="subscription", locale=locale
            )
        if _PURCHASE_ONE_TIME.search(t) and state.stage in (
            STAGE_PRELIMINARY_ESTIMATE,
            STAGE_PURCHASE,
            STAGE_AGREEMENT,
        ):
            return self._on_purchase_selected(
                state, service_id=service_id, purchase_type="one_time", locale=locale
            )

        if _APPROVAL_INTENT.search(t) and state.version_count >= 1:
            return self._on_client_agreement(state, service_id=service_id, goal=t, locale=locale)

        if _REVISION_INTENT.search(t) and state.version_count >= 1:
            self._advance(
                state,
                STAGE_REVISION,
                event_type="revision",
                label="Запрошена доработка",
                detail=t[:120],
                product_phase=LIFECYCLE_COLLABORATION,
            )
            return None

        return None

    def on_consultation(self, visitor_id: str, *, service_id: str, goal: str = "") -> dict[str, Any]:
        state = self._store.ensure(visitor_id[:64])
        state.service_id = service_id
        if goal:
            state.goal_summary = goal[:180]
        self._advance(
            state,
            STAGE_CONSULTATION,
            event_type="consultation",
            label="Консультация",
            detail=service_display(service_id)["label_ru"],
        )
        return {
            "answer": consultation_intro(service_id),
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "delivery_engine",
        }

    def on_execution_complete(
        self,
        *,
        visitor_id: str,
        workspace_id: str,
        capability_id: str,
        outputs: dict[str, Any],
        goal: str,
        preview_href: str | None = None,
        primary_href: str | None = None,
        primary_label: str | None = None,
        extra_ctas: list[dict[str, Any]] | None = None,
        answer_override: str | None = None,
    ) -> dict[str, Any]:
        """Universal completion response — replaces per-service bridge copy."""
        vid = (visitor_id or "anonymous").strip()[:64]
        service_id = service_for_capability(capability_id, goal=goal)
        state = self._store.ensure(vid)
        self._merge_project_snapshot(state, vid)
        state.service_id = service_id
        state.workspace_id = workspace_id
        state.version_count = max(
            state.version_count + 1,
            self._version_count_from_project(vid),
        )
        if goal:
            state.goal_summary = goal[:180]

        artifact = service_display(service_id)["artifact_ru"]
        self._advance(
            state,
            STAGE_REVISION if state.version_count > 1 else STAGE_CONCEPT,
            event_type="generation",
            label=f"Обновлён {artifact}",
            detail=f"Version {state.version_count or 1}",
            product_phase=LIFECYCLE_COLLABORATION,
        )

        answer = answer_override or concept_completion_message(service_id, capability_id=capability_id)
        cta_actions = list(extra_ctas or [])
        href = preview_href or primary_href
        label = primary_label or f"Открыть {artifact}"
        if href and not any(a.get("href") == href for a in cta_actions):
            cta_actions.insert(
                0,
                {"href": href, "label": label, "group": "artifacts", "available": True},
            )

        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": href,
            "cta_label": label,
            "cta_actions": cta_actions or None,
            "context": {
                "workspace_id": workspace_id,
                "capability_id": capability_id,
                "service_id": service_id,
                "delivery_stage": state.stage,
                "execution_profile": execution_profile(capability_id),
            },
        }

    def _on_client_agreement(
        self,
        state: DeliveryState,
        *,
        service_id: str,
        goal: str,
        locale: str,
    ) -> dict[str, Any]:
        self._advance(
            state,
            STAGE_PRELIMINARY_ESTIMATE,
            event_type="approval",
            label="Концепция согласована",
            detail=service_display(service_id)["label_ru"],
            product_phase=LIFECYCLE_APPROVAL,
        )
        ctx = resolve_market_context(text=goal or state.goal_summary)
        estimate = format_preliminary_after_approval(ctx, locale=locale[:2])
        answer = (
            f"{agreement_acknowledgement(service_id)}\n\n"
            f"{estimate}\n\n"
            f"{universal_approved_purchase_options(service_id, estimate_block='')}"
        )
        ctas = build_purchase_ctas(
            service_id=service_id,
            visitor_id=state.visitor_id,
            workspace_id=state.workspace_id,
        )
        self._advance(
            state,
            STAGE_PURCHASE,
            event_type="estimate",
            label="Предварительная смета",
            product_phase=LIFECYCLE_CHOICE,
        )
        order_href = build_order_href(
            service_id=service_id,
            visitor_id=state.visitor_id,
            workspace_id=state.workspace_id,
            purchase_type="one_time",
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "delivery_engine",
            "cta_href": order_href,
            "cta_label": "Оформить заказ",
            "cta_actions": ctas,
            "context": {"delivery_stage": state.stage, "service_id": service_id},
        }

    def _on_purchase_selected(
        self,
        state: DeliveryState,
        *,
        service_id: str,
        purchase_type: str,
        locale: str,
    ) -> dict[str, Any]:
        state.purchase_type = purchase_type
        stage = STAGE_SUPPORT if purchase_type == "subscription" else STAGE_DELIVERY
        product_phase = LIFECYCLE_SUBSCRIPTION if purchase_type == "subscription" else LIFECYCLE_HANDOFF
        self._advance(
            state,
            stage,
            event_type="purchase",
            label="Выбран формат сотрудничества",
            detail="Подписка" if purchase_type == "subscription" else "Разовая покупка",
            product_phase=product_phase,
        )
        from app.integration.delivery_engine.handoff import unified_handoff_message

        order_href = build_order_href(
            service_id=service_id,
            visitor_id=state.visitor_id,
            workspace_id=state.workspace_id,
            purchase_type=purchase_type,
        )
        handoff = unified_handoff_message(purchase_type, service_id, locale=locale)
        label = service_display(service_id)["label_ru"].lower()
        return {
            "answer": (
                f"**{label.capitalize()}** — переходим к оформлению.\n\n"
                f"{handoff}\n\n"
                "На странице заказа вы увидите условия и сможете завершить оплату."
            ),
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "delivery_engine",
            "cta_href": order_href,
            "cta_label": "Перейти к оплате",
            "context": {
                "delivery_stage": state.stage,
                "purchase_type": purchase_type,
                "service_id": service_id,
            },
        }

    def _sync_from_project(self, visitor_id: str) -> DeliveryState:
        state = self._store.ensure(visitor_id)
        self._merge_project_snapshot(state, visitor_id)
        self._store.save(state)
        return state

    def _merge_project_snapshot(self, state: DeliveryState, visitor_id: str) -> None:
        project_payload = ProjectPlatformService(self._memory).get_for_visitor(visitor_id)
        project = project_payload.get("project")
        if not project:
            if not state.stage:
                state.stage = infer_delivery_stage(product_phase=None, mode="conversation")
            return

        versions = project.get("versions") or []
        state.version_count = max(state.version_count, len(versions))
        state.service_id = project.get("service_id") or state.service_id
        state.workspace_id = project.get("workspace_id") or state.workspace_id
        product_phase = project.get("lifecycle_phase")
        state.product_phase = product_phase
        inferred = infer_delivery_stage(
            product_phase=product_phase,
            mode=project.get("mode") or "conversation",
            has_versions=bool(versions),
            purchase_type=state.purchase_type,
        )
        from app.integration.delivery_engine.phases import delivery_stage_index

        if delivery_stage_index(inferred) >= delivery_stage_index(state.stage or "conversation"):
            state.stage = inferred

    def _version_count_from_project(self, visitor_id: str) -> int:
        project = ProjectPlatformService(self._memory).get_for_visitor(visitor_id).get("project")
        if not project:
            return 0
        return len(project.get("versions") or [])

    def _advance(
        self,
        state: DeliveryState,
        stage: str,
        *,
        event_type: str,
        label: str,
        detail: str = "",
        product_phase: str | None = None,
    ) -> None:
        state.stage = stage
        if product_phase:
            state.product_phase = product_phase
        state.events.append(
            DeliveryEvent(
                type=event_type,
                label=label,
                at=_utc_now(),
                detail=detail,
            )
        )
        if len(state.events) > 24:
            state.events = state.events[-24:]
        self._store.save(state)

    def _stage_progress(self, current: str) -> list[dict[str, str]]:
        ids = [s[0] for s in DELIVERY_STAGES]
        idx = ids.index(current) if current in ids else 0
        out: list[dict[str, str]] = []
        for i, (sid, label) in enumerate(DELIVERY_STAGES):
            if i < idx:
                st = "done"
            elif i == idx:
                st = "current"
            else:
                st = "upcoming"
            out.append({"id": sid, "label": label, "state": st})
        return out
