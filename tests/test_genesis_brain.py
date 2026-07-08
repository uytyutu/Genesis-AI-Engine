"""Genesis Brain — personality calibration tests."""

from app.integration.genesis_brain import GenesisBrain
from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalIntelligenceLayer
from app.integration.genesis_brain.layers.personality import GenesisPersonalityLayer
from app.integration.genesis_brain.local_mind import LocalMindProvider


def test_greetings_differ_by_visitor():
    style = ConversationStyleEngine()
    a = style.pick_greeting(style.build_context({"visit_count": 0}, "visitor-a"))
    b = style.pick_greeting(style.build_context({"visit_count": 5, "name": "Анна"}, "visitor-b"))
    assert a != b or "Анна" in b


def test_emotional_promotion():
    layer = EmotionalIntelligenceLayer()
    brief = layer.analyze("Я сегодня получил повышение")
    assert brief.mood.value == "promotion"
    opening = layer.emotional_opening(brief)
    assert opening and "Поздравляю" in opening


def test_emotional_heavy():
    layer = EmotionalIntelligenceLayer()
    opening = layer.emotional_opening(layer.analyze("Мне тяжело"))
    assert opening and "непросто" in opening.lower()


def test_flat_earth_respectful():
    layer = EmotionalIntelligenceLayer()
    opening = layer.emotional_opening(layer.analyze("Земля плоская"))
    assert opening and "сфер" in opening.lower()
    assert "не прав" not in opening.lower()


def test_personality_finalize_greeting():
    p = GenesisPersonalityLayer()
    out = p.finalize("", messages=[{"role": "user", "content": "Привет"}], visitor_id="x1")
    assert "Добро" in out or "Genesis" in out or "Приветствую" in out
    assert "ChatGPT" not in out


def test_local_mind_factory():
    p = LocalMindProvider()
    r = p.chat(system="", messages=[{"role": "user", "content": "Что такое Factory?"}])
    assert "Factory" in r.answer


def test_brain_promotion_dialogue(tmp_path):
    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    r = brain.chat(
        system="",
        messages=[{"role": "user", "content": "Я получил повышение!"}],
        visitor_id="t1",
    )
    assert "Поздравляю" in r.answer


def test_brain_ceo_morning(tmp_path):
    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    r = brain.chat(
        system="",
        messages=[{"role": "user", "content": "Доброе утро"}],
        visitor_id="owner",
        personality_mode="ceo",
    )
    assert "Доброе утро" in r.answer
    assert "Предлагаю" in r.answer


def test_business_consultation_flow():
    """Mission scenario: open business → no re-introduction."""
    mind = LocalMindProvider()
    msgs: list[dict[str, str]] = []

    steps = [
        ("Привет", None),
        ("Хочу открыть бизнес", "направлен|предложил|вариант"),
        ("Не знаю какой", "офлайн|онлайн|личн"),
        ("Бюджет 20000€", "20 000|20000"),
        ("Я из Германии", "герман|направлен|вариант|20 000"),
        ("Хочу открыть кофейню", "кофейн|направлен|бюджет|стран"),
        ("Нужен сайт", "сайт"),
        ("Нужно приложение", "приложен"),
        ("Нужно продвижение", "продвиж|карт|лендинг"),
        ("Хочу пользоваться Studio", "Studio"),
    ]
    for user_text, must_contain in steps:
        msgs.append({"role": "user", "content": user_text})
        r = mind.chat(system="", messages=msgs)
        answer = r.answer
        assert "Расскажите о задаче" not in answer
        assert not answer.strip().startswith("Я — Genesis.")
        if must_contain:
            low = answer.lower()
            if "|" in must_contain:
                parts = must_contain.split("|")
                assert any(p in low for p in parts), f"Missing any of {parts} in: {answer[:120]}"
            else:
                assert must_contain.lower() in low, f"Missing {must_contain} in: {answer[:120]}"
        msgs.append({"role": "assistant", "content": answer})


def test_personality_suppresses_repeat_intro():
    p = GenesisPersonalityLayer()
    out = p.finalize(
        "Я — Genesis. Расскажите о задаче — бизнес или сайт.",
        messages=[
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте!"},
            {"role": "user", "content": "Хочу открыть бизнес"},
        ],
        visitor_id="x2",
    )
    assert "Расскажите о задаче" not in out
    assert not out.strip().startswith("Я — Genesis")


def test_conversation_state_moscow_scenario(tmp_path):
    """CEO scenario: Russia/Moscow/budget — never re-ask country or budget."""
    from app.integration.genesis_brain.layers.conversation_state import ConversationStateLayer
    from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer

    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    vid = "moscow-test"
    msgs: list[dict[str, str]] = []

    steps = [
        ("хочу бизнес открыть поможешь?", ["направлен", "предложил", "вариант", "**1."], False),
        ("бюджет минимальный страна россия город москва", [], True),
        ("10к рублей", ["10", "вариант"], False),
    ]
    for user_text, must_contain, must_not_ask_budget_country in steps:
        msgs.append({"role": "user", "content": user_text})
        r = brain.chat(system="", messages=msgs, visitor_id=vid)
        ans = r.answer.lower()
        assert "расскажите о задаче" not in ans
        if must_not_ask_budget_country:
            assert "какой бюджет" not in ans, ans
            assert "в какой стране" not in ans, ans
        if must_contain:
            assert any(token.lower() in ans for token in must_contain), (
                f"Missing any of {must_contain} in: {ans[:200]}"
            )
        msgs.append({"role": "assistant", "content": r.answer})

    layer = ConversationStateLayer(GenesisMemoryLayer(tmp_path))
    state = layer.process(vid, msgs)
    assert state.country == "Россия"
    assert state.city == "Москва"
    assert state.budget_amount == 10000
    assert state.budget_currency == "RUB"


def test_fuzzy_typo_business_intent():
    from app.integration.genesis_brain.fuzzy_nlp import normalize_for_intent
    from app.integration.genesis_brain.layers.intent import GenesisIntentLayer

    n = normalize_for_intent("придкмай мне бизнес проект")
    assert "придумай" in n or "бизнес" in n
    intent = GenesisIntentLayer().analyze(
        [{"role": "user", "content": "придкмай мне бизнес проект"}],
        {},
    )
    assert intent.intent == "business"


def test_self_critique_rejects_template():
    from app.integration.genesis_brain.layers.intent import GenesisIntentLayer
    from app.integration.genesis_brain.layers.self_critique import GenesisSelfCritiqueLayer

    intent = GenesisIntentLayer().analyze(
        [{"role": "user", "content": "Хочу сайт"}],
        {},
    )
    critique = GenesisSelfCritiqueLayer()
    out = critique.polish(
        "Я — Genesis. Расскажите о задаче.",
        intent=intent,
        visitor_id="t1",
        provider_id="genesis-local",
    )
    assert "расскажите о задаче" not in out.lower()


def test_greeting_variation():
    from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine

    style = ConversationStyleEngine()
    a = style.pick_greeting(style.build_context({"visit_count": 0}, "v-a"))
    b = style.pick_greeting(style.build_context({"visit_count": 0}, "v-b"))
    assert a != b or "Genesis" in a


def test_executive_propose_first():
    """First business turn — three options, no mandatory country question."""
    mind = LocalMindProvider()
    r = mind.chat(
        system="",
        messages=[{"role": "user", "content": "Хочу открыть бизнес"}],
        turn_index=1,
    )
    low = r.answer.lower()
    assert "в какой стране" not in low
    assert any(w in low for w in ("направлен", "предложил", "вариант", "**1."))


def test_executive_thanks_close(tmp_path):
    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    msgs = [
        {"role": "user", "content": "Хочу открыть бизнес"},
        {"role": "assistant", "content": "Три направления..."},
        {"role": "user", "content": "Спасибо"},
    ]
    r = brain.chat(system="", messages=msgs, visitor_id="close-test")
    low = r.answer.lower()
    assert "рад был помочь" in low or "продолжим" in low
    assert "чем могу помочь" not in low
    assert "что ещё" not in low


def test_executive_pivot_chain(tmp_path):
    """Germany → Austria → budget → reject coffee → AI company."""
    from app.integration.genesis_brain.layers.conversation_state import ConversationStateLayer
    from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer

    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    vid = "pivot-chain"
    msgs: list[dict[str, str]] = []
    steps = [
        "Я живу в Германии",
        "Нет, я переехал — теперь живу в Австрии",
        "Бюджет вырос — 50000 €",
        "Не кофейня",
        "Лучше онлайн",
        "Вообще хочу AI компанию",
    ]
    for text in steps:
        msgs.append({"role": "user", "content": text})
        r = brain.chat(system="", messages=msgs, visitor_id=vid)
        assert "расскажите о задаче" not in r.answer.lower()
        msgs.append({"role": "assistant", "content": r.answer})

    layer = ConversationStateLayer(GenesisMemoryLayer(tmp_path))
    state = layer.process(vid, msgs)
    assert state.country == "Австрия"
    assert state.budget_amount == 50000
    assert state.budget_currency == "EUR"
    assert state.goal == "ai_company"
    assert state.prefers_online is True
    assert "coffee" in state.rejected_types or state.business_type != "coffee"


def test_executive_ty_oshibsya():
    mind = LocalMindProvider()
    msgs = [
        {"role": "user", "content": "Хочу бизнес в Москве"},
        {"role": "assistant", "content": "Кофейня..."},
        {"role": "user", "content": "Ты ошибся"},
    ]
    r = mind.chat(system="", messages=msgs, turn_index=3)
    low = r.answer.lower()
    assert "поправили" in low or "пересмотр" in low


def test_executive_pochemu(tmp_path):
    brain = GenesisBrain(memory_dir=tmp_path, packages=[])
    msgs = [
        {"role": "user", "content": "бюджет минимальный страна россия город москва"},
        {"role": "assistant", "content": "Варианты..."},
        {"role": "user", "content": "10к рублей"},
        {"role": "assistant", "content": "Кофейню не получится..."},
        {"role": "user", "content": "Почему?"},
    ]
    r = brain.chat(system="", messages=msgs, visitor_id="why-test")
    assert len(r.answer) > 40
    assert "потому" in r.answer.lower() or "бюджет" in r.answer.lower()


def test_personal_reflection_not_website_sales():
    """Dogfooding FAIL fix: success question ≠ business pipeline."""
    mind = LocalMindProvider()
    cases = [
        "Как думаешь, я стану успешным?",
        "Я хочу стать миллионером",
        "Смогу ли я добиться успеха?",
        "Как ты думаешь, у меня получится?",
    ]
    banned = ("6 страниц", "650–850", "studio basic", "factory", "запись клиентов")
    for q in cases:
        r = mind.chat(system="", messages=[{"role": "user", "content": q}])
        low = r.answer.lower()
        for b in banned:
            assert b not in low, f"Sales leak in {q!r}: {r.answer[:120]}"
        assert len(r.answer) > 30


def test_business_still_works_after_conversation_type():
    mind = LocalMindProvider()
    r = mind.chat(system="", messages=[{"role": "user", "content": "Хочу открыть бизнес"}])
    low = r.answer.lower()
    assert any(w in low for w in ("направлен", "предложил", "вариант", "**1."))


def test_dogfooding_personal_three_turn():
    """Critical dogfooding: success → correction → millionaire — zero sales."""
    brain = GenesisBrain()
    banned = (
        "6 страниц",
        "650–850",
        "studio basic",
        "factory",
        "запись клиентов",
        "продолжайте — я слушаю",
        "расскажите подробнее",
    )

    msgs: list[dict[str, str]] = []
    steps = [
        "Как думаешь, я стану успешным?",
        "Я задавал не этот вопрос",
        "Хочу стать миллионером",
    ]
    for q in steps:
        msgs.append({"role": "user", "content": q})
        r = brain.chat(system="", messages=list(msgs), visitor_id="dogfood-personal")
        msgs.append({"role": "assistant", "content": r.answer})
        low = r.answer.lower()
        for b in banned:
            assert b not in low, f"Sales/template leak on {q!r}: {r.answer[:160]}"
        assert len(r.answer) > 40, f"Too short on {q!r}: {r.answer!r}"

    assert "миллион" in msgs[-1]["content"].lower() or "деньги" in msgs[-1]["content"].lower()
    assert "прав" in msgs[-3]["content"].lower() or "неверно" in msgs[-3]["content"].lower()


def test_meta_correction_classifier():
    from app.integration.genesis_brain.layers.conversation_type import classify_conversation_type

    assert classify_conversation_type("Я задавал не этот вопрос", []) == "meta_correction"
    assert classify_conversation_type("Как думаешь, я стану успешным?", []) == "personal_reflection"
    assert classify_conversation_type("Я хочу стать миллионером", []) == "personal_reflection"
    assert classify_conversation_type("Хочу открыть кофейню", []) == "business_consulting"
    assert classify_conversation_type("Нужен сайт для салона", []) == "product_creation"
    assert classify_conversation_type("Мне плохо", []) == "emotional_support"


def test_goal_analysis_doubt_not_business():
    from app.integration.genesis_brain.layers.goal_analysis import GoalAnalysisLayer
    from app.integration.genesis_brain.layers.conversation_state import ConversationState

    goal = GoalAnalysisLayer().analyze(
        "Как думаешь, я стану успешным?",
        [{"role": "user", "content": "Как думаешь, я стану успешным?"}],
        ConversationState(),
        None,
    )
    assert goal.real_goal == "doubt"
    assert goal.helpful_action in ("answer", "comfort")
    assert "сомнение" in goal.reasoning_chain.lower() or "бизнес" in goal.reasoning_chain.lower()


def test_goal_analysis_life_context_connects_thread():
    from app.integration.genesis_brain import GenesisBrain

    brain = GenesisBrain()
    msgs: list[dict[str, str]] = []
    for q in (
        "Как думаешь, я стану успешным?",
        "Мне 27",
        "Хочу стать миллионером",
    ):
        msgs.append({"role": "user", "content": q})
        r = brain.chat(system="", messages=list(msgs), visitor_id="goal-v2-thread")
        msgs.append({"role": "assistant", "content": r.answer})

    last = msgs[-1]["content"].lower()
    age_reply = msgs[-3]["content"].lower()
    assert "27" in age_reply
    assert len(age_reply) > 40
    assert "миллион" in last or "деньги" in last
    assert "6 страниц" not in last


def test_thinking_engine_v3_millionaire_inference():
    from app.integration.genesis_brain.layers.thinking_engine import ThinkingEngine
    from app.integration.genesis_brain.layers.conversation_state import ConversationState

    thinking = ThinkingEngine().think(
        last_user="Хочу стать миллионером",
        messages=[{"role": "user", "content": "Хочу стать миллионером"}],
        state=ConversationState(),
        emotional=None,
    )
    assert "финансов" in thinking.real_goal
    assert thinking.emotional_state == "надежда"
    assert thinking.confidence >= 0.7
    assert thinking.recommended_action == "advise"


def test_executive_v2_has_goal_brief():
    from app.integration.genesis_brain.layers.executive_brain import GenesisExecutiveBrain
    from app.integration.genesis_brain.layers.conversation_state import ConversationState

    ex = GenesisExecutiveBrain().decide(
        state=ConversationState(),
        last_user="Хочу стать миллионером",
        messages=[{"role": "user", "content": "Хочу стать миллионером"}],
        turn_index=1,
    )
    assert ex.goal is not None
    assert ex.goal.real_goal == "future_vision"
    assert ex.reasoning_chain
    assert ex.helpful_action == "advise"


def test_calibration_allows_identity_capability_word_automation():
    from app.integration.genesis_brain.layers.human_calibration import HumanCalibrationLayer
    from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

    cal = HumanCalibrationLayer()
    identity = (
        "Я создан для того, чтобы понимать задачи людей: объяснять, планировать, "
        "анализировать и сопровождать — в обучении, бизнесе, творчестве и автоматизации."
    )
    verdict = cal.evaluate(
        identity,
        ThinkingBrief(implicit_need="identity", real_goal="who_am_i"),
        messages=[{"role": "user", "content": "Кто ты?"}],
        conversation_kind="general_question",
    )
    assert not verdict.needs_rewrite


def test_calibration_rejects_unsolicited_sales():
    from app.integration.genesis_brain.layers.human_calibration import HumanCalibrationLayer
    from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

    cal = HumanCalibrationLayer()
    verdict = cal.evaluate(
        "Рекомендую лендинг и CRM под ключ от 650–850 €.",
        ThinkingBrief(implicit_need="отдых", real_goal="отдых"),
        messages=[{"role": "user", "content": "Я устал"}],
        conversation_kind="emotional_support",
    )
    assert verdict.needs_rewrite
    assert any("продаж" in r for r in verdict.reasons)


def test_calibration_allows_greeting_reply_on_casual_conversation():
    """Groq-style short greeting must not fail implicit_need heuristic (step 1 fix)."""
    from app.integration.genesis_brain.layers.human_calibration import HumanCalibrationLayer
    from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

    cal = HumanCalibrationLayer()
    thinking = ThinkingBrief(
        real_goal="человеческий контакт",
        implicit_need="услышать живого собеседника, не бота",
        recommended_action="answer",
        best_response_strategy="1–2 коротких предложения + один вопрос о человеке",
    )
    verdict = cal.evaluate(
        "Привет! Как дела сегодня?",
        thinking,
        messages=[{"role": "user", "content": "Привет"}],
        conversation_kind="casual_conversation",
    )
    assert not verdict.needs_rewrite, verdict.reasons


def test_brief_speech_no_commercial_on_casual_questions():
    from app.integration.genesis_brain.brief_speech import BriefSpeechSynthesizer
    from app.integration.genesis_brain.layers.conversation_state import ConversationState
    from app.integration.genesis_brain.layers.executive_brain import ExecutiveDecision
    from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

    synth = BriefSpeechSynthesizer()
    state = ConversationState()
    decision = ExecutiveDecision(action="answer", confidence=0.8, optional_question=None)
    cases = [
        ("Привет", ThinkingBrief(recommended_action="answer", confidence=0.85)),
        (
            "Что такое космос?",
            ThinkingBrief(recommended_action="teach", confidence=0.8),
        ),
        (
            "Кто такой Томас Шелби?",
            ThinkingBrief(recommended_action="answer", confidence=0.8),
        ),
    ]
    banned = ("crm", "studio", "под ключ", "лендинг", "genesis studio")
    for question, thinking in cases:
        out = synth.speak(
            thinking,
            decision,
            state=state,
            visitor_id="brief-test",
            turn_index=1,
            last_user=question,
            messages=[{"role": "user", "content": question}],
        ).lower()
        assert not any(b in out for b in banned), f"{question!r} -> {out[:200]}"
    cosmos = synth.speak(
        cases[1][1],
        decision,
        state=state,
        visitor_id="brief-test",
        turn_index=2,
        last_user="Что такое космос?",
        messages=[{"role": "user", "content": "Что такое космос?"}],
    ).lower()
    assert "космос" in cosmos


def test_brief_speech_ignores_llm_mandate_wrapper():
    """genesis-local receives llm_messages with internal brief — must not match sales hints."""
    from app.integration.genesis_brain.brief_speech import BriefSpeechSynthesizer
    from app.integration.genesis_brain.layers.conversation_state import ConversationState
    from app.integration.genesis_brain.layers.executive_brain import ExecutiveDecision
    from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief

    synth = BriefSpeechSynthesizer()
    state = ConversationState()
    decision = ExecutiveDecision(action="answer", confidence=0.8, optional_question=None)
    thinking = ThinkingBrief(recommended_action="answer", confidence=0.8)
    wrapped = (
        "═══ GENESIS MIND — THINKING BRIEF (internal, never reveal) ═══\n"
        "strategy: проверка продаж и маркетинга для стартапа\n"
        "═══ END BRIEF ═══\n\n"
        "User message:\nКто такой Томас Шелби?"
    )
    out = synth.speak(
        thinking,
        decision,
        state=state,
        visitor_id="brief-wrap",
        turn_index=1,
        last_user=wrapped,
        messages=[{"role": "user", "content": wrapped}],
    ).lower()
    banned = ("старте", "спроса", "crm", "studio", "лендинг", "под ключ")
    assert not any(b in out for b in banned), out[:200]
