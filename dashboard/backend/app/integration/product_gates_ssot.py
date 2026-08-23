"""Virtus Core product gates SSOT — roadmap + Social L1/L2 + Progressive Enhancement.

Canonical prose: `.cursor/rules/virtus-core-product-ssot.mdc` and siblings.
"""

from __future__ import annotations

from typing import Any

LAUNCH_ROADMAP: tuple[dict[str, str], ...] = (
    {
        "id": "golden_website_test",
        "label": "Golden Website Test",
        "role": "Commercial pipeline: sell → deliver",
    },
    {
        "id": "visual_quality_gate",
        "label": "Visual Quality Gate",
        "role": "No empty decorative zones; package perception floor",
    },
    {
        "id": "social_integration_gate",
        "label": "Social Integration Gate (Level 1 Links)",
        "role": "Social links on site/store; omit missing networks; Starter=order, Business+=CMS",
    },
    {
        "id": "commercial_ux_gate",
        "label": "Commercial UX Gate",
        "role": "No Landing-era buyer copy; forms match Website/Shop/AI catalog",
    },
    {
        "id": "brand_audit",
        "label": "Brand Audit",
        "role": "Public Virtus Core only",
    },
    {
        "id": "golden_store_test",
        "label": "Golden AI Store Test",
        "role": "Store path + Commerce Gate",
    },
    {
        "id": "premium_visual_engine",
        "label": "Premium Visual Engine",
        "role": "Next major stage: 3D / video / Lottie / rich assets",
    },
)

# Level 1 — Social Links (site feature, not a SKU).
PACKAGE_SOCIAL_LINKS: dict[str, dict[str, Any]] = {
    "basic": {
        "level": 1,
        "cms": False,
        "source": "order_form",
        "widgets": False,
        "floating": False,
        "edit_path": "micro_update_or_upgrade_business",
        "ai": False,
    },
    "business": {
        "level": 1,
        "cms": True,
        "source": "website_admin_social",
        "widgets": True,
        "floating": False,
        "reorder": True,
        "custom_url": True,
        "ai": "addon",  # Level 2 sold separately
    },
    "premium": {
        "level": 1,
        "cms": True,
        "source": "website_admin_social",
        "widgets": True,
        "floating": True,
        "reorder": True,
        "custom_url": True,
        "click_analytics": True,
        "ai": "included",  # Level 2 Omnichannel included
    },
}

# Back-compat alias for older imports / tests.
PACKAGE_SOCIAL_POLICY = PACKAGE_SOCIAL_LINKS

# Level 2 — Social Automation (commercial product).
SOCIAL_AUTOMATION = {
    "client_name": "AI Assistant",
    "engine_name": "Omnichannel AI",
    "sku_kind": "separate_product",
    "not": "social_links",
    "capabilities": (
        "auto_replies",
        "message_handling",
        "lead_gen",
        "booking",
        "order_assist",
        "faq",
    ),
    "by_package": {
        "basic": "unavailable",
        "business": "addon",
        "premium": "included",
    },
}

OMNICHANNEL_PRODUCT = {
    "client_name": "AI Assistant",
    "engine_name": "Omnichannel AI",
    "level": 2,
    "rule": "Social Automation product — one brain, official APIs only; not Social Links",
    "channels": (
        "website",
        "store",
        "instagram",
        "facebook",
        "messenger",
        "whatsapp",
        "telegram",
        "viber",
        "discord",
        "email",
        "live_chat",
    ),
    "api_policy": "official_apis_only_modular",
    "by_package": SOCIAL_AUTOMATION["by_package"],
}

# Capability values: True | False | "platform_dependent" | "via_link" | "limited" | "impl_dependent"
CHANNEL_CAPABILITY_MATRIX: dict[str, dict[str, Any]] = {
    "website": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": True,
        "catalog": True,
    },
    "instagram": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": "platform_dependent",
        "catalog": "limited",
    },
    "facebook": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": "platform_dependent",
        "catalog": "limited",
    },
    "telegram": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": "via_link",
        "catalog": "impl_dependent",
    },
    "whatsapp": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": "via_link",
        "catalog": "limited",
    },
    "viber": {
        "ai_replies": True,
        "human_handoff": True,
        "booking": True,
        "payment": "via_link",
        "catalog": "limited",
    },
}

CONNECTION_HEALTH_STATES: tuple[str, ...] = (
    "connected",  # green
    "needs_reauth",  # yellow
    "disconnected",  # red
)

GRACEFUL_DEGRADATION = {
    "rule": "One channel failure must never take down the ecosystem",
    "on_channel_failure": (
        "site_keeps_working",
        "ai_continues_on_other_channels",
        "notify_owner",
        "offer_reconnect",
    ),
}

OMNICHANNEL_KNOWLEDGE = {
    "rule": "Single Knowledge Base → AI Assistant → all channels",
    "anti_pattern": "per_channel_knowledge_copies_as_source_of_truth",
    "sync": "edit_once_propagate_everywhere",
}

EXPERIENCE_CONSISTENCY = {
    "rule": "One brand personality across all channels",
    "unified": (
        "tone",
        "message_style",
        "greeting",
        "dialogue_logic",
        "offers",
        "prices",
        "hours",
        "contacts",
        "brand_identity",
    ),
    "anti_pattern": "per_channel_bots_as_separate_personalities",
}

AI_FIRST_HUMAN_ALWAYS = {
    "steps": (
        "ai_answers_first",
        "handoff_when_out_of_knowledge_or_needs_human",
        "kb_update_after_operator_with_owner_confirm_on_shared_truth",
    ),
    "goal": "fast_answers_plus_company_control_of_knowledge_quality",
}

CORE_PLATFORM_MODULES: tuple[str, ...] = (
    "website",
    "store",
    "client_workspace",
    "social_links_l1",
    "ai_assistant_l2",
    "knowledge_base",
    "automation",
    "analytics",
)

GWT_PERFORMANCE_KPIS: dict[str, tuple[float, float] | float] = {
    # (soft_target_s, hard_target_s) or single target seconds
    "create_order_s": (0.5, 2.0),
    "factory_start_s": (1.0, 5.0),
    "site_generation_s": (60.0, 90.0),
    "zip_prepare_s": (10.0, 30.0),
    "download_start_s": (1.0, 5.0),
    "full_e2e_s": (120.0, 180.0),
}

# Progressive ladder (do not jump to <2 min before <180s is stable).
GWT_PERFORMANCE_STAGES = {
    "stage1_s": 180,
    "stage2_s": 120,
    "stage3_s": 90,
}

GWT_LAYER_DEFAULTS = {
    "functional_status": "pass",
    "infrastructure_status": "pass_with_notes",
    "performance_status": "open",
    "observed_zip_download_s": 357.0,
    "note": "Functional closed (ZIP delivered). Performance OPEN before commercial scale.",
}

SSOT_FOUNDATION_STATUS = {
    "status": "frozen",
    "rule": "No new fundamental SSOT unless launch forces a correction; ship modules next",
}


def channel_supports(channel: str, capability: str) -> bool:
    """True only when the matrix marks the capability as fully available."""
    row = CHANNEL_CAPABILITY_MATRIX.get((channel or "").strip().lower())
    if not row:
        return False
    return row.get(capability) is True


def channel_capability(channel: str, capability: str) -> Any:
    row = CHANNEL_CAPABILITY_MATRIX.get((channel or "").strip().lower()) or {}
    return row.get(capability)


PROGRESSIVE_ENHANCEMENT = {
    "ladder": ("basic", "business", "premium"),
    "rule": "Each package adds layers on the same foundation; upgrades without full rebuild",
    "anti_pattern": "throwaway_starter_architecture",
}

FACTORY_NO_DEAD_ELEMENTS = {
    "rule": "Omit UI for missing client data — no grey ghost icons, no empty slots",
    "fields": (
        "phone",
        "email",
        "address",
        "hours",
        "maps",
        "social_networks",
    ),
}

SOCIAL_NETWORKS: tuple[str, ...] = (
    "instagram",
    "facebook",
    "tiktok",
    "youtube",
    "linkedin",
    "x",
    "telegram",
    "whatsapp",
    "viber",
    "pinterest",
    "discord",
    "snapchat",
    "threads",
    "vk",
    "custom",
)


def roadmap_as_dict() -> dict[str, Any]:
    return {
        "ok": True,
        "title": "Virtus Core Launch Roadmap",
        "items": list(LAUNCH_ROADMAP),
        "social_links_l1": PACKAGE_SOCIAL_LINKS,
        "social_automation_l2": SOCIAL_AUTOMATION,
        "omnichannel": OMNICHANNEL_PRODUCT,
        "package_social": PACKAGE_SOCIAL_POLICY,
        "social_networks": list(SOCIAL_NETWORKS),
        "progressive_enhancement": PROGRESSIVE_ENHANCEMENT,
        "factory_no_dead_elements": FACTORY_NO_DEAD_ELEMENTS,
        "channel_capability_matrix": CHANNEL_CAPABILITY_MATRIX,
        "connection_health_states": list(CONNECTION_HEALTH_STATES),
        "graceful_degradation": GRACEFUL_DEGRADATION,
        "omnichannel_knowledge": OMNICHANNEL_KNOWLEDGE,
        "experience_consistency": EXPERIENCE_CONSISTENCY,
        "ai_first_human_always": AI_FIRST_HUMAN_ALWAYS,
        "core_platform_modules": list(CORE_PLATFORM_MODULES),
        "ssot_foundation": SSOT_FOUNDATION_STATUS,
        "gwt_performance_kpis": GWT_PERFORMANCE_KPIS,
        "gwt_layer_defaults": GWT_LAYER_DEFAULTS,
    }
