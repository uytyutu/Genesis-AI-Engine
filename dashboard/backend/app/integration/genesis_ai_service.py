"""Genesis AI — unified public conversation via Genesis Brain + layers."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from app.integration.genesis_ai_knowledge import build_system_prompt
from app.integration.locale_service import localized_service_copy, resolve_assistant_locale
from app.security import (
    META_EXFILTRATION_REFUSAL,
    is_meta_exfiltration_attempt,
    scrub_internal_terms_from_answer,
)
from app.integration.genesis_brain import GenesisBrain
from app.integration.knowledge_intake_transparency import transparency_enabled
from app.integration.knowledge_intake_service import KnowledgeIntakeService
from app.integration.knowledge_reasoning import maybe_append_expert_review
from app.integration.vector_intelligence.service import VectorIntelligenceService
from app.integration.vector_pipeline_trace import start_trace, trace_step
from app.integration.vector_dev_stats import build_dev_stats, format_dev_stats_lines, save_last_dev_stats

logger = logging.getLogger(__name__)

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class GenesisAIService:
    """
    Public /site intelligence entry.

    Genesis Brain + Personality + Memory + Knowledge.
    LLM vendors are invisible tools.
    """

    def __init__(
        self,
        packages: list[dict] | None = None,
        *,
        memory_dir: Path | None = None,
    ) -> None:
        self._packages = packages or []
        self._memory_dir = memory_dir or _DEFAULT_MEMORY
        self._brain = GenesisBrain(memory_dir=self._memory_dir, packages=self._packages)
        self._system = build_system_prompt(self._packages)

    def _with_project_state(
        self,
        payload: dict[str, Any],
        visitor_id: str,
        message: str = "",
    ) -> dict[str, Any]:
        """Attach canonical Project State — panel must match Vector on every reply."""
        from app.integration.project_platform.service import ProjectPlatformService

        svc = ProjectPlatformService(self._memory_dir)
        q = (message or "").strip()
        if q:
            try:
                svc.bootstrap_from_message(visitor_id, q)
            except Exception:
                pass
        return svc.enrich_with_project_state(dict(payload), visitor_id)

    def chat(
        self,
        question: str,
        *,
        history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
        attachment_note: str = "",
        attachment_files: list[dict] | None = None,
        attachment_ids: list[str] | None = None,
        visitor_id: str | None = None,
        session_id: str | None = None,
        personality_mode: Literal["public", "ceo"] = "public",
        debug: bool = False,
    ) -> dict[str, Any]:
        history = history or []
        ctx = context or {}
        vid = (visitor_id or ctx.get("visitor_id") or "anonymous").strip()[:64]
        sid = (session_id or ctx.get("session_id") or "").strip()[:64] or None

        assistant_locale = resolve_assistant_locale(
            ctx.get("assistant_locale"),
            ui_locale=ctx.get("ui_locale"),
            legacy_locale=ctx.get("locale"),
        )

        q = question.strip()
        user_q = q
        trace = start_trace(
            visitor_id=vid,
            question=q,
            memory_dir=self._memory_dir,
        )
        intake = KnowledgeIntakeService(self._memory_dir)
        files = list(attachment_files or [])
        if attachment_ids:
            resolved = intake.resolve_for_execution(
                attachment_ids=attachment_ids,
                visitor_id=vid,
                session_id=sid,
            )
            if resolved:
                files = resolved

        if attachment_ids and not files:
            trace.finish(ok=True, provider="execution", reason="attachment_missing")
            return self._with_project_state(
                {
                    "answer": (
                        "Файл не найден на сервере (возможно, истёк срок хранения).\n\n"
                        "Прикрепите PDF ещё раз и напишите «Проверь мой бизнес-план»."
                    ),
                    "source": "genesis-ai",
                    "mode": "genesis",
                    "provider": "execution",
                    "cta_href": None,
                    "cta_label": None,
                    "cta_actions": None,
                },
                vid,
                user_q,
            )

        if is_meta_exfiltration_attempt(q):
            trace.finish(ok=True, provider="security", reason="meta_exfiltration")
            return self._with_project_state(
                {
                    "answer": META_EXFILTRATION_REFUSAL,
                    "source": "genesis-ai",
                    "mode": "genesis",
                    "cta_href": None,
                    "cta_label": None,
                    "cta_actions": None,
                },
                vid,
                user_q,
            )

        from app.execution.bridge import try_user_execution, should_route_attachments_to_execution
        import time as _time

        t_exec0 = _time.perf_counter()
        executed = try_user_execution(
            q,
            visitor_id=vid,
            memory_dir=self._memory_dir,
            attachment_files=files,
            ui_locale=assistant_locale,
            history=history,
        )
        exec_ms = int((_time.perf_counter() - t_exec0) * 1000)
        if executed:
            trace.finish(ok=True, provider="execution")
            executed = self._with_project_state(dict(executed), vid, user_q)
            executed["product_timing_ms"] = {"execution": exec_ms, "total": exec_ms}
            return executed

        from app.integration.delivery_engine.gate import delivery_engine_enabled

        if delivery_engine_enabled(self._memory_dir):
            from app.integration.delivery_engine import DeliveryEngine

            t_del0 = _time.perf_counter()
            delivery = DeliveryEngine(self._memory_dir).try_handle_message(
                vid, q, locale=assistant_locale
            )
            del_ms = int((_time.perf_counter() - t_del0) * 1000)
            if delivery:
                trace.finish(ok=True, provider="delivery_engine")
                delivery = self._with_project_state(dict(delivery), vid, user_q)
                delivery["product_timing_ms"] = {"delivery_engine": del_ms, "total": del_ms}
                return delivery

        if files and should_route_attachments_to_execution(q, files):
            return self._with_project_state(
                {
                    "answer": (
                        "Документ получен, но отчёты не созданы.\n\n"
                        "Прикрепите PDF ещё раз и напишите «Проанализируй бизнес-план» — "
                        "я создам Executive Summary и Report в Workspace."
                    ),
                    "source": "genesis-ai",
                    "mode": "genesis",
                    "provider": "execution",
                    "cta_href": None,
                    "cta_label": None,
                    "cta_actions": None,
                },
                vid,
                user_q,
            )

        if files:
            note = intake.build_brain_intake_context(files, locale=assistant_locale)
            if not should_route_attachments_to_execution(q, files):
                note = maybe_append_expert_review(
                    q,
                    note,
                    files,
                    memory_dir=self._memory_dir,
                    locale=assistant_locale,
                )
        else:
            note = attachment_note
        if note:
            q = f"{q}\n\n[{note}]" if q else f"[{note}]"

        mode: Literal["public", "ceo"] = "ceo" if ctx.get("personality") == "ceo" else "public"
        if ctx.get("personality_mode") == "ceo":
            mode = "ceo"

        messages = self._brain.assemble_messages(history, q)
        intel = VectorIntelligenceService(self._memory_dir)
        turn_plan, intelligence_hint = intel.plan_turn(
            vid,
            q,
            history=history,
            has_attachments=bool(files),
        )
        trace_step(
            "plan_turn",
            workforce_tier=turn_plan.workforce_tier,
            workforce_task=turn_plan.workforce_task,
            intent=turn_plan.intent,
        )
        intel.touch_session(vid)
        try:
            trace_step("brain_chat_start")
            import time as _time

            t0 = _time.perf_counter()
            result = self._brain.chat(
                system=self._system,
                messages=messages,
                visitor_id=vid,
                session_id=sid,
                personality_mode=mode,
                assistant_locale=assistant_locale,
                communication_style=ctx.get("communication_style"),
                debug=debug,
                intelligence_context=intelligence_hint,
                workforce_tier=turn_plan.workforce_tier,
                workforce_task=turn_plan.workforce_task,
                has_attachments=bool(files),
            )
            elapsed_sec = _time.perf_counter() - t0
            out = self._brain.to_public_dict(result)
            trace_step(
                "brain_chat_done",
                provider=result.provider_id,
                answer_len=len(result.answer or ""),
            )
            if sid:
                out["session_id"] = sid
            if out.get("answer"):
                out["answer"] = scrub_internal_terms_from_answer(out["answer"])
            if debug:
                from app.integration.provider_health_service import workforce_health_report

                health = workforce_health_report(memory_dir=self._memory_dir, force_probe=False)
                dev_stats = build_dev_stats(
                    turn_plan=turn_plan,
                    provider_id=result.provider_id,
                    elapsed_sec=elapsed_sec,
                    route=result.dev_route,
                    health_excluded=health.get("excluded"),
                )
                out["debug"] = dict(result.trace or {})
                out["debug"]["pipeline_request_id"] = trace.request_id
                out["debug"]["dev_stats"] = dev_stats
                out["debug"]["dev_stats_text"] = format_dev_stats_lines(dev_stats)
                save_last_dev_stats(self._memory_dir, vid, dev_stats)
            elif result.trace:
                out["debug"] = result.trace
                out["debug"]["pipeline_request_id"] = trace.request_id
            intel.observe_after_turn(vid, q, turn=turn_plan)
            trace_step("memory_observe_done")
            if files and out.get("answer") and not should_route_attachments_to_execution(q, files):
                ack = intake.build_user_ack(files, locale=assistant_locale)
                if ack:
                    out["answer"] = f"{ack}{out['answer']}"
            elif attachment_note and out.get("answer") and not transparency_enabled(self._memory_dir):
                ack = localized_service_copy("attachment_ack", assistant_locale)
                out["answer"] = f"{ack}{out['answer']}"
            trace.finish(
                ok=bool(out.get("answer")),
                provider=out.get("provider"),
                answer_len=len(out.get("answer") or ""),
            )
            return self._with_project_state(out, vid, user_q)
        except Exception as exc:
            logger.warning("Genesis Brain error: %s", exc)
            trace.finish(ok=False, error=f"{type(exc).__name__}: {exc}")
            return self._with_project_state(
                {
                    "answer": localized_service_copy("error_fallback", assistant_locale),
                    "source": "genesis-ai",
                    "mode": "genesis",
                    "cta_href": None,
                    "cta_label": None,
                },
                vid,
                user_q,
            )

    def chat_stream(
        self,
        question: str,
        *,
        history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
        attachment_note: str = "",
        attachment_files: list[dict] | None = None,
        attachment_ids: list[str] | None = None,
        visitor_id: str | None = None,
        session_id: str | None = None,
        personality_mode: Literal["public", "ceo"] = "public",
        debug: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """SSE-friendly stream: token events, then a done payload (falls back to chat)."""
        history = history or []
        ctx = context or {}
        vid = (visitor_id or ctx.get("visitor_id") or "anonymous").strip()[:64]
        sid = (session_id or ctx.get("session_id") or "").strip()[:64] or None

        assistant_locale = resolve_assistant_locale(
            ctx.get("assistant_locale"),
            ui_locale=ctx.get("ui_locale"),
            legacy_locale=ctx.get("locale"),
        )

        def _done(payload: dict[str, Any]) -> dict[str, Any]:
            out = self._with_project_state(dict(payload), vid, user_q)
            out.setdefault("type", "done")
            out.setdefault("source", "genesis-ai")
            out.setdefault("mode", "genesis")
            if sid:
                out["session_id"] = sid
            return out

        q = question.strip()
        user_q = q
        trace = start_trace(visitor_id=vid, question=q, memory_dir=self._memory_dir)

        yield {"type": "status", "phase": "thinking"}

        intake = KnowledgeIntakeService(self._memory_dir)
        files = list(attachment_files or [])
        if attachment_ids:
            resolved = intake.resolve_for_execution(
                attachment_ids=attachment_ids,
                visitor_id=vid,
                session_id=sid,
            )
            if resolved:
                files = resolved

        if attachment_ids and not files:
            trace.finish(ok=True, provider="execution", reason="attachment_missing")
            yield _done({
                "answer": (
                    "Файл не найден на сервере (возможно, истёк срок хранения).\n\n"
                    "Прикрепите PDF ещё раз и напишите «Проверь мой бизнес-план»."
                ),
                "provider": "execution",
                "cta_href": None,
                "cta_label": None,
                "cta_actions": None,
            })
            return

        if is_meta_exfiltration_attempt(q):
            trace.finish(ok=True, provider="security", reason="meta_exfiltration")
            yield _done({
                "answer": META_EXFILTRATION_REFUSAL,
                "cta_href": None,
                "cta_label": None,
                "cta_actions": None,
            })
            return

        from app.execution.bridge import try_user_execution, should_route_attachments_to_execution
        import time as _time

        t_exec0 = _time.perf_counter()
        executed = try_user_execution(
            q,
            visitor_id=vid,
            memory_dir=self._memory_dir,
            attachment_files=files,
            ui_locale=assistant_locale,
            history=history,
        )
        exec_ms = int((_time.perf_counter() - t_exec0) * 1000)
        if executed:
            trace.finish(ok=True, provider="execution")
            payload = dict(executed)
            payload["product_timing_ms"] = {"execution": exec_ms, "total": exec_ms}
            yield _done(payload)
            return

        from app.integration.delivery_engine.gate import delivery_engine_enabled

        if delivery_engine_enabled(self._memory_dir):
            from app.integration.delivery_engine import DeliveryEngine

            t_del0 = _time.perf_counter()
            delivery = DeliveryEngine(self._memory_dir).try_handle_message(
                vid, q, locale=assistant_locale
            )
            del_ms = int((_time.perf_counter() - t_del0) * 1000)
            if delivery:
                trace.finish(ok=True, provider="delivery_engine")
                payload = dict(delivery)
                payload["product_timing_ms"] = {"delivery_engine": del_ms, "total": del_ms}
                yield _done(payload)
                return

        if files and should_route_attachments_to_execution(q, files):
            yield _done({
                "answer": (
                    "Документ получен, но отчёты не созданы.\n\n"
                    "Прикрепите PDF ещё раз и напишите «Проанализируй бизнес-план» — "
                    "я создам Executive Summary и Report в Workspace."
                ),
                "provider": "execution",
                "cta_href": None,
                "cta_label": None,
                "cta_actions": None,
            })
            return

        if files:
            note = intake.build_brain_intake_context(files, locale=assistant_locale)
            if not should_route_attachments_to_execution(q, files):
                note = maybe_append_expert_review(
                    q,
                    note,
                    files,
                    memory_dir=self._memory_dir,
                    locale=assistant_locale,
                )
        else:
            note = attachment_note
        if note:
            q = f"{q}\n\n[{note}]" if q else f"[{note}]"

        mode: Literal["public", "ceo"] = "ceo" if ctx.get("personality") == "ceo" else "public"
        if ctx.get("personality_mode") == "ceo":
            mode = "ceo"

        messages = self._brain.assemble_messages(history, q)
        intel = VectorIntelligenceService(self._memory_dir)
        turn_plan, intelligence_hint = intel.plan_turn(
            vid,
            q,
            history=history,
            has_attachments=bool(files),
        )
        trace_step(
            "plan_turn",
            workforce_tier=turn_plan.workforce_tier,
            workforce_task=turn_plan.workforce_task,
            intent=turn_plan.intent,
        )
        intel.touch_session(vid)

        got_done = False
        try:
            import time as _time

            t0 = _time.perf_counter()
            for event in self._brain.stream_fast_lane(
                system=self._system,
                messages=messages,
                visitor_id=vid,
                session_id=sid,
                personality_mode=mode,
                assistant_locale=assistant_locale,
                communication_style=ctx.get("communication_style"),
                intelligence_context=intelligence_hint,
                workforce_task=turn_plan.workforce_task,
                has_attachments=bool(files),
            ):
                if event.get("type") == "done":
                    got_done = True
                    elapsed_sec = _time.perf_counter() - t0
                    out = dict(event)
                    if out.get("answer"):
                        out["answer"] = scrub_internal_terms_from_answer(out["answer"])
                    if files and out.get("answer") and not should_route_attachments_to_execution(q, files):
                        ack = intake.build_user_ack(files, locale=assistant_locale)
                        if ack:
                            out["answer"] = f"{ack}{out['answer']}"
                    elif attachment_note and out.get("answer") and not transparency_enabled(self._memory_dir):
                        ack = localized_service_copy("attachment_ack", assistant_locale)
                        out["answer"] = f"{ack}{out['answer']}"
                    if debug:
                        from app.integration.provider_health_service import workforce_health_report

                        health = workforce_health_report(memory_dir=self._memory_dir, force_probe=False)
                        dev_stats = build_dev_stats(
                            turn_plan=turn_plan,
                            provider_id=out.get("provider") or "unknown",
                            elapsed_sec=elapsed_sec,
                            route=out.get("dev_route"),
                            health_excluded=health.get("excluded"),
                        )
                        out["debug"] = {"dev_stats": dev_stats, "dev_stats_text": format_dev_stats_lines(dev_stats)}
                        save_last_dev_stats(self._memory_dir, vid, dev_stats)
                    intel.observe_after_turn(vid, q, turn=turn_plan)
                    trace.finish(
                        ok=bool(out.get("answer")),
                        provider=out.get("provider"),
                        answer_len=len(out.get("answer") or ""),
                    )
                    yield _done(out)
                    return
                yield event
        except Exception as exc:
            logger.warning("Genesis Brain stream error: %s", exc)
            trace.finish(ok=False, error=f"{type(exc).__name__}: {exc}")

        if not got_done:
            result = self._brain.chat(
                system=self._system,
                messages=messages,
                visitor_id=vid,
                session_id=sid,
                personality_mode=mode,
                assistant_locale=assistant_locale,
                communication_style=ctx.get("communication_style"),
                intelligence_context=intelligence_hint,
                workforce_tier=turn_plan.workforce_tier,
                workforce_task=turn_plan.workforce_task,
                has_attachments=bool(files),
                fast_lane_only=True,
            )
            out = self._brain.to_public_dict(result)
            if out.get("answer"):
                out["answer"] = scrub_internal_terms_from_answer(out["answer"])
            yield _done(out)

    def llm_configured(self) -> bool:
        from app.integration.genesis_brain.providers import build_provider_chain

        for p in build_provider_chain(self._packages):
            if p.provider_id == "genesis-local":
                continue
            if p.available():
                return True
        return False

    def intelligence_active(self) -> bool:
        return self._brain.intelligence_active()

    def greeting(self, visitor_id: str = "anonymous") -> str:
        return VectorIntelligenceService(self._memory_dir).proactive_greeting(
            (visitor_id or "anonymous").strip()[:64]
        )

    @property
    def sessions(self):
        return self._brain._sessions  # noqa: SLF001
