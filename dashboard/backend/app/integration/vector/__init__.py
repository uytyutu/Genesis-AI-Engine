"""Vector — one assistant, many surfaces (Platform / Website / Store / Customer)."""

from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.capabilities import CAPABILITIES, action_for, is_live
from app.integration.vector.companion_context import (
    COMPANION_CONTEXT_PATH,
    CompanionContextService,
)
from app.integration.vector.companion_contracts import (
    B4_ENGINE,
    B4_SLICE_ORDER,
    CONTEXT_ENGINE_REQUIRED,
    ENTRY_SURFACE,
)
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
    "B4_ENGINE",
    "B4_SLICE_ORDER",
    "CAPABILITIES",
    "COMPANION_CONTEXT_PATH",
    "CONTEXT_ENGINE_REQUIRED",
    "CompanionContextService",
    "ENTRY_SURFACE",
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
