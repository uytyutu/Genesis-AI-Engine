"""Genesis AI — unified public conversation via Genesis Brain + layers."""

from __future__ import annotations

import logging
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

    def chat(
        self,
        question: str,
        *,
        history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
        attachment_note: str = "",
        visitor_id: str | None = None,
        session_id: str | None = None,
        personality_mode: Literal["public", "ceo"] = "public",
        debug: bool = False,
    ) -> dict[str, Any]:
        history = history or []
        ctx = context or {}
        vid = (visitor_id or ctx.get("visitor_id") or "anonymous").strip()[:64]
        sid = (session_id or ctx.get("session_id") or "").strip()[:64] or None

        q = question.strip()
        if attachment_note:
            q = f"{q}\n\n[{attachment_note}]" if q else f"[{attachment_note}]"

        if is_meta_exfiltration_attempt(q):
            return {
                "answer": META_EXFILTRATION_REFUSAL,
                "source": "genesis-ai",
                "mode": "genesis",
                "cta_href": None,
                "cta_label": None,
            }

        mode: Literal["public", "ceo"] = "ceo" if ctx.get("personality") == "ceo" else "public"
        if ctx.get("personality_mode") == "ceo":
            mode = "ceo"

        assistant_locale = resolve_assistant_locale(
            ctx.get("assistant_locale"),
            ui_locale=ctx.get("ui_locale"),
            legacy_locale=ctx.get("locale"),
        )

        messages = self._brain.assemble_messages(history, q)
        try:
            result = self._brain.chat(
                system=self._system,
                messages=messages,
                visitor_id=vid,
                session_id=sid,
                personality_mode=mode,
                assistant_locale=assistant_locale,
                communication_style=ctx.get("communication_style"),
                debug=debug,
            )
            out = self._brain.to_public_dict(result)
            if sid:
                out["session_id"] = sid
            if out.get("answer"):
                out["answer"] = scrub_internal_terms_from_answer(out["answer"])
            if debug and result.trace:
                out["debug"] = result.trace
            if attachment_note and out.get("answer"):
                ack = localized_service_copy("attachment_ack", assistant_locale)
                out["answer"] = f"{ack}{out['answer']}"
            return out
        except Exception as exc:
            logger.warning("Genesis Brain error: %s", exc)
            return {
                "answer": localized_service_copy("error_fallback", assistant_locale),
                "source": "genesis-ai",
                "mode": "genesis",
                "cta_href": None,
                "cta_label": None,
            }

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
        from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine

        mem = self._brain._memory.load(visitor_id)  # noqa: SLF001
        style = ConversationStyleEngine()
        ctx = style.build_context(mem, visitor_id)
        return style.pick_greeting(ctx)

    @property
    def sessions(self):
        return self._brain._sessions  # noqa: SLF001
