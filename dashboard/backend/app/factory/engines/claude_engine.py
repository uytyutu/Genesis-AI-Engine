"""Claude research engine — animated single-page HTML via Claude / OpenRouter / Kimi.

Hard fail if key missing or model returns unusable HTML. Never falls back to Classic.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from app.factory.engines.base import ClaudeEngineAuthError, EngineError, EngineRequest, EngineResult

ENGINE_ID = "claude"

_HTML_FENCE = re.compile(r"```(?:html)?\s*([\s\S]*?)```", re.I)

_SYSTEM_PROMPT = """You are Virtus Core Factory — Animated Landing research generator.
Output ONE complete production-ready HTML5 document only (no markdown prose outside HTML).
Prefer a ```html fenced block if you must fence.

Quality bar (matches Animated tier pricing — do not under-deliver):
1) Architecture: semantic sections (header, hero, services, proof, CTA, footer); clear class names; readable CSS variables.
2) Motion: purposeful hero entrance + scroll reveal; CSS @keyframes and/or IntersectionObserver; honor prefers-reduced-motion.
3) Performance: no heavy Three.js / WebGL / video backgrounds unless the brief explicitly asks for 3D; keep DOM lean; inline CSS/JS only.
4) Design: distinctive niche palette — not purple-on-white AI cliché; real visual hierarchy; mobile-first.
5) SEO: <title>, meta description, one h1, sensible heading order.
6) Content: no lorem ipsum; plausible niche copy in the requested language; clear CTA (call / WhatsApp / form).
7) Legal: do NOT invent Impressum/Privacy HTML unless market is DE/AT/CH; footer may say legal pages to be added.
8) Editability: clean structure a human can tweak in under 30 minutes — no minified soup, no opaque generated IDs.

If you cannot meet this bar, still return the best complete HTML you can — never return an empty or partial page.
"""


def _resolve_llm() -> tuple[str, str, str, str]:
    """Return (provider_id, api_key, base_url, model). Raises ClaudeEngineAuthError if no key."""
    preferred = (os.getenv("FACTORY_RESEARCH_LLM") or "claude").strip().lower()

    openrouter = (os.getenv("GENESIS_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or "").strip()
    anthropic = (os.getenv("GENESIS_ANTHROPIC_API_KEY") or "").strip()
    kimi = (os.getenv("GENESIS_KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or "").strip()

    candidates: list[tuple[str, str, str, str]] = []
    if preferred == "kimi" and kimi:
        candidates.append(
            (
                "kimi",
                kimi,
                (os.getenv("GENESIS_KIMI_BASE_URL") or "https://api.moonshot.ai/v1").rstrip("/"),
                os.getenv("GENESIS_KIMI_MODEL") or "moonshot-v1-128k",
            )
        )
    if preferred in ("claude", "anthropic") and (anthropic or openrouter):
        key = anthropic or openrouter
        candidates.append(
            (
                "claude",
                key,
                (
                    os.getenv("GENESIS_ANTHROPIC_BASE_URL")
                    or os.getenv("GENESIS_OPENROUTER_BASE_URL")
                    or "https://openrouter.ai/api/v1"
                ).rstrip("/"),
                os.getenv("GENESIS_ANTHROPIC_MODEL")
                or os.getenv("GENESIS_CLAUDE_ENGINE_MODEL")
                or "anthropic/claude-3.5-haiku",
            )
        )
    if preferred == "openrouter" and openrouter:
        candidates.append(
            (
                "openrouter",
                openrouter,
                (os.getenv("GENESIS_OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/"),
                os.getenv("GENESIS_OPENROUTER_MODEL") or "anthropic/claude-3.5-sonnet",
            )
        )

    # Fallbacks if preferred missing but another research key exists
    if not candidates:
        if anthropic or openrouter:
            key = anthropic or openrouter
            candidates.append(
                (
                    "claude",
                    key,
                    (
                        os.getenv("GENESIS_ANTHROPIC_BASE_URL")
                        or os.getenv("GENESIS_OPENROUTER_BASE_URL")
                        or "https://openrouter.ai/api/v1"
                    ).rstrip("/"),
                    os.getenv("GENESIS_ANTHROPIC_MODEL")
                    or os.getenv("GENESIS_CLAUDE_ENGINE_MODEL")
                    or "anthropic/claude-3.5-haiku",
                )
            )
        elif kimi:
            candidates.append(
                (
                    "kimi",
                    kimi,
                    (os.getenv("GENESIS_KIMI_BASE_URL") or "https://api.moonshot.ai/v1").rstrip("/"),
                    os.getenv("GENESIS_KIMI_MODEL") or "moonshot-v1-128k",
                )
            )

    if not candidates:
        raise ClaudeEngineAuthError(
            "Set GENESIS_ANTHROPIC_API_KEY, GENESIS_OPENROUTER_API_KEY, or GENESIS_KIMI_API_KEY "
            "in .env (gitignored). No silent Classic fallback."
        )
    return candidates[0]


def _build_user_prompt(request: EngineRequest) -> str:
    lang = (request.language or "en").strip().lower()
    name = request.business_name.strip() or "the business"
    tier = (request.package_id or "basic").strip().lower()
    motion_bar = {
        "basic": "tasteful CSS motion (hero fade/slide + 2–3 scroll reveals)",
        "business": "richer motion system (staggered reveals, CTA pulse, section transitions) still CSS/JS-light",
        "premium": "premium motion polish (layered hero, scroll storytelling) WITHOUT Three.js unless brief demands 3D",
    }.get(tier, "tasteful CSS motion")
    return f"""Build the Animated Landing for:

Business: {name}
Market: {request.market_code}
UI language: {lang} (ALL visible copy in this language)
Package tier: {tier} — motion bar: {motion_bar}
City: {request.city or "n/a"}
Phone: {request.phone or "n/a"}
Email: {request.email or "n/a"}
WhatsApp: {request.whatsapp or request.phone or "n/a"}

Client brief:
{request.description.strip()[:1400]}

Return only the HTML document.
"""


def _chat_completion(api_key: str, base_url: str, model: str, user_prompt: str) -> str:
    url = f"{base_url}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0.35,
        "max_tokens": 12_000,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://virtuscore.local/research",
            "X-Title": "Virtus Core Claude Engine Research",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise EngineError("claude_http_error", f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EngineError("claude_network_error", str(exc.reason or exc)) from exc

    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise EngineError("claude_bad_response", "Model response missing message content") from exc
    if not isinstance(content, str) or not content.strip():
        raise EngineError("claude_empty", "Model returned empty content")
    return content


def _extract_html(text: str) -> str:
    fenced = _HTML_FENCE.search(text)
    if fenced:
        candidate = fenced.group(1).strip()
    else:
        candidate = text.strip()
    lower = candidate.lower()
    for marker in ("<!doctype html", "<html"):
        idx = lower.find(marker)
        if idx >= 0:
            candidate = candidate[idx:]
            break
    return candidate.strip()


def _validate_html(html: str) -> None:
    low = html.lower()
    if "<html" not in low or "</html>" not in low:
        raise EngineError("claude_invalid_html", "Response is not a complete HTML document")
    if len(html) < 800:
        raise EngineError("claude_too_short", "HTML artifact too short to be a real landing page")
    has_motion = (
        "animation" in low
        or "@keyframes" in low
        or "transition" in low
        or "intersectionobserver" in low
        or "scroll" in low
    )
    if not has_motion:
        raise EngineError(
            "claude_no_motion",
            "HTML lacks animation/transition — Claude engine must deliver motion (or fail).",
        )


def generate(request: EngineRequest) -> EngineResult:
    provider_id, api_key, base_url, model = _resolve_llm()
    prompt = _build_user_prompt(request)
    raw = _chat_completion(api_key, base_url, model, prompt)
    html = _extract_html(raw)
    _validate_html(html)
    return EngineResult(
        engine_id=ENGINE_ID,
        html=html,
        meta={
            "research_provider": provider_id,
            "model": model,
            "base_url": base_url,
            "market_code": request.market_code,
            "language": request.language,
            "package_id": request.package_id,
            "business_name": request.business_name,
            "bytes": len(html.encode("utf-8")),
        },
    )
