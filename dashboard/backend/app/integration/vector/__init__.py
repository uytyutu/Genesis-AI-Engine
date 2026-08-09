"""Vector — one assistant, many surfaces (Platform / Website / Store / Customer)."""

from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.capabilities import CAPABILITIES, action_for, is_live
from app.integration.vector.dialog_wizard import (
    build_customer_dialog_stub,
    build_platform_dialog,
    build_store_dialog,
    build_website_dialog_stub,
)
from app.integration.vector.service import VectorContextService
from app.integration.vector.ai_health import build_ai_health
from app.integration.vector.website_tips import scan_website_tips

__all__ = [
    "CAPABILITIES",
    "VectorContextService",
    "action_for",
    "is_live",
    "build_business_setup",
    "build_ai_health",
    "build_store_dialog",
    "build_platform_dialog",
    "build_website_dialog_stub",
    "build_customer_dialog_stub",
    "scan_website_tips",
]
