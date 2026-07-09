"""
Genesis Brain — Genesis Mind v3.

Pipeline: Think → Decide → LLM (+ Personality, Knowledge, Memory) → Calibrate → Critique
Thinking Brief never leaves the server stack — not in API, logs, or persistence.
"""

from __future__ import annotations

import logging
import time
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
from app.integration.genesis_brain.ai_identity import try_local_identity_reply
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
from app.integration.genesis_brain.types import ChatResult, ProviderAttempt, WorkforceAttemptLog, WorkforceRouteLog
from app.integration.locale_service import assistant_llm_language_hint

from dataclasses import replace

logger = logging.getLogger(__name__)
BRAIN_VERSION = "genesis-mind-v3.0"
_CLOUD_EMPLOYEES = frozenset(
    {"groq", "gemini", "openrouter", "ollama", "openai", "anthropic", "deepseek"}
)


class GenesisBrain:
    """Genesis Mind — think first, speak through LLM."""

    def __init__(
        self,
        *,
        memory_dir: Path | None = None,
        packages: list[dict[str, Any]] | None = None,
    ) -> None:
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

        identity_answer = try_local_identity_reply(
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=messages,
        )
        if identity_answer:
            if last_user_raw:
                if session_id:
                    self._sessions.append_messages(
                        session_id,
                        user=last_user_raw,
                        assistant=identity_answer,
                        auto_title_from=last_user_raw if turn_index == 1 else None,
                    )
                else:
                    self._memory.record_exchange(visitor_id, last_user_raw, identity_answer)
            return ChatResult(answer=identity_answer, provider_id="genesis-identity")

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

        intent = brief.intent

        full_system = personality.wrap_system(
            base_system=system,
            knowledge_block=knowledge_block,
            memory_block=memory_block,
            reasoning_hint="",
            emotional_hint=self._emotion.to_prompt_hint(emotional),
        )

        language_hint = assistant_llm_language_hint(
            assistant_locale or "ru",
            ASSISTANT_NAME,
            BRAND_NAME,
        )
        llm_instruction = (
            f"\n\n[{BRAND_NAME} Mind — LLM is cortex]\n"
            "Порядок: Thinking Brief (ниже) → сообщение пользователя → Ваш ответ.\n"
            f"Вы НЕ ChatGPT. Вы — языковая кора {ASSISTANT_NAME} ({BRAND_NAME}). Brief уже принят.\n"
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
        workforce_plan = self._workforce.plan(
            last_user,
            thinking,
            executive_action=decision.action,
            premium_allowed=self._premium_llm_allowed(thinking, last_user),
            available_employees=available_employees,
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
        )

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
        debug: bool = False,
    ) -> tuple[ChatResult, str, bool, bool, WorkforceRouteLog]:
        """Route by Employee Score; escalate when calibration rejects a draft."""
        errors: list[str] = []
        chain = providers or self._chain
        task = getattr(workforce_plan, "task", "conversation")
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
            nonlocal last_attempted, escalation_count, chosen_latency_ms, fallback_started_at
            emp = provider.provider_id
            if not provider.available():
                reason, code = _diag_reason(emp)
                _log_skip(emp, reason, code)
                return None
            last_attempted = emp
            model = getattr(provider, "model_name", None)
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
                verdict = self._calibration.evaluate(
                    draft, thinking_brief, messages=cal_messages
                )
                raw_capture = debug
                if verdict.needs_rewrite:
                    escalation_count += 1
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
                return result
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                escalation_count += 1
                err_name = type(exc).__name__
                err_text = str(exc).lower()
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
                return None

        for provider in chain:
            if provider.provider_id == "genesis-local":
                continue
            result = _try_provider(provider)
            if result is not None:
                return _finalize_route(
                    result,
                    why=getattr(workforce_plan, "reason", ""),
                )

        if fallback_started_at is None:
            fallback_started_at = "cloud_exhausted"

        for provider in chain:
            if provider.provider_id != "genesis-local":
                continue
            if cloud_proof_mode():
                continue
            if fallback_started_at == "cloud_exhausted":
                fallback_started_at = "genesis-local"
            result = _try_provider(provider)
            if result is not None:
                why = self._why_local_chosen(diagnostics)
                return _finalize_route(result, why=why)

        if last_attempted:
            self._workforce.record_outcome(
                last_attempted,
                task,
                latency_ms=0.0,
                calibration_passed=False,
                rewritten_heavily=True,
            )

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

        fallback_started_at = "brief_speech"
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
    def _premium_llm_allowed(thinking: Any, last_user: str) -> bool:
        """5–20% hardest tasks may use paid employees when keys exist."""
        import os

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
