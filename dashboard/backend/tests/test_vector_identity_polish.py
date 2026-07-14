"""Product Reality — Vector identity polish (no architecture changes)."""

from app.integration.genesis_brain.ai_identity import (
    build_vector_llm_anchor,
    scrub_language_drift,
)
from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules


def test_build_vector_llm_anchor_language_lock_only():
    block = build_vector_llm_anchor(
        brand_name="Virtus Core",
        assistant_name="Vector",
        language_hint="Пишите на русском.",
        style_block="",
        rhythm_block="",
        product_rules=product_mind_llm_rules(),
    )
    assert "Vector" in block
    assert "Virtus Core" in block
    assert "gracias" in block.lower()
    assert "цифровой сотрудник" not in block
    assert "не generic AI" not in block
    assert "собеседник" not in block


def test_scrub_language_drift_removes_foreign_slips():
    raw = "Да, могу помочь. Gracias! I'm glad you asked."
    out = scrub_language_drift(raw, user_locale="ru")
    assert "gracias" not in out.lower()
    assert "i'm glad" not in out.lower()
    assert "могу помочь" in out.lower()


def test_scrub_language_drift_removes_heute():
    raw = "Отлично, heute можем начать с сайта для ресторана."
    out = scrub_language_drift(raw, user_locale="ru")
    assert "heute" not in out.lower()
    assert "ресторан" in out.lower()


def test_scrub_language_drift_fixes_mixed_script_and_underscores():
    # Latin O + Cyrillic tail; underscore glitch between scripts
    raw = "O\u043d\u043b\u0430\u0439\u043d-\u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0438 \u0441_clientem"
    out = scrub_language_drift(raw, user_locale="ru")
    assert "O\u043d" not in out
    assert "\u041e\u043d\u043b\u0430\u0439\u043d" in out
    assert "_clientem" not in out
    assert "clientem" not in out.lower()


def test_scrub_language_drift_keeps_english_when_locale_en():
    raw = "I'm glad you asked."
    out = scrub_language_drift(raw, user_locale="en")
    assert "glad" in out.lower()


def test_compact_fast_lane_hint_high_intent():
    from app.integration.vector_intelligence.pipeline import VectorTurnPlan, compact_fast_lane_hint
    from app.integration.vector_intelligence.planner import PlannerDecision

    plan = VectorTurnPlan(
        conversation_kind="product_creation",
        journey_phase="accept_responsibility",
        intent="build_result",
        need="helper",
        action="explore_together",
        priority="помочь с сайтом",
        memory_summary="",
        context_summary="",
        planner=PlannerDecision(
            goal="Сайт для ресторана",
            instruction="Признать задачу и предложить следующий шаг",
        ),
        workforce_channel="fast_dialog",
        workforce_task="simple",
        workforce_tier=1,
    )
    hint = compact_fast_lane_hint(plan)
    assert "Journey:" in hint
    assert "Высокое намерение" not in hint
    assert len(hint) < 600
