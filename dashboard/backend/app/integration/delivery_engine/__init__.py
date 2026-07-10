"""Delivery Engine — universal service lifecycle for Virtus Core."""

from app.integration.delivery_engine.engine import DeliveryEngine
from app.integration.delivery_engine.phases import DELIVERY_STAGES, delivery_stage_label_ru

__all__ = ["DeliveryEngine", "DELIVERY_STAGES", "delivery_stage_label_ru"]
