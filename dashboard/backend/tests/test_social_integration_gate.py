"""Social Integration Gate + product SSOT roadmap."""

from __future__ import annotations

from app.integration.product_gates_ssot import (
    LAUNCH_ROADMAP,
    OMNICHANNEL_PRODUCT,
    PACKAGE_SOCIAL_POLICY,
)
from app.integration.social_integration_gate import audit_social_integration_ready


def test_roadmap_order_matches_ssot():
    ids = [i["id"] for i in LAUNCH_ROADMAP]
    assert ids[:3] == [
        "golden_website_test",
        "visual_quality_gate",
        "social_integration_gate",
    ]
    assert "premium_visual_engine" in ids


def test_starter_has_no_cms_social():
    assert PACKAGE_SOCIAL_POLICY["basic"]["cms"] is False
    assert PACKAGE_SOCIAL_POLICY["basic"]["ai"] is False
    assert PACKAGE_SOCIAL_POLICY["business"]["cms"] is True
    assert PACKAGE_SOCIAL_POLICY["business"]["ai"] == "addon"
    assert PACKAGE_SOCIAL_POLICY["premium"]["ai"] == "included"
    assert PACKAGE_SOCIAL_POLICY["premium"]["floating"] is True


def test_omnichannel_is_one_product():
    assert OMNICHANNEL_PRODUCT["api_policy"] == "official_apis_only_modular"
    assert OMNICHANNEL_PRODUCT["level"] == 2
    assert "website" in OMNICHANNEL_PRODUCT["channels"]
    assert OMNICHANNEL_PRODUCT["by_package"]["business"] == "addon"
    assert OMNICHANNEL_PRODUCT["by_package"]["premium"] == "included"


def test_progressive_enhancement_ladder():
    from app.integration.product_gates_ssot import (
        FACTORY_NO_DEAD_ELEMENTS,
        PROGRESSIVE_ENHANCEMENT,
    )

    assert PROGRESSIVE_ENHANCEMENT["ladder"] == ("basic", "business", "premium")
    assert "phone" in FACTORY_NO_DEAD_ELEMENTS["fields"]
    assert "social_networks" in FACTORY_NO_DEAD_ELEMENTS["fields"]


def test_channel_capability_matrix_and_knowledge():
    from app.integration.product_gates_ssot import (
        CHANNEL_CAPABILITY_MATRIX,
        CONNECTION_HEALTH_STATES,
        GRACEFUL_DEGRADATION,
        OMNICHANNEL_KNOWLEDGE,
        channel_capability,
        channel_supports,
    )

    assert channel_supports("website", "payment") is True
    assert channel_supports("whatsapp", "payment") is False
    assert channel_capability("telegram", "payment") == "via_link"
    assert channel_capability("instagram", "catalog") == "limited"
    assert "ai_replies" in CHANNEL_CAPABILITY_MATRIX["viber"]
    assert "connected" in CONNECTION_HEALTH_STATES
    assert "notify_owner" in GRACEFUL_DEGRADATION["on_channel_failure"]
    assert OMNICHANNEL_KNOWLEDGE["sync"] == "edit_once_propagate_everywhere"


def test_experience_consistency_and_platform_modules():
    from app.integration.product_gates_ssot import (
        AI_FIRST_HUMAN_ALWAYS,
        CORE_PLATFORM_MODULES,
        EXPERIENCE_CONSISTENCY,
        SSOT_FOUNDATION_STATUS,
    )

    assert EXPERIENCE_CONSISTENCY["rule"].startswith("One brand")
    assert "prices" in EXPERIENCE_CONSISTENCY["unified"]
    assert AI_FIRST_HUMAN_ALWAYS["steps"][0] == "ai_answers_first"
    assert "ai_assistant_l2" in CORE_PLATFORM_MODULES
    assert SSOT_FOUNDATION_STATUS["status"] == "frozen"


def test_social_gate_fails_until_factory_surface():
    snap = audit_social_integration_ready()
    # Current demos lack social-bar markup — gate must stay honest FAIL.
    assert snap["status"] == "FAIL"
    assert snap["ok"] is False
