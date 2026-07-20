"""Engine AI Brain — smart outreach, niche classification, LLM Router integration."""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

from app.config import env_config_file
from app.integration.genesis_brain.providers import build_provider_registry
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.llm_router.router import LLMRouter

_NICHE_LABELS = (
    "local_service",
    "auto_repair",
    "dental",
    "restaurant",
    "retail",
    "professional_services",
    "expired_landing",
    "niche_blog",
)


class EngineAIService:
    """Uses LLM (Groq/OpenAI via Router) for Engine outreach — template fallback."""

    def __init__(
        self,
        memory_dir: Path | None = None,
        *,
        api_keys: Mapping[str, str | None] | None = None,
        use_env: bool = True,
    ) -> None:
        self._memory = memory_dir or Path(__file__).resolve().parent.parent / "memory"
        self._router = LLMRouter(self._memory)
        self._api_keys = dict(api_keys) if api_keys is not None else None
        self._use_env = use_env

    def _env_get(self, key: str) -> str:
        if self._api_keys is not None and key in self._api_keys:
            value = self._api_keys[key]
            return (value or "").strip() if value is not None else ""
        if not self._use_env:
            return ""
        return os.getenv(key, "").strip()

    def _has_cloud_keys(self) -> tuple[bool, bool, bool]:
        groq = bool(self._env_get("GENESIS_GROQ_API_KEY") or self._env_get("GROQ_API_KEY"))
        openai = bool(self._env_get("GENESIS_LLM_API_KEY") or self._env_get("OPENAI_API_KEY"))
        gemini = bool(self._env_get("GENESIS_GEMINI_API_KEY") or self._env_get("GOOGLE_API_KEY"))
        return groq, openai, gemini

    @contextmanager
    def _temporary_key_env(self):
        if not self._api_keys:
            yield
            return
        old: dict[str, str | None] = {}
        for key, value in self._api_keys.items():
            old[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            yield
        finally:
            for key, previous in old.items():
                if previous is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = previous

    def setup_status(self) -> dict[str, Any]:
        groq, openai, gemini = self._has_cloud_keys()
        configured = groq or openai or gemini
        provider = self._pick_provider()
        plan = self._router.plan_route("outreach_draft", premium_allowed=False)
        return {
            "configured": configured,
            "brain_ready": provider is not None,
            "recommended_provider": "groq",
            "recommendation_note": (
                "Groq — быстрее и дешевле для коротких офферов и классификации ниш. "
                "OpenAI — запасной вариант (gpt-4o-mini)."
            ),
            "env_vars": {
                "groq": "GENESIS_GROQ_API_KEY или GROQ_API_KEY",
                "openai": "OPENAI_API_KEY или GENESIS_LLM_API_KEY",
                "gemini": "GENESIS_GEMINI_API_KEY (опционально)",
            },
            "primary_config_file": env_config_file(),
            "active_provider": getattr(provider, "provider_id", None) if provider else None,
            "active_model": getattr(provider, "model_name", None) if provider else None,
            "llm_router_task": plan.task,
            "llm_router_order": plan.failover_order[:4],
            "uses": [
                "Персонализированные outreach-офферы из site_analysis issues",
                "Классификация ниши (мастерская, кафе, магазин…)",
                "Planner / LLM Router для Vector Brain и Engine",
            ],
            "cold_outreach_note": (
                "Cold Outreach — 5 конкретных писем лучше 10 000 шаблонных. "
                "Не спам: одна проблема → одно решение → один человек."
            ),
            "status_label": "AI Brain готов" if provider else "Нужен GROQ или OPENAI ключ",
        }

    def _pick_provider(self) -> Any | None:
        """Cloud API keys only — Engine outreach needs Groq/OpenAI/Gemini, not local Ollama."""
        with self._temporary_key_env():
            reg = build_provider_registry()
            for pid in ("groq", "openai", "gemini"):
                p = reg.get(pid)
                if p is not None and p.available():
                    return p
        return None

    def _pick_provider_for_task(self, task: str = "simple") -> Any | None:
        plan = self._router.plan_route(task, premium_allowed=False)
        with self._temporary_key_env():
            reg = build_provider_registry()
            for pid in plan.failover_order:
                p = reg.get(pid)
                if p is not None and p.available():
                    return p
        return None

    def classify_niche(
        self,
        *,
        analysis: dict[str, Any],
        company: str,
        url: str = "",
        router_task: str = "simple",
    ) -> dict[str, Any]:
        """Classify business niche from scan — LLM if available, heuristics fallback."""
        issues = analysis.get("issues") or []
        title = str(analysis.get("title") or company)
        tech = analysis.get("tech_stack") or []
        blob = f"{title} {company} {url} {' '.join(issues)} {' '.join(tech)}".lower()

        heuristic = "local_service"
        if any(w in blob for w in ("zahn", "dental", "стомат", "dentist")):
            heuristic = "dental"
        elif any(w in blob for w in ("autowerkstatt", "werkstatt", "auto repair", "garage")):
            heuristic = "auto_repair"
        elif any(w in blob for w in ("restaurant", "café", "cafe", "bistro", "pizza")):
            heuristic = "restaurant"
        elif any(w in blob for w in ("shop", "store", "laden", "магазин")):
            heuristic = "retail"
        elif any(w in blob for w in ("anwalt", "kanzlei", "law", "юрист")):
            heuristic = "professional_services"
        elif any(w in blob for w in ("blog", "coming soon", "under construction")):
            heuristic = "expired_landing"

        provider = self._pick_provider_for_task(router_task)
        if not provider:
            return {
                "niche": heuristic,
                "confidence": 0.55,
                "source": "heuristic",
                "label": heuristic.replace("_", " ").title(),
                "router_task": router_task,
            }

        system = (
            "You classify German/local business websites into one niche id. "
            f"Valid ids: {', '.join(_NICHE_LABELS)}. "
            "Reply JSON only: {\"niche\": \"...\", \"confidence\": 0.0-1.0, \"label\": \"human label\"}"
        )
        user = json.dumps(
            {
                "company": company,
                "url": url,
                "title": title,
                "issues": issues[:6],
                "tech_stack": tech,
            },
            ensure_ascii=False,
        )
        try:
            result = provider.chat(
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            raw = (result.answer if hasattr(result, "answer") else str(result)).strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                niche = str(data.get("niche") or heuristic)
                if niche not in _NICHE_LABELS:
                    niche = heuristic
                return {
                    "niche": niche,
                    "confidence": float(data.get("confidence") or 0.75),
                    "source": "llm_router",
                    "label": str(data.get("label") or niche),
                    "provider": getattr(provider, "provider_id", ""),
                    "router_task": router_task,
                }
        except Exception:
            pass
        return {
            "niche": heuristic,
            "confidence": 0.55,
            "source": "heuristic_fallback",
            "label": heuristic.replace("_", " ").title(),
            "router_task": router_task,
        }

    def generate_personalized_offer(
        self,
        *,
        company: str,
        analysis: dict[str, Any],
        language: str,
        package_name: str,
        price_eur: float,
        fit_reason: str = "",
        price_label: str = "",
        currency: str = "",
        market: str = "",
    ) -> dict[str, Any] | None:
        """LLM outreach draft — company-voice commercial proposal, not spam."""
        provider = self._pick_provider()
        if not provider:
            return None

        issues = [str(i) for i in (analysis.get("issues") or [])[:7]]
        strengths = [str(s) for s in (analysis.get("strengths") or [])[:3]]
        lang = (language or "de").split("-")[0]
        lang_names = {
            "de": "German",
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "uk": "Ukrainian",
            "ru": "Russian",
            "cs": "Czech",
        }
        lang_label = lang_names.get(lang, "German")
        money = (price_label or "").strip() or f"{price_eur:.0f} EUR"

        system = (
            f"You write ONE commercial proposal email in {lang_label} as Virtus Core / {BRAND_NAME} "
            f"(sender: Ramish speaking for the company). "
            "Tone: living offer from a digital company — concrete, respectful, not spam. "
            "Write as WE/OUR team addressing THEIR company by name. "
            "Mention SPECIFIC website issues as DIAGNOSIS only. "
            "Do NOT promise to repair, patch, or connect to their existing WordPress/Wix/CMS. "
            "Sell Path A: a NEW modern Landing Page = digital restart "
            "(fast, mobile-first, clear contact/booking). "
            f"State the price EXACTLY as: {money} "
            "(local currency for their market — never invent another currency). "
            "Deliverable: finished HTML landing in ~5–7 business days, ready for their host; "
            "optional: we upload to their domain. "
            "Primary CTA: invite them to open the order page URL from user JSON — "
            "do NOT make 'reply to this email' the main call to action. "
            "No hype, no ALL CAPS, no mass-mail tone. "
            "Reply JSON only: {\"subject\": \"...\", \"body\": \"...\"}"
        )
        from app.integration.public_site_url import configured_public_base

        order_base = configured_public_base()
        mcode = (market or "").strip().upper()
        order_url = f"{order_base}/order" + (f"?market={mcode}" if mcode else "")
        user = json.dumps(
            {
                "company": company,
                "issues": issues,
                "strengths": strengths,
                "package": package_name,
                "price_label": money,
                "currency": currency or "",
                "market": mcode,
                "fit_reason": fit_reason[:200],
                "site_url": analysis.get("final_url") or analysis.get("url"),
                "order_url": order_url,
            },
            ensure_ascii=False,
        )
        try:
            result = provider.chat(system=system, messages=[{"role": "user", "content": user}])
            raw = (result.answer if hasattr(result, "answer") else str(result)).strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                return None
            data = json.loads(m.group(0))
            subject = str(data.get("subject") or "").strip()
            body = str(data.get("body") or "").strip()
            if not subject or not body:
                return None
            return {
                "subject": subject,
                "body": body,
                "language": lang,
                "source": "llm",
                "provider": getattr(provider, "provider_id", ""),
                "model": getattr(provider, "model_name", ""),
            }
        except Exception:
            return None
