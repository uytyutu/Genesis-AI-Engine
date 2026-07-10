"""Canonical delivery stages — Block 4 unified lifecycle."""

from __future__ import annotations

from app.integration.product_line import (
    LIFECYCLE_APPROVAL,
    LIFECYCLE_CHOICE,
    LIFECYCLE_COLLABORATION,
    LIFECYCLE_CONCEPT,
    LIFECYCLE_DIALOG,
    LIFECYCLE_HANDOFF,
    LIFECYCLE_SUBSCRIPTION,
)

STAGE_CONVERSATION = "conversation"
STAGE_CONSULTATION = "consultation"
STAGE_PROJECT = "project"
STAGE_CONCEPT = "concept"
STAGE_REVISION = "revision"
STAGE_AGREEMENT = "agreement"
STAGE_PRELIMINARY_ESTIMATE = "preliminary_estimate"
STAGE_PURCHASE = "purchase"
STAGE_DELIVERY = "delivery"
STAGE_SUPPORT = "support"

DELIVERY_STAGES: tuple[tuple[str, str], ...] = (
    (STAGE_CONVERSATION, "Разговор"),
    (STAGE_CONSULTATION, "Консультация"),
    (STAGE_PROJECT, "Проект"),
    (STAGE_CONCEPT, "Концепция"),
    (STAGE_REVISION, "Доработка"),
    (STAGE_AGREEMENT, "Согласование"),
    (STAGE_PRELIMINARY_ESTIMATE, "Предварительная смета"),
    (STAGE_PURCHASE, "Покупка"),
    (STAGE_DELIVERY, "Передача"),
    (STAGE_SUPPORT, "Сопровождение"),
)

_STAGE_LABELS = dict(DELIVERY_STAGES)

# Product-line lifecycle (project_platform) → delivery stage
PRODUCT_PHASE_TO_DELIVERY: dict[str, str] = {
    LIFECYCLE_DIALOG: STAGE_CONVERSATION,
    LIFECYCLE_CONCEPT: STAGE_CONCEPT,
    LIFECYCLE_COLLABORATION: STAGE_REVISION,
    LIFECYCLE_APPROVAL: STAGE_AGREEMENT,
    LIFECYCLE_CHOICE: STAGE_PRELIMINARY_ESTIMATE,
    LIFECYCLE_HANDOFF: STAGE_DELIVERY,
    LIFECYCLE_SUBSCRIPTION: STAGE_SUPPORT,
}


def delivery_stage_label_ru(stage_id: str) -> str:
    return _STAGE_LABELS.get(stage_id, stage_id)


def delivery_stage_index(stage_id: str) -> int:
    ids = [s[0] for s in DELIVERY_STAGES]
    return ids.index(stage_id) if stage_id in ids else 0


def infer_delivery_stage(
    *,
    product_phase: str | None,
    mode: str = "conversation",
    has_versions: bool = False,
    purchase_type: str | None = None,
) -> str:
    """Map project snapshot → canonical delivery stage."""
    if purchase_type == "subscription" and product_phase == LIFECYCLE_SUBSCRIPTION:
        return STAGE_SUPPORT
    if product_phase == LIFECYCLE_HANDOFF:
        return STAGE_DELIVERY
    if product_phase == LIFECYCLE_CHOICE:
        return STAGE_PURCHASE if purchase_type else STAGE_PRELIMINARY_ESTIMATE
    if product_phase == LIFECYCLE_APPROVAL:
        return STAGE_AGREEMENT
    if product_phase == LIFECYCLE_COLLABORATION:
        return STAGE_REVISION if has_versions else STAGE_CONCEPT
    if product_phase == LIFECYCLE_CONCEPT:
        return STAGE_CONCEPT
    if mode == "project":
        return STAGE_PROJECT if not has_versions else STAGE_CONCEPT
    return STAGE_CONVERSATION
