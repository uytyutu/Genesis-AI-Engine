"""Claude research engine — animated single-page HTML via Anthropic/OpenRouter.

Hard fail if key missing or model returns unusable HTML. Never falls back to Classic.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from app.factory.engines.base import EngineError, EngineRequest, EngineResult

ENGINE_ID = "claude"

_HTML_FENCE = re.compile(r"```(?:html)?\s*([\s\S]*?)```", re.I)


def _resolve_llm() -> tuple[str, str, str]:
    """Return (api_key, base_url, model). Raises EngineError if no key."""
    openrouter = (os.getenv("GENESIS_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or "").strip()
    key = (os.getenv("GENESIS_ANTHROPIC_API_KEY") or openrouter or "").strip()
    if not key:
        raise EngineError(
            "claude_no_key",
            "GENESIS_ANTHROPIC_API_KEY (or OpenRouter key) required for claude engine. "
            "No silent Classic fallback.",
        )
    base = (
        os.getenv("GENESIS_ANTHROPIC_BASE_URL")
        or os.getenv("GENESIS_OPENROUTER_BASE_URL")
        or "https://openrouter.ai/api/v1"
    ).rstrip("/")
    model = (
        os.getenv("GENESIS_ANTHROPIC_MODEL")
        or os.getenv("GENESIS_CLAUDE_ENGINE_MODEL")
        or "anthropic/claude-3.5-haiku"
    )
    return key, base, model


def _build_prompt(request: EngineRequest) -> str:
    lang = (request.language or "en").strip().lower()
    name = request.business_name.strip() or "the business"
    return f"""You are a senior web designer. Output ONE complete production-ready HTML5 document only.
No markdown explanation outside the HTML. Prefer a ```html fenced block if you must fence.

Requirements:
- Modern, distinctive landing page for: {name}
- Market: {request.market_code}; UI language: {lang} (all visible copy in this language)
- Package tier: {request.package_id}
- City: {request.city or "n/a"}; phone: {request.phone or "n/a"}; email: {request.email or "n/a"}
- Brief: {request.description.strip()[:1200]}
- Mobile-first, SEO: title, meta description, semantic headings
- Clear CTA (call / WhatsApp / form)
- Visible motion: CSS animations and/or light JS for hero entrance + scroll reveal
- Respect prefers-reduced-motion (disable or simplify animations)
- Self-contained single file (inline CSS/JS); no external build step
- Do NOT include German Impressum unless market is DE/AT/CH
- Do NOT invent fake legal pages; footer may say "Legal pages to be added"
- No lorem ipsum; use plausible niche copy
- Avoid purple-gradient AI cliché; pick a cohesive brand palette for the niche
"""


def _chat_completion(api_key: str, base_url: str, model: str, prompt: str) -> str:
    url = f"{base_url}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 8000,
        "messages": [
            {
                "role": "system",
                "content": "You generate complete HTML landing pages. Output HTML only.",
            },
            {"role": "user", "content": prompt},
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
        with urllib.request.urlopen(req, timeout=120) as resp:
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
    # Trim leading chatter before <!DOCTYPE / <html
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
    # Soft animation signal — require CSS animation/transition or JS observer
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
    api_key, base_url, model = _resolve_llm()
    prompt = _build_prompt(request)
    raw = _chat_completion(api_key, base_url, model, prompt)
    html = _extract_html(raw)
    _validate_html(html)
    return EngineResult(
        engine_id=ENGINE_ID,
        html=html,
        meta={
            "model": model,
            "base_url": base_url,
            "market_code": request.market_code,
            "language": request.language,
            "package_id": request.package_id,
            "business_name": request.business_name,
            "bytes": len(html.encode("utf-8")),
        },
    )
