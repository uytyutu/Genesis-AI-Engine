"""
Genesis Brain — Genesis Mind v3.

Pipeline: Think → Decide → LLM (+ Personality, Knowledge, Memory) → Calibrate → Critique
Thinking Brief never leaves the server stack — not in API, logs, or persistence.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from app.config import cloud_first_responses, cloud_proof_mode
from app.integration.chat_sessions import ChatSessionStore
from app.integration.genesis_brain.ai_jury import (
    apply_jury,
    invoke_jury,
    should_invoke_jury,
)
from app.integration.genesis_brain.brief_speech import BriefSpeechSynthesizer, clean_user_messages
from app.integration.genesis_brain.colloquial_ru import (
    colloquial_understanding_hint,
    is_colloquial_register,
)
from app.integration.genesis_brain.communication_presets import (
    resolve_effective_style,
    rhythm_for_style,
    style_llm_block,
    style_memory_hint,
)

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules
from app.integration.genesis_brain.layers import (
    GenesisKnowledgeLayer,
    GenesisLearningLayer,
    GenesisMemoryLayer,
    GenesisPersonalityLayer,
    GenesisPlanningLayer,
    GenesisReasoningLayer,
    GenesisSelfCritiqueLayer,
)
from app.integration.genesis_brain.layers.emotional_intelligence import (
    EmotionalIntelligenceLayer,
)
from app.integration.genesis_brain.layers.conversation_state import (
    ConversationState,
    ConversationStateLayer,
)
from app.integration.genesis_brain.layers.executive_brain import GenesisExecutiveBrain
from app.integration.genesis_brain.layers.human_calibration import HumanCalibrationLayer
from app.integration.genesis_brain.layers.thinking_engine import ThinkingEngine
from app.integration.genesis_brain.providers import build_provider_chain, build_provider_registry
from app.integration.genesis_brain.provider_diagnostics import diagnose_workforce
from app.integration.genesis_brain.workforce_manager import WorkforceManager, _PREMIUM_EMPLOYEES
from app.integration.genesis_brain.types import ChatResult, ProviderAttempt, WorkforceAttemptLog, WorkforceRouteLog, CalibrationVerdict
from app.integration.locale_service import assistant_llm_language_hint, effective_chat_locale
from app.integration.provider_health_service import viable_cloud_employees
from app.integration.llm_router.router import LLMRouter
from app.integration.vector_pipeline_trace import trace_step

from dataclasses import replace

logger = logging.getLogger(__name__)
BRAIN_VERSION = "genesis-mind-v3.0"
_CLOUD_EMPLOYEES = frozenset(
    {"groq", "gemini", "openrouter", "ollama", "openai", "anthropic", "deepseek", "kimi"}
)


class GenesisBrain:
    """Genesis Mind — think first, speak through LLM."""

    def __init__(
        self,
        *,
        memory_dir: Path | None = None,
        packages: list[dict[str, Any]] | None = None,
    ) -> None:
        _mem = memory_dir or Path(__file__).resolve().parent.parent / "memory"
        self._memory_dir = _mem
        self._chain = build_provider_chain(packages)
        self._registry = build_provider_registry(packages)
        self._workforce = WorkforceManager(memory_dir)
        self._last_provider: str | None = None
        self._knowledge = GenesisKnowledgeLayer(packages)
        self._memory = GenesisMemoryLayer(memory_dir)
        self._sessions = ChatSessionStore(memory_dir)
        self._conv_state = ConversationStateLayer(self._memory, self._sessions)
        self._reasoning = GenesisReasoningLayer()
        self._planning = GenesisPlanningLayer()
        self._learning = GenesisLearningLayer(memory_dir)
        self._emotion = EmotionalIntelligenceLayer()
        self._critique = GenesisSelfCritiqueLayer()
        self._thinking = ThinkingEngine()
        self._executive = GenesisExecutiveBrain()
        self._calibration = HumanCalibrationLayer()
        self._brief_speech = BriefSpeechSynthesizer()
        self._llm_router = LLMRouter(memory_dir)

    def intelligence_active(self) -> bool:
        return any(p.available() for p in self._chain)

    def provider_status(self) -> list[ProviderAttempt]:
        return [
            ProviderAttempt(provider_id=p.provider_id, available=p.available())
            for p in self._chain
        ]

    def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        visitor_id: str = "anonymous",
        session_id: str | None = None,
        personality_mode: Literal["public", "ceo"] = "public",
        assistant_locale: str | None = None,
        communication_style: str | None = None,
        debug: bool = False,
        intelligence_context: str | None = None,
        workforce_tier: int = 1,
        workforce_task: str | None = None,
        has_attachments: bool = False,
        fast_lane_only: bool = False,
    ) -> ChatResult:
        last_user_raw = self._last_user_text(messages)
        messages = clean_user_messages(messages)
        personality = GenesisPersonalityLayer(mode=personality_mode)
        memory_data = self._memory.observe_messages(visitor_id, messages)
        inferences = self._memory.get_inferences(visitor_id)
        conv_state = self._conv_state.process(
            visitor_id, messages, session_id=session_id
        )
        memory_block = self._memory.build_context_block(visitor_id)
        state_block = conv_state.to_prompt_block()
        knowledge_block = self._knowledge.build_block()

        last_user = self._last_user_text(messages)
        turn_index = sum(1 for m in messages if m.get("role") == "user")

        effective_style = resolve_effective_style(
            communication_style,
            last_user,
            inferences,
        )
        if last_user_raw:
            self._memory.observe_communication_habits(visitor_id, last_user_raw)

        from app.integration.genesis_brain.conversation_fast_lane import (
            FAST_MAX_CLOUD_ATTEMPTS,
            FAST_ROUTE_BUDGET_SEC,
            should_use_conversation_fast_lane,
        )

        if should_use_conversation_fast_lane(
            has_attachments=has_attachments,
            workforce_task=workforce_task,
            last_user=last_user,
        ):
            trace_step("conversation_fast_lane", task=workforce_task or "conversation")
            fast_result = self._conversation_fast_lane(
                system=system,
                messages=messages,
                visitor_id=visitor_id,
                session_id=session_id,
                personality=personality,
                memory_data=memory_data,
                conv_state=conv_state,
                knowledge_block=knowledge_block,
                memory_block=memory_block,
                state_block=state_block,
                last_user=last_user,
                last_user_raw=last_user_raw,
                turn_index=turn_index,
                assistant_locale=assistant_locale,
                effective_style=effective_style,
                intelligence_context=intelligence_context,
                workforce_task=workforce_task,
                debug=debug,
            )
            if fast_result and (fast_result.answer or "").strip():
                return fast_result

        if fast_lane_only:
            from app.integration.locale_service import localized_service_copy

            loc = assistant_locale or "de"
            return ChatResult(
                answer=localized_service_copy("error_fallback", loc),
                provider_id="genesis-local",
            )

        emotional = self._emotion.analyze(last_user)

        # Genesis Mind v3 — internal thinking cycle (never exposed)
        thinking = self._thinking.think(
            last_user=last_user,
            messages=messages,
            state=conv_state,
            emotional=emotional,
            memory_inferences=inferences,
        )
        if emotional.mood.value == "promotion":
            thinking = replace(
                thinking,
                emotional_state="воодушевление",
                recommended_action="comfort",
                best_response_strategy="поздравить искренне; разделить радость",
            )

        decision = self._executive.decide_from_thinking(
            thinking,
            state=conv_state,
            messages=messages,
            last_user=last_user,
        )

        brief = self._reasoning.analyze(messages, memory_data)
        plan = self._planning.suggest(brief.topic)

        personality_label = f"{ASSISTANT_NAME} CEO" if personality_mode == "ceo" else ASSISTANT_NAME
        mandate = thinking.to_llm_mandate(
            executive_action=decision.action,
            executive_confidence=decision.confidence,
            memory_inferences=inferences,
            conv_state=conv_state,
            personality=personality_label,
        )
        if plan.steps:
            mandate += "\n\n" + plan.to_prompt_hint()
        if state_block:
            mandate += "\n\n" + state_block
        if intelligence_context:
            mandate += "\n\n" + intelligence_context.strip()

        intent = brief.intent

        full_system = personality.wrap_system(
            base_system=system,
            knowledge_block=knowledge_block,
            memory_block=memory_block,
            reasoning_hint=brief.to_prompt_hint(),
            emotional_hint=self._emotion.to_prompt_hint(emotional),
        )

        language_hint = assistant_llm_language_hint(
            effective_chat_locale(assistant_locale, last_user),
            ASSISTANT_NAME,
            BRAND_NAME,
        )
        llm_instruction = (
            f"\n\n[{BRAND_NAME} Mind — Vector personality layer]\n"
            "Порядок: Thinking Brief (ниже) → сообщение пользователя → Ваш ответ.\n"
            f"Вы — {ASSISTANT_NAME}. Один голос для клиента. Внутренний исполнитель может меняться — "
            f"личность, память и стиль остаются Vector ({BRAND_NAME}). Brief уже принят.\n"
            f"{language_hint}\n"
            f"{ASSISTANT_NAME} не пытается быть правым — пытается быть полезным.\n"
            f"{style_llm_block(effective_style)}\n"
            f"{rhythm_for_style(effective_style, last_user)}\n"
            + product_mind_llm_rules()
        )
        if is_colloquial_register(last_user_raw):
            llm_instruction += "\n" + colloquial_understanding_hint()
        memory_style_hint = style_memory_hint(communication_style, inferences)
        if memory_style_hint:
            llm_instruction += "\n" + memory_style_hint
        full_system += (
            f"\n\n## THINKING BRIEF — THIS TURN\n"
            f"{mandate}\n"
            + llm_instruction
        )

        llm_messages = self._build_llm_messages(messages, mandate)

        available_employees = [
            p.provider_id for p in self._chain if p.available()
        ]
        viable_cloud = viable_cloud_employees(self._memory_dir)
        trace_step(
            "provider_health",
            viable_cloud=viable_cloud,
            viable_count=len(viable_cloud),
        )
        workforce_plan = self._workforce.plan(
            last_user,
            thinking,
            executive_action=decision.action,
            premium_allowed=self._premium_llm_allowed(
                thinking,
                last_user,
                workforce_tier=workforce_tier,
            ),
            available_employees=available_employees,
            preferred_employees=viable_cloud or None,
            messages=messages,
            workforce_task=workforce_task,
            visitor_id=visitor_id,
            memory_dir=self._memory_dir,
            has_attachments=has_attachments,
        )
        ordered_providers = self._workforce.sort_providers(self._chain, workforce_plan)

        employee_diagnostics = diagnose_workforce(
            self._registry,
            plan_order=list(workforce_plan.employee_order),
            premium_ids=_PREMIUM_EMPLOYEES,
        )

        result, draft, needs_rewrite, used_brief_fallback, route_log = self._route_providers(
            full_system,
            llm_messages,
            conversation_state=conv_state,
            visitor_id=visitor_id,
            turn_index=turn_index,
            thinking_brief=thinking,
            executive_decision=decision,
            providers=ordered_providers,
            workforce_plan=workforce_plan,
            conversation_messages=messages,
            available_employees=available_employees,
            employee_diagnostics=employee_diagnostics,
            viable_cloud_ids=set(viable_cloud),
            debug=debug,
        )

        used_brief_rewrite = False
        calibrated = draft
        _, cloud_from_employee = self._resolve_answer_source(
            result.provider_id,
            used_brief_fallback=used_brief_fallback,
            used_brief_rewrite=False,
        )
        if (
            needs_rewrite
            and not used_brief_fallback
            and not cloud_from_employee
            and not cloud_proof_mode()
        ):
            used_brief_rewrite = True
            calibrated = self._brief_speech.speak(
                thinking,
                decision,
                state=conv_state,
                visitor_id=visitor_id,
                turn_index=turn_index,
                last_user=last_user,
                messages=messages,
            )

        turn_calibration = self._calibration.evaluate(
            calibrated, thinking, messages=messages
        )
        answer_source, cloud_llm_used = self._resolve_answer_source(
            result.provider_id,
            used_brief_fallback=used_brief_fallback,
            used_brief_rewrite=used_brief_rewrite,
        )
        jury_verdict = None
        if should_invoke_jury(
            confidence=float(thinking.confidence),
            chosen_employee=route_log.chosen_employee,
            cloud_llm_used=cloud_llm_used,
            user_message=last_user,
            calibration_passed=not turn_calibration.needs_rewrite,
        ):
            jury_verdict = invoke_jury(
                registry=self._registry,
                chosen_employee=route_log.chosen_employee,
                user_message=last_user,
                draft_answer=calibrated,
            )
            calibrated = apply_jury(calibrated, jury_verdict)

        shaped = personality.finalize(
            calibrated,
            messages=messages,
            memory=memory_data,
            visitor_id=visitor_id,
            user_uses_ty=personality.user_uses_ty(messages),
            cloud_llm_used=cloud_llm_used,
            llm_draft_from_provider=answer_source not in ("brief_speech", "genesis-identity"),
            response_style=effective_style,
        )

        if intent and not cloud_llm_used and not cloud_proof_mode():
            shaped = self._critique.polish(
                shaped,
                intent=intent,
                messages=messages,
                visitor_id=visitor_id,
                provider_id=result.provider_id,
                cloud_llm_used=cloud_llm_used,
            )

        if last_user_raw:
            if session_id:
                self._sessions.append_messages(
                    session_id,
                    user=last_user_raw,
                    assistant=shaped,
                    auto_title_from=last_user_raw if turn_index == 1 else None,
                )
            else:
                self._memory.record_exchange(visitor_id, last_user_raw, shaped)
        self._memory.update_inferences(visitor_id, thinking, conv_state)

        self._learning.observe_turn(
            visitor_id=visitor_id,
            provider_id=result.provider_id,
            user_len=len(last_user),
            answer_len=len(shaped),
            used_local=result.provider_id == "genesis-local",
            workforce_task=workforce_plan.task,
            user_message=last_user,
            answer_preview=shaped[:400],
        )
        self._learning.reflect_turn(
            visitor_id=visitor_id,
            user_message=last_user,
            answer=shaped,
            employee_chosen=route_log.chosen_employee,
            workforce_task=workforce_plan.task,
            confidence=float(thinking.confidence),
            calibration_passed=not turn_calibration.needs_rewrite,
            calibration_reasons=list(turn_calibration.reasons),
            jury=jury_verdict.to_dict() if jury_verdict else None,
            plan_order=list(workforce_plan.employee_order),
        )

        trace = None
        if debug:
            final_calibration = turn_calibration
            answer_source, cloud_llm_used = self._resolve_answer_source(
                result.provider_id,
                used_brief_fallback=used_brief_fallback,
                used_brief_rewrite=used_brief_rewrite,
            )
            selected_attempt = next(
                (a for a in route_log.attempts if a.outcome == "selected"),
                None,
            )
            ranked_scores = sorted(
                workforce_plan.scores, key=lambda s: s.total, reverse=True
            )
            provider_score = next(
                (round(s.total, 1) for s in workforce_plan.scores if s.employee_id == workforce_plan.selected),
                None,
            )
            provider_candidates = [
                {"name": s.employee_id, "score": round(s.total, 1)}
                for s in ranked_scores
            ]
            runtime_pipeline = self._build_runtime_pipeline(
                user_message=last_user,
                mandate=mandate,
                thinking=thinking,
                decision=decision,
                route_log=route_log,
                selected_attempt=selected_attempt,
                draft=draft,
                calibrated=calibrated,
                final_answer=shaped,
                final_calibration=final_calibration,
                answer_source=answer_source,
                cloud_llm_used=cloud_llm_used,
                employee_diagnostics=employee_diagnostics,
                used_brief_fallback=used_brief_fallback,
                used_brief_rewrite=used_brief_rewrite,
            )
            trace = {
                "brain_version": BRAIN_VERSION,
                "provider": result.provider_id,
                "current_employee": route_log.chosen_employee,
                "current_model": route_log.chosen_model,
                "current_provider": answer_source,
                "cloud_llm_used": cloud_llm_used,
                "local_fallback_warning": (
                    None
                    if cloud_llm_used
                    else "Cloud LLM was NOT used"
                ),
                "answer_source": answer_source,
                "runtime_pipeline": runtime_pipeline,
                "executive_action": decision.action,
                "executive_decision": {
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "optional_question": decision.optional_question,
                },
                "thinking_brief": thinking.to_debug_dict(),
                "thinking_brief_text": mandate,
                "brief_injected_into_llm": True,
                "workforce_task": workforce_plan.task,
                "workforce_reason": workforce_plan.reason,
                "workforce_selected": workforce_plan.selected,
                "provider_score": provider_score,
                "provider_candidates": provider_candidates,
                "workforce_scores": [s.to_dict() for s in workforce_plan.scores],
                "workforce_employees": list(workforce_plan.employee_order),
                "workforce_quotas": self._workforce.quota_snapshot(),
                "workforce_performance": self._workforce.performance_snapshot(),
                "workforce_director": self._workforce.director_snapshot(),
                "ai_jury": jury_verdict.to_dict() if jury_verdict else {"invoked": False},
                "workforce_reality": {
                    **route_log.to_dict(),
                    "emotional_mood": emotional.mood.value,
                    "executive_action": decision.action,
                    "thinking_goal": thinking.real_goal or thinking.conversation_goal,
                    "thinking_implicit_need": thinking.implicit_need,
                    "final_calibration": final_calibration.to_dict(),
                    "employee_diagnostics": employee_diagnostics,
                },
                "conversation_pipeline": runtime_pipeline.get("steps", []),
                "pipeline": [
                    "ThinkingEngine",
                    "ExecutiveBrain",
                    "Memory+GoalAnalysis",
                    f"WorkforceManager ({route_log.chosen_employee})",
                    f"LLM cortex ({result.provider_id})",
                    "HumanCalibration",
                    "GenesisPersonalityLayer",
                    "GenesisSelfCritiqueLayer",
                ],
                "intent": intent.intent if intent else None,
                "emotional_mood": emotional.mood.value,
                "conversation_state": conv_state.to_dict(),
                "calibration": {
                    "llm_draft_preview": (draft or "")[:400],
                    "needs_rewrite": needs_rewrite,
                    "used_brief_speech_fallback": used_brief_fallback,
                    "used_brief_speech_rewrite": used_brief_rewrite,
                    "verdict": final_calibration.to_dict(),
                },
                "path": [
                    "frontend",
                    "POST /api/public/genesis-ai?debug=true",
                    "GenesisBrain.chat",
                    "ThinkingEngine",
                    "ExecutiveBrain.decide_from_thinking",
                    "LLM",
                    "HumanCalibration",
                    "GenesisPersonalityLayer",
                    "GenesisSelfCritiqueLayer",
                    "frontend",
                ],
            }

        return ChatResult(
            answer=shaped,
            cta_href=result.cta_href,
            cta_label=result.cta_label,
            action=result.action,
            provider_id=result.provider_id,
            trace=trace,
            dev_route=route_log.to_dict(),
        )

    def _conversation_fast_lane(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        visitor_id: str,
        session_id: str | None,
        personality: Any,
        memory_data: dict,
        conv_state: ConversationState,
        knowledge_block: str,
        memory_block: str,
        state_block: str,
        last_user: str,
        last_user_raw: str,
        turn_index: int,
        assistant_locale: str | None,
        effective_style: str,
        intelligence_context: str | None,
        workforce_task: str | None,
        debug: bool,
    ) -> ChatResult | None:
        """LLM-only dialogue — Identity/Memory/Knowledge context, no template pools."""
        from app.integration.genesis_brain.conversation_fast_lane import (
            FAST_MAX_CLOUD_ATTEMPTS,
            FAST_ROUTE_BUDGET_SEC,
            cap_context_block,
            cap_system_prompt,
            prioritize_local_provider,
            trim_messages_for_fast_lane,
        )
        from app.integration.genesis_brain.ai_identity import build_vector_llm_anchor
        from app.integration.genesis_brain.conversation_rhythm import rhythm_instruction
        from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules
        from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
        from app.integration.locale_service import assistant_llm_language_hint, effective_chat_locale
        from app.integration.genesis_brain.communication_presets import style_llm_block
        from app.integration.vector_pipeline_trace import trace_step

        emotional = self._emotion.analyze(last_user)
        memory_block = cap_context_block(memory_block)
        state_block = cap_context_block(state_block)
        # Fast lane skips the ~23KB product catalog — it dominates Ollama prefill latency.
        full_system = personality.wrap_system(
            base_system=system,
            knowledge_block="",
            memory_block=memory_block,
            emotional_hint=self._emotion.to_prompt_hint(emotional),
        )
        if state_block:
            full_system += "\n\n" + state_block
        if intelligence_context:
            full_system += "\n\n" + cap_context_block(intelligence_context.strip())
        language_hint = assistant_llm_language_hint(
            effective_chat_locale(assistant_locale, last_user),
            ASSISTANT_NAME,
            BRAND_NAME,
        )
        full_system += build_vector_llm_anchor(
            brand_name=BRAND_NAME,
            assistant_name=ASSISTANT_NAME,
            language_hint=language_hint,
            style_block=style_llm_block(effective_style),
            rhythm_block=rhythm_instruction(last_user),
            product_rules=product_mind_llm_rules(),
        )
        full_system = cap_system_prompt(full_system)
        llm_messages = trim_messages_for_fast_lane(list(messages))
        available_employees = [p.provider_id for p in self._chain if p.available()]
        viable_cloud = viable_cloud_employees(self._memory_dir)
        workforce_plan = self._workforce.plan(
            last_user,
            None,
            workforce_task=workforce_task or "conversation",
            available_employees=available_employees,
            preferred_employees=viable_cloud or None,
            messages=llm_messages,
            visitor_id=visitor_id,
            memory_dir=self._memory_dir,
        )
        ordered = prioritize_local_provider(
            self._workforce.sort_providers(self._chain, workforce_plan),
        )
        result, draft, _needs_rewrite, used_brief, route_log = self._route_providers(
            full_system,
            llm_messages,
            conversation_state=conv_state,
            visitor_id=visitor_id,
            turn_index=turn_index,
            providers=ordered,
            workforce_plan=workforce_plan,
            conversation_messages=messages,
            available_employees=available_employees,
            employee_diagnostics=[],
            viable_cloud_ids=set(viable_cloud),
            debug=debug,
            route_budget_sec=FAST_ROUTE_BUDGET_SEC,
            max_cloud_attempts_override=FAST_MAX_CLOUD_ATTEMPTS,
            skip_calibration_escalation=True,
        )
        if used_brief or not (draft or "").strip():
            trace_step("fast_lane_fallback", provider=result.provider_id)
            return None

        answer_source, cloud_llm_used = self._resolve_answer_source(
            result.provider_id,
            used_brief_fallback=used_brief,
            used_brief_rewrite=False,
        )
        shaped = personality.finalize(
            draft,
            messages=messages,
            memory=memory_data,
            visitor_id=visitor_id,
            user_uses_ty=personality.user_uses_ty(messages),
            cloud_llm_used=cloud_llm_used,
            llm_draft_from_provider=True,
            response_style=effective_style,
        )
        if last_user_raw:
            if session_id:
                self._sessions.append_messages(
                    session_id,
                    user=last_user_raw,
                    assistant=shaped,
                    auto_title_from=last_user_raw if turn_index == 1 else None,
                )
            else:
                self._memory.record_exchange(visitor_id, last_user_raw, shaped)
        trace_step(
            "fast_lane_ok",
            provider=result.provider_id,
            answer_len=len(shaped),
        )
        return ChatResult(
            answer=shaped,
            cta_href=result.cta_href,
            cta_label=result.cta_label,
            action=result.action,
            provider_id=result.provider_id,
            dev_route={
                **route_log.to_dict(),
                "fast_lane": True,
                "cloud_llm_used": cloud_llm_used,
            },
        )

    def stream_fast_lane(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        visitor_id: str,
        session_id: str | None,
        personality_mode: Literal["public", "ceo"] = "public",
        assistant_locale: str | None = None,
        communication_style: str | None = None,
        intelligence_context: str | None = None,
        workforce_task: str | None = None,
        has_attachments: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Stream fast-lane tokens; yields token events then a done payload."""
        from app.integration.genesis_brain.conversation_fast_lane import (
            FAST_MAX_CLOUD_ATTEMPTS,
            FAST_ROUTE_BUDGET_SEC,
            cap_context_block,
            cap_system_prompt,
            prioritize_local_provider,
            should_use_conversation_fast_lane,
            trim_messages_for_fast_lane,
        )
        from app.integration.genesis_brain.ai_identity import build_vector_llm_anchor
        from app.integration.genesis_brain.conversation_rhythm import rhythm_instruction
        from app.integration.genesis_brain.layers.product_mind import product_mind_llm_rules
        from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
        from app.integration.locale_service import assistant_llm_language_hint, effective_chat_locale
        from app.integration.genesis_brain.communication_presets import style_llm_block
        from app.integration.vector_pipeline_trace import trace_step

        messages = clean_user_messages(messages)
        last_user_raw = self._last_user_text(messages)
        last_user = last_user_raw
        if not should_use_conversation_fast_lane(
            has_attachments=has_attachments,
            workforce_task=workforce_task,
            last_user=last_user,
        ):
            return

        personality = GenesisPersonalityLayer(mode=personality_mode)
        memory_data = self._memory.observe_messages(visitor_id, messages)
        inferences = self._memory.get_inferences(visitor_id)
        conv_state = self._conv_state.process(visitor_id, messages, session_id=session_id)
        memory_block = cap_context_block(self._memory.build_context_block(visitor_id))
        state_block = cap_context_block(conv_state.to_prompt_block())
        turn_index = sum(1 for m in messages if m.get("role") == "user")
        effective_style = resolve_effective_style(communication_style, last_user, inferences)
        if last_user_raw:
            self._memory.observe_communication_habits(visitor_id, last_user_raw)

        emotional = self._emotion.analyze(last_user)
        full_system = personality.wrap_system(
            base_system=system,
            knowledge_block="",
            memory_block=memory_block,
            emotional_hint=self._emotion.to_prompt_hint(emotional),
        )
        if state_block:
            full_system += "\n\n" + state_block
        if intelligence_context:
            full_system += "\n\n" + cap_context_block(intelligence_context.strip())
        language_hint = assistant_llm_language_hint(
            effective_chat_locale(assistant_locale, last_user),
            ASSISTANT_NAME,
            BRAND_NAME,
        )
        full_system += build_vector_llm_anchor(
            brand_name=BRAND_NAME,
            assistant_name=ASSISTANT_NAME,
            language_hint=language_hint,
            style_block=style_llm_block(effective_style),
            rhythm_block=rhythm_instruction(last_user),
            product_rules=product_mind_llm_rules(),
        )
        full_system = cap_system_prompt(full_system)
        llm_messages = trim_messages_for_fast_lane(list(messages))
        available_employees = [p.provider_id for p in self._chain if p.available()]
        viable_cloud = viable_cloud_employees(self._memory_dir)
        workforce_plan = self._workforce.plan(
            last_user,
            None,
            workforce_task=workforce_task or "conversation",
            available_employees=available_employees,
            preferred_employees=viable_cloud or None,
            messages=llm_messages,
            visitor_id=visitor_id,
            memory_dir=self._memory_dir,
        )
        ordered = prioritize_local_provider(
            self._workforce.sort_providers(self._chain, workforce_plan),
        )
        route_deadline = time.perf_counter() + FAST_ROUTE_BUDGET_SEC
        cloud_attempts = 0
        trace_step("conversation_fast_lane_stream", task=workforce_task or "conversation")

        for provider in ordered:
            if time.perf_counter() >= route_deadline:
                break
            emp = provider.provider_id
            if not provider.available() or not hasattr(provider, "chat_stream"):
                continue
            if emp != "genesis-local":
                cloud_attempts += 1
                if cloud_attempts > FAST_MAX_CLOUD_ATTEMPTS:
                    break
            try:
                draft_parts: list[str] = []
                trace_step("provider_stream_attempt", employee=emp)
                for chunk in provider.chat_stream(system=full_system, messages=llm_messages):
                    draft_parts.append(chunk)
                    yield {"type": "token", "text": chunk}
                draft = "".join(draft_parts).strip()
                if not draft:
                    continue
                parsed = provider._parse_action(draft)  # noqa: SLF001
                raw_answer = (parsed.get("answer") or draft).strip()
                answer_source, cloud_llm_used = self._resolve_answer_source(
                    emp,
                    used_brief_fallback=False,
                    used_brief_rewrite=False,
                )
                shaped = personality.finalize(
                    raw_answer,
                    messages=messages,
                    memory=memory_data,
                    visitor_id=visitor_id,
                    user_uses_ty=personality.user_uses_ty(messages),
                    cloud_llm_used=cloud_llm_used,
                    llm_draft_from_provider=True,
                    response_style=effective_style,
                )
                if last_user_raw:
                    if session_id:
                        self._sessions.append_messages(
                            session_id,
                            user=last_user_raw,
                            assistant=shaped,
                            auto_title_from=last_user_raw if turn_index == 1 else None,
                        )
                    else:
                        self._memory.record_exchange(visitor_id, last_user_raw, shaped)
                self._last_provider = emp
                self._workforce.record_success(emp)
                trace_step("fast_lane_stream_ok", provider=emp, answer_len=len(shaped))
                yield {
                    "type": "done",
                    "answer": shaped,
                    "provider": emp,
                    "cta_href": parsed.get("cta_href"),
                    "cta_label": parsed.get("cta_label"),
                    "action": parsed.get("action"),
                    "dev_route": {
                        "fast_lane": True,
                        "stream": True,
                        "cloud_llm_used": cloud_llm_used,
                        "answer_source": answer_source,
                    },
                }
                return
            except Exception as exc:
                logger.warning("Genesis stream_fast_lane %s failed: %s", emp, exc)
                self._llm_router.on_provider_failure(emp, error=str(exc))
                continue

    def _route_providers(
        self,
        system: str,
        messages: list[dict[str, str]],
        *,
        conversation_state: ConversationState | None = None,
        visitor_id: str = "anonymous",
        turn_index: int = 0,
        thinking_brief: Any = None,
        executive_decision: Any = None,
        providers: list[Any] | None = None,
        workforce_plan: Any = None,
        conversation_messages: list[dict[str, str]] | None = None,
        available_employees: list[str] | None = None,
        employee_diagnostics: list[dict[str, Any]] | None = None,
        viable_cloud_ids: set[str] | None = None,
        debug: bool = False,
        route_budget_sec: float | None = None,
        max_cloud_attempts_override: int | None = None,
        skip_calibration_escalation: bool = False,
    ) -> tuple[ChatResult, str, bool, bool, WorkforceRouteLog]:
        """Route by Employee Score; escalate when calibration rejects a draft."""
        import os

        errors: list[str] = []
        chain = providers or self._chain
        task = getattr(workforce_plan, "task", "conversation")
        route_budget_sec = float(
            route_budget_sec if route_budget_sec is not None else os.getenv("GENESIS_ROUTE_BUDGET_SEC", "75")
        )
        route_deadline = time.perf_counter() + route_budget_sec
        max_cloud_attempts = int(
            max_cloud_attempts_override
            if max_cloud_attempts_override is not None
            else os.getenv("GENESIS_MAX_CLOUD_ATTEMPTS", "4")
        )
        cloud_attempts = 0
        last_attempted: str | None = None
        cal_messages = conversation_messages or messages
        attempts: list[WorkforceAttemptLog] = []
        escalation_count = 0
        chosen_latency_ms = 0.0
        fallback_started_at: str | None = None
        diagnostics = employee_diagnostics or []
        diag_by_id = {d["employee_id"]: d for d in diagnostics}

        score_map: dict[str, float] = {}
        if workforce_plan is not None:
            for s in workforce_plan.scores:
                score_map[s.employee_id] = s.total

        def _diag_reason(emp: str) -> tuple[str, str]:
            d = diag_by_id.get(emp)
            if d:
                return d.get("reason", "unavailable"), d.get("code", "disabled")
            return "недоступен", "disabled"

        def _log_skip(emp: str, reason: str, code: str = "") -> None:
            attempts.append(
                WorkforceAttemptLog(
                    employee_id=emp,
                    employee_score=score_map.get(emp),
                    outcome="skipped",
                    error=reason,
                    skip_code=code,
                )
            )

        def _finalize_route(
            result: ChatResult,
            *,
            why: str,
            used_brief: bool = False,
        ) -> tuple[ChatResult, str, bool, bool, WorkforceRouteLog]:
            chosen = result.provider_id
            model = getattr(
                next((p for p in chain if p.provider_id == chosen), None),
                "model_name",
                None,
            )
            src, cloud = self._resolve_answer_source(
                chosen,
                used_brief_fallback=used_brief,
                used_brief_rewrite=False,
            )
            route_log = WorkforceRouteLog(
                task=task,
                llm_capability=route_plan.capability,
                proof_pin=route_plan.proof_pin,
                chosen_employee=chosen,
                chosen_score=self._workforce.score_for(workforce_plan, chosen),
                chosen_latency_ms=chosen_latency_ms,
                chosen_model=model,
                why_chosen=why,
                not_chosen=self._workforce.explain_not_chosen(
                    workforce_plan,
                    chosen,
                    available_employees=available_employees or [],
                ),
                attempts=attempts,
                second_pass=escalation_count > 0,
                escalation_count=escalation_count,
                used_brief_speech_fallback=used_brief,
                employee_diagnostics=diagnostics,
                fallback_started_at=fallback_started_at,
                answer_source=src,
                cloud_llm_used=cloud,
            )
            return result, result.answer, used_brief, used_brief, route_log

        def _try_provider(provider: Any) -> ChatResult | None:
            nonlocal last_attempted, escalation_count, chosen_latency_ms, fallback_started_at, cloud_attempts
            emp = provider.provider_id
            if time.perf_counter() >= route_deadline:
                trace_step("route_budget_exceeded", employee=emp, task=task)
                return None
            if not provider.available():
                reason, code = _diag_reason(emp)
                _log_skip(emp, reason, code)
                return None
            last_attempted = emp
            model = getattr(provider, "model_name", None)
            if emp != "genesis-local":
                cloud_attempts += 1
                if cloud_attempts > max_cloud_attempts:
                    trace_step("cloud_attempt_cap", employee=emp, cap=max_cloud_attempts)
                    return None
            trace_step("provider_attempt", employee=emp, model=model)
            t0 = time.perf_counter()
            try:
                result = provider.chat(
                    system=system,
                    messages=messages,
                    conversation_state=conversation_state,
                    visitor_id=visitor_id,
                    turn_index=turn_index,
                    thinking_brief=thinking_brief,
                    executive_decision=executive_decision,
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                self._workforce.record_success(emp)
                draft = (result.answer or "").strip()
                if thinking_brief is None:
                    verdict = CalibrationVerdict(passed=True, needs_rewrite=False)
                else:
                    verdict = self._calibration.evaluate(
                        draft, thinking_brief, messages=cal_messages
                    )
                raw_capture = debug
                if verdict.needs_rewrite and not skip_calibration_escalation:
                    escalation_count += 1
                    trace_step(
                        "provider_escalated",
                        employee=emp,
                        reasons=list(verdict.reasons)[:3],
                    )
                    self._workforce.record_outcome(
                        emp,
                        task,
                        latency_ms=latency_ms,
                        calibration_passed=False,
                    )
                    attempts.append(
                        WorkforceAttemptLog(
                            employee_id=emp,
                            employee_score=score_map.get(emp),
                            latency_ms=latency_ms,
                            outcome="escalated",
                            calibration=verdict,
                            model=model,
                            raw_system=system if raw_capture else "",
                            raw_messages=list(messages) if raw_capture else None,
                            raw_response=draft if raw_capture else "",
                        )
                    )
                    logger.info(
                        "Genesis Workforce: escalate task=%s employee=%s (calibration)",
                        task,
                        emp,
                    )
                    return None
                self._workforce.record_outcome(
                    emp,
                    task,
                    latency_ms=latency_ms,
                    calibration_passed=True,
                )
                chosen_latency_ms = latency_ms
                attempts.append(
                    WorkforceAttemptLog(
                        employee_id=emp,
                        employee_score=score_map.get(emp),
                        latency_ms=latency_ms,
                        outcome="selected",
                        calibration=verdict,
                        model=model,
                        raw_system=system if raw_capture else "",
                        raw_messages=list(messages) if raw_capture else None,
                        raw_response=draft if raw_capture else "",
                    )
                )
                self._last_provider = emp
                logger.info("Genesis Workforce: task=%s employee=%s model=%s", task, emp, model)
                trace_step(
                    "provider_selected",
                    employee=emp,
                    model=model,
                    latency_ms=round(latency_ms, 1),
                )
                self._llm_router.on_provider_success(emp)
                return result
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                escalation_count += 1
                err_name = type(exc).__name__
                err_text = str(exc).lower()
                self._llm_router.on_provider_failure(emp, error=str(exc))
                if "429" in err_text or "rate" in err_text or err_name == "HTTPStatusError":
                    self._workforce.on_rate_limit(emp)
                self._workforce.record_outcome(
                    emp,
                    task,
                    latency_ms=latency_ms,
                    calibration_passed=False,
                    error=True,
                )
                attempts.append(
                    WorkforceAttemptLog(
                        employee_id=emp,
                        employee_score=score_map.get(emp),
                        latency_ms=latency_ms,
                        outcome="error",
                        error=f"{type(exc).__name__}: {exc}",
                        skip_code="network",
                        model=model,
                    )
                )
                errors.append(f"{emp}: {type(exc).__name__}")
                logger.warning("Genesis Mind provider failed %s: %s", emp, exc)
                trace_step(
                    "provider_error",
                    employee=emp,
                    error=f"{type(exc).__name__}: {exc}",
                    latency_ms=round(latency_ms, 1),
                )
                return None

        trace_step(
            "workforce_route_start",
            task=task,
            order=[getattr(p, "provider_id", "") for p in chain],
            budget_sec=route_budget_sec,
            viable_cloud=sum(
                1 for p in chain if getattr(p, "provider_id", "") != "genesis-local"
            ),
        )
        premium_in_plan = bool(
            workforce_plan
            and any(
                e in {"openai", "anthropic", "deepseek"}
                for e in workforce_plan.employee_order
            )
        )
        route_plan = self._llm_router.plan_route(
            task,
            premium_allowed=premium_in_plan,
        )
        by_id = {getattr(p, "provider_id", ""): p for p in chain}
        tried_cloud: set[str] = set()

        trace_step(
            "llm_router_plan",
            task=task,
            capability=route_plan.capability,
            primary=route_plan.primary,
            eligible=len(route_plan.failover_order),
            proof_pin=route_plan.proof_pin,
        )

        for eid in route_plan.failover_order:
            provider = by_id.get(eid)
            if provider is None:
                continue
            tried_cloud.add(eid)
            result = _try_provider(provider)
            if result is not None:
                return _finalize_route(
                    result,
                    why=route_plan.reason,
                )

        # Safety net: any remaining cloud provider not yet tried this turn.
        for provider in chain:
            eid = provider.provider_id
            if eid == "genesis-local" or eid in tried_cloud:
                continue
            if not provider.available():
                continue
            tried_cloud.add(eid)
            result = _try_provider(provider)
            if result is not None:
                return _finalize_route(
                    result,
                    why=f"{route_plan.reason}; safety_net",
                )

        if fallback_started_at is None:
            fallback_started_at = "cloud_exhausted"

        allow_emergency = self._llm_router.emergency_fallback_allowed(route_plan)
        if not allow_emergency and route_plan.any_cloud_configured:
            trace_step(
                "emergency_blocked",
                reason="cloud_configured_but_exhausted_this_turn",
            )

        def _try_local_silent(*, why_suffix: str = "") -> tuple | None:
            """User path: local Ollama without exposing infra — no cloud outage banners."""
            for provider in chain:
                if provider.provider_id != "genesis-local":
                    continue
                if cloud_proof_mode():
                    continue
                result = _try_provider(provider)
                if result is not None:
                    why = self._why_local_chosen(diagnostics)
                    return _finalize_route(result, why=why + why_suffix)
            return None

        local_result = _try_local_silent(why_suffix=" → local_fallback")
        if local_result is not None:
            return local_result

        if last_attempted:
            self._workforce.record_outcome(
                last_attempted,
                task,
                latency_ms=0.0,
                calibration_passed=False,
                rewritten_heavily=True,
            )

        from app.integration.locale_service import localized_service_copy

        user_fallback = localized_service_copy("error_fallback", "ru")

        if cloud_proof_mode():
            err_text = (
                "[CLOUD_PROOF] Все облачные провайдеры недоступны. "
                "Локальный fallback отключён — Groq/Gemini не ответили."
            )
            route_log = WorkforceRouteLog(
                task=task,
                chosen_employee="cloud-proof-failed",
                chosen_score=None,
                chosen_latency_ms=0.0,
                chosen_model=None,
                why_chosen="GENESIS_CLOUD_PROOF=1 — brief_speech/genesis-local disabled",
                not_chosen=self._workforce.explain_not_chosen(
                    workforce_plan,
                    "groq",
                    available_employees=available_employees or [],
                ),
                attempts=attempts,
                second_pass=False,
                escalation_count=escalation_count,
                used_brief_speech_fallback=False,
                employee_diagnostics=diagnostics,
                fallback_started_at="cloud_exhausted",
                answer_source="cloud_failed",
                cloud_llm_used=False,
            )
            return (
                ChatResult(answer=err_text, provider_id="cloud-proof-failed"),
                err_text,
                False,
                False,
                route_log,
            )

        if route_plan.any_cloud_configured:
            err_text = user_fallback
            route_log = WorkforceRouteLog(
                task=task,
                chosen_employee="cloud-exhausted",
                chosen_score=None,
                chosen_latency_ms=0.0,
                chosen_model=None,
                why_chosen="All configured cloud providers failed — user-safe fallback",
                not_chosen=self._workforce.explain_not_chosen(
                    workforce_plan,
                    last_attempted or "groq",
                    available_employees=available_employees or [],
                ),
                attempts=attempts,
                second_pass=False,
                escalation_count=escalation_count,
                used_brief_speech_fallback=False,
                employee_diagnostics=diagnostics,
                fallback_started_at="cloud_exhausted",
                answer_source="cloud_failed",
                cloud_llm_used=False,
            )
            return (
                ChatResult(answer=err_text, provider_id="genesis-local"),
                err_text,
                False,
                False,
                route_log,
            )

        fallback_started_at = "brief_speech"
        if thinking_brief is None or executive_decision is None:
            trace_step(
                "brief_speech_skipped",
                reason="missing_thinking_context",
            )
            route_log = WorkforceRouteLog(
                task=task,
                chosen_employee=last_attempted or "none",
                chosen_score=None,
                chosen_latency_ms=0.0,
                chosen_model=None,
                why_chosen="cloud exhausted; brief_speech skipped (no thinking context)",
                not_chosen=self._workforce.explain_not_chosen(
                    workforce_plan,
                    last_attempted or "groq",
                    available_employees=available_employees or [],
                ),
                attempts=attempts,
                second_pass=False,
                escalation_count=escalation_count,
                used_brief_speech_fallback=False,
                employee_diagnostics=diagnostics,
                fallback_started_at=fallback_started_at,
                answer_source="cloud_failed",
                cloud_llm_used=False,
            )
            return (
                ChatResult(answer="", provider_id=last_attempted or "none"),
                "",
                False,
                False,
                route_log,
            )
        trace_step("brief_speech_fallback", reason="cloud_exhausted_or_budget")
        synth = self._brief_speech.speak(
            thinking_brief,
            executive_decision,
            state=conversation_state or ConversationState(),
            visitor_id=visitor_id,
            turn_index=turn_index,
            last_user=self._last_user_text(messages),
            messages=messages,
        )
        chosen = "genesis-local"
        route_log = WorkforceRouteLog(
            task=task,
            chosen_employee=chosen,
            chosen_score=self._workforce.score_for(workforce_plan, chosen),
            chosen_latency_ms=0.0,
            chosen_model="brief_speech",
            why_chosen=self._why_local_chosen(diagnostics) + " → brief_speech",
            not_chosen=self._workforce.explain_not_chosen(
                workforce_plan,
                chosen,
                available_employees=available_employees or [],
            ),
            attempts=attempts,
            second_pass=True,
            escalation_count=escalation_count,
            used_brief_speech_fallback=True,
            employee_diagnostics=diagnostics,
            fallback_started_at=fallback_started_at,
            answer_source="brief_speech",
            cloud_llm_used=False,
        )
        return (
            ChatResult(answer=synth, provider_id=chosen),
            synth,
            True,
            True,
            route_log,
        )

    @staticmethod
    def _resolve_answer_source(
        provider_id: str,
        *,
        used_brief_fallback: bool,
        used_brief_rewrite: bool,
    ) -> tuple[str, bool]:
        if used_brief_fallback or used_brief_rewrite:
            return "brief_speech", False
        if provider_id == "genesis-local":
            return "genesis-local", False
        if provider_id in _CLOUD_EMPLOYEES:
            return provider_id, True
        return provider_id, False

    @staticmethod
    def _why_local_chosen(diagnostics: list[dict[str, Any]]) -> str:
        parts = [
            f"{d['employee_id']}={d['code']}"
            for d in diagnostics
            if d.get("employee_id") != "genesis-local" and not d.get("callable")
        ]
        if parts:
            return "Cloud not callable: " + ", ".join(parts)
        return "Cloud employees failed calibration or network — genesis-local fallback"

    @staticmethod
    def _build_runtime_pipeline(
        *,
        user_message: str,
        mandate: str,
        thinking: Any,
        decision: Any,
        route_log: WorkforceRouteLog,
        selected_attempt: WorkforceAttemptLog | None,
        draft: str,
        calibrated: str,
        final_answer: str,
        final_calibration: Any,
        answer_source: str,
        cloud_llm_used: bool,
        employee_diagnostics: list[dict[str, Any]],
        used_brief_fallback: bool,
        used_brief_rewrite: bool,
    ) -> dict[str, Any]:
        steps = [
            {"step": "Thinking", "status": "done"},
            {
                "step": "Executive",
                "status": "done",
                "action": decision.action,
                "confidence": decision.confidence,
            },
            {
                "step": "Employee",
                "status": "done",
                "employee": route_log.chosen_employee,
                "model": route_log.chosen_model,
                "provider": answer_source,
            },
            {
                "step": "Calibration",
                "status": "done",
                "passed": final_calibration.passed,
                "reasons": list(final_calibration.reasons),
            },
            {"step": "Personality", "status": "done"},
            {"step": "Done", "status": "done"},
        ]
        return {
            "user_message": user_message,
            "steps": steps,
            "thinking_brief": mandate,
            "employee_chosen": route_log.chosen_employee,
            "employee_why": route_log.why_chosen,
            "employee_model": route_log.chosen_model,
            "raw_prompt": {
                "system": selected_attempt.raw_system if selected_attempt else "",
                "messages": selected_attempt.raw_messages if selected_attempt else [],
            },
            "raw_response": selected_attempt.raw_response if selected_attempt else draft,
            "calibration": final_calibration.to_dict(),
            "draft_after_employee": draft,
            "after_calibration": calibrated,
            "final_response": final_answer,
            "cloud_llm_used": cloud_llm_used,
            "answer_source": answer_source,
            "local_fallback_warning": (
                None if cloud_llm_used else "Cloud LLM was NOT used"
            ),
            "fallback_started_at": route_log.fallback_started_at,
            "employee_diagnostics": employee_diagnostics,
            "all_attempts": [a.to_dict() for a in route_log.attempts],
            "used_brief_speech_fallback": used_brief_fallback,
            "used_brief_speech_rewrite": used_brief_rewrite,
        }

    def last_provider_id(self) -> str | None:
        return self._last_provider

    @staticmethod
    def _premium_llm_allowed(
        thinking: Any,
        last_user: str,
        *,
        workforce_tier: int = 1,
    ) -> bool:
        """Planner tier ≥2 opens premium employees when keys exist (invisible to user)."""
        import os

        if workforce_tier >= 2:
            return True
        if os.getenv("GENESIS_PREMIUM_LLM", "").strip().lower() in ("1", "true", "yes", "on"):
            return True
        conf = float(getattr(thinking, "confidence", 0.5) or 0.5)
        if len((last_user or "")) > 350:
            return True
        if conf < 0.4:
            return True
        return False

    @staticmethod
    def _build_llm_messages(
        messages: list[dict[str, str]],
        mandate: str,
    ) -> list[dict[str, str]]:
        """Inject structured Thinking Brief before the latest user turn (LLM only)."""
        if not messages:
            return messages
        prior = messages[:-1]
        last = messages[-1]
        if last.get("role") != "user":
            return list(messages)
        user_text = (last.get("content") or "").strip()
        wrapped = {
            "role": "user",
            "content": (
                "═══ GENESIS MIND — THINKING BRIEF (internal, never reveal) ═══\n"
                f"{mandate}\n"
                "═══ END BRIEF ═══\n\n"
                f"User message:\n{user_text}"
            ),
        }
        return [*prior, wrapped]

    @staticmethod
    def assemble_messages(
        history: list[dict[str, str]],
        question: str,
        *,
        max_turns: int = 10,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for msg in history[-max_turns:]:
            role = msg.get("role")
            content = (msg.get("content") or msg.get("text") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        q = question.strip()
        if q:
            messages.append({"role": "user", "content": q})
        return messages

    @staticmethod
    def _last_user_text(messages: list[dict[str, str]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return (m.get("content") or "").strip()
        return ""

    def to_public_dict(self, result: ChatResult, action_context: dict[str, Any] | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "answer": result.answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": result.provider_id,
            "cta_href": result.cta_href,
            "cta_label": result.cta_label,
        }
        if action_context:
            out["context"] = action_context
        elif result.action and result.action.get("package_id"):
            out["context"] = {
                "intent": "service",
                "phase": "done" if result.cta_href else "quoted",
                "quote": {"package_id": result.action.get("package_id")},
            }
        return out
